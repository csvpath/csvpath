import datetime
import hashlib
import logging

from .macie_exceptions import MacieException
from .macie_wrapper_loader import MacieWrapperLoader
from .recommended_lists import RecommendedLists


class MacieDownloader:
    """reads a Macie job's or automated-discovery template's whole setup
    from AWS and returns it as a wrapper dict, validated by
    MacieWrapperLoader (specs/macie/download-design.md). Read-only: it
    never writes to AWS, and it writes no file; loading the wrapper into a
    named-paths group is a separate, offline step.

        downloader = MacieDownloader(session=boto3.Session(region_name="us-east-1"))
        wrapper = downloader.download_job(job_id="3ce05dbb7ec5505def334104bf1b3bca")
        wrapper = downloader.download_template()

    Any AWS error stops the download, except reading a text allow list's
    S3 object, which is recorded in the wrapper with a warning, as the
    wrapper format provides. The AWS responses are kept verbatim, less
    boto3's ResponseMetadata, with datetimes as UTC ISO 8601 strings."""

    #
    # Macie's limits for a text (S3 words) allow list
    #
    MAX_ENTRIES = 100000
    MAX_ENTRY_LENGTH = 90

    def __init__(self, *, session, clock=None) -> None:
        if session is None:
            raise ValueError("session cannot be None")
        region = getattr(session, "region_name", None)
        if not isinstance(region, str) or region.strip() == "":
            raise ValueError(
                "The session needs a region: Macie is regional, and a job id is "
                "only meaningful in its region"
            )
        if clock is not None and not callable(clock):
            raise TypeError("clock must be callable, returning an aware datetime")
        self.region = region
        self.clock = clock or (lambda: datetime.datetime.now(datetime.timezone.utc))
        self.macie = session.client("macie2")
        self.s3 = session.client("s3")
        self.sts = session.client("sts")
        self.warnings = []

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    #
    # the two origins
    #

    def download_job(self, *, job_id: str) -> dict:
        if not isinstance(job_id, str) or job_id.strip() == "":
            raise ValueError("job_id must be a non-empty str")
        self.warnings = []
        account = self._account()
        job = self._call(self.macie.describe_classification_job, jobId=job_id)
        available = self._available()
        selector = job.get("managedDataIdentifierSelector") or "RECOMMENDED"
        ids = list(job.get("managedDataIdentifierIds") or [])
        selection = {
            "managedDataIdentifierSelector": selector,
            "managedDataIdentifierIds": ids if selector == "INCLUDE" else [],
            "excludedManagedDataIdentifierIds": ids if selector == "EXCLUDE" else [],
            "customDataIdentifierIds": list(job.get("customDataIdentifierIds") or []),
            "allowListIds": list(job.get("allowListIds") or []),
        }
        resolved, recommended_list = self._resolve_job(
            selector=selector, ids=ids, available=available
        )
        return self._wrapper(
            source={
                "origin": "job",
                "account_id": account,
                "region": self.region,
                "downloaded_at": self._now(),
                "job_id": job_id,
            },
            selection=selection,
            resolved=resolved,
            recommended_list=recommended_list,
            available=available,
            aws={"classificationJob": job},
        )

    def download_template(self) -> dict:
        """the account's sensitivity inspection template, used by
        automated sensitive data discovery"""
        self.warnings = []
        account = self._account()
        config = self._call(self.macie.get_automated_discovery_configuration)
        template_id = config.get("sensitivityInspectionTemplateId")
        if not template_id:
            self._fail(
                "This account has no sensitivity inspection template: automated "
                "sensitive data discovery has not been set up"
            )
        first_enabled = config.get("firstEnabledAt")
        if not isinstance(first_enabled, str):
            self._fail(
                "GetAutomatedDiscoveryConfiguration has no firstEnabledAt, which "
                "decides the recommended set; automated discovery has never been "
                "enabled in this account"
            )
        template = self._call(
            self.macie.get_sensitivity_inspection_template, id=template_id
        )
        available = self._available()
        includes = template.get("includes") or {}
        excludes = template.get("excludes") or {}
        included = list(includes.get("managedDataIdentifierIds") or [])
        excluded = list(excludes.get("managedDataIdentifierIds") or [])
        recommended, recommended_list = RecommendedLists.for_template(
            first_enabled_at=datetime.datetime.fromisoformat(
                first_enabled.replace("Z", "+00:00")
            )
        )
        resolved = self._unique(recommended + included)
        resolved = [i for i in resolved if i not in set(excluded)]
        resolved = self._only_available(
            ids=resolved, available=available, recommended=set(recommended)
        )
        selection = {
            "managedDataIdentifierSelector": "RECOMMENDED",
            "managedDataIdentifierIds": included,
            "excludedManagedDataIdentifierIds": excluded,
            "customDataIdentifierIds": list(
                includes.get("customDataIdentifierIds") or []
            ),
            "allowListIds": list(includes.get("allowListIds") or []),
        }
        return self._wrapper(
            source={
                "origin": "template",
                "account_id": account,
                "region": self.region,
                "downloaded_at": self._now(),
                "template_id": template_id,
            },
            selection=selection,
            resolved=resolved,
            recommended_list=recommended_list,
            available=available,
            aws={"sensitivityInspectionTemplate": template},
        )

    #
    # the parts every wrapper has
    #

    def _wrapper(
        self,
        *,
        source: dict,
        selection: dict,
        resolved: list[str],
        recommended_list: str | None,
        available: list[dict],
        aws: dict,
    ) -> dict:
        cdis = [
            self._custom_identifier(cdi_id=i)
            for i in selection["customDataIdentifierIds"]
        ]
        allow = [self._allow_list(list_id=i) for i in selection["allowListIds"]]
        wrapper = {
            "csvpath_macie": 1,
            "source": source,
            "selection": selection,
            "managedDataIdentifiers": {
                "resolved": resolved,
                "resolution": {
                    "method": "selector",
                    "recommended_list": recommended_list,
                },
                "available": available,
            },
            "customDataIdentifiers": cdis,
            "allowLists": allow,
            "findingsFilters": self._findings_filters(),
            "aws": aws,
            "warnings": list(self.warnings),
        }
        #
        # a download that produces a wrapper we would refuse to load is a
        # bug: fail here, before anything is loaded
        #
        return MacieWrapperLoader.validate(wrapper=wrapper)

    def _resolve_job(
        self, *, selector: str, ids: list[str], available: list[dict]
    ) -> tuple[list[str], str | None]:
        everything = [a["id"] for a in available]
        if selector == "INCLUDE":
            return list(ids), None
        if selector == "EXCLUDE":
            return [i for i in everything if i not in set(ids)], None
        if selector == "ALL":
            return everything, None
        if selector == "NONE":
            return [], None
        if selector == "RECOMMENDED":
            recommended, label = RecommendedLists.for_job()
            resolved = self._only_available(
                ids=recommended, available=available, recommended=set(recommended)
            )
            return resolved, label
        self._fail(f"Unknown managed data identifier selector {selector!r}")

    def _only_available(
        self, *, ids: list[str], available: list[dict], recommended: set
    ) -> list[str]:
        """drops a recommended id AWS no longer offers, with a warning, so a
        wrapper never claims an identifier AWS does not run. Ids the user
        chose (template includes) are kept: Macie checked them."""
        offered = {a["id"] for a in available}
        out = []
        for i in ids:
            if i in recommended and i not in offered:
                self.warnings.append(
                    {
                        "code": "RECOMMENDED_ID_UNAVAILABLE",
                        "subject": i,
                        "message": (
                            f"{i} is in our recommended list but this account's "
                            "ListManagedDataIdentifiers does not offer it; it is "
                            "left out"
                        ),
                    }
                )
                continue
            out.append(i)
        return out

    def _custom_identifier(self, *, cdi_id: str) -> dict:
        cdi = self._call(self.macie.get_custom_data_identifier, id=cdi_id)
        if cdi.get("deleted") is True:
            self.warnings.append(
                {
                    "code": "CDI_DELETED_BUT_SELECTED",
                    "subject": cdi_id,
                    "message": (
                        f"Custom data identifier {cdi.get('name')} was deleted in "
                        "Macie (AWS reports deleted: true) but is still selected; "
                        "Macie keeps using it, so it is kept"
                    ),
                }
            )
        return cdi

    def _allow_list(self, *, list_id: str) -> dict:
        settings = self._call(self.macie.get_allow_list, id=list_id)
        code = (settings.get("status") or {}).get("code")
        if code is not None and code != "OK":
            self.warnings.append(
                {
                    "code": "MACIE_ALLOW_LIST_STATUS",
                    "subject": list_id,
                    "message": f"Macie reports allow list {settings.get('name')} as {code}",
                }
            )
        words = (settings.get("criteria") or {}).get("s3WordsList")
        if words is None:
            return {"settings": settings}
        return {
            "settings": settings,
            "contents": self._words(list_id=list_id, words=words),
        }

    def _words(self, *, list_id: str, words: dict) -> dict:
        bucket, key = words["bucketName"], words["objectKey"]
        where = f"s3://{bucket}/{key}"
        try:
            body = self.s3.get_object(Bucket=bucket, Key=key)["Body"].read()
        except Exception as e:  # pylint: disable=W0718
            #
            # the one AWS failure that does not stop the download: the
            # wrapper records it, and the list is reported as not
            # translated when it is loaded
            #
            status = self._s3_status(error=e)
            msg = f"s3:GetObject failed on {where}: {self._error_text(error=e)}"
            self.logger().warning(msg)
            return self._unreadable(list_id=list_id, status=status, message=msg)
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError as e:
            return self._unreadable(
                list_id=list_id, status="ERROR", message=f"{where} is not UTF-8: {e}"
            )
        entries = [line.strip() for line in text.splitlines() if line.strip() != ""]
        if not entries:
            return self._unreadable(
                list_id=list_id, status="EMPTY", message=f"{where} has no entries"
            )
        too_long = [e for e in entries if len(e) > self.MAX_ENTRY_LENGTH]
        if len(entries) > self.MAX_ENTRIES or too_long:
            return self._unreadable(
                list_id=list_id,
                status="ERROR",
                message=(
                    f"{where} is over Macie's limits ({self.MAX_ENTRIES} entries of at "
                    f"most {self.MAX_ENTRY_LENGTH} characters), so Macie cannot use it"
                ),
            )
        return {
            "status": "OK",
            "entries": entries,
            "sha256": hashlib.sha256(body).hexdigest(),
            "error": None,
        }

    def _unreadable(self, *, list_id: str, status: str, message: str) -> dict:
        self.warnings.append(
            {"code": "ALLOW_LIST_UNREADABLE", "subject": list_id, "message": message}
        )
        return {"status": status, "entries": [], "sha256": None, "error": message}

    @classmethod
    def _s3_status(cls, *, error: Exception) -> str:
        code = cls._error_code(error=error)
        if code in ("AccessDenied", "403", "AllAccessDisabled"):
            return "ACCESS_DENIED"
        if code in ("NoSuchKey", "NoSuchBucket", "404"):
            return "NOT_FOUND"
        return "ERROR"

    def _findings_filters(self) -> list[dict]:
        ids = []
        for page in self._pages(self.macie.list_findings_filters):
            ids.extend(f["id"] for f in page.get("findingsFilterListItems") or [])
        filters = [self._call(self.macie.get_findings_filter, id=i) for i in ids]
        return sorted(filters, key=lambda f: f.get("position", 0))

    def _available(self) -> list[dict]:
        items = []
        for page in self._pages(self.macie.list_managed_data_identifiers):
            items.extend(page.get("items") or [])
        return items

    def _account(self) -> str:
        return self._call(self.sts.get_caller_identity)["Account"]

    #
    # AWS calls
    #

    def _pages(self, method):
        token = None
        while True:
            page = self._call(method, **({"nextToken": token} if token else {}))
            yield page
            token = page.get("nextToken")
            if not token:
                return

    def _call(self, method, **kwargs) -> dict:
        """one AWS call; any error stops the download"""
        try:
            response = method(**kwargs)
        except Exception as e:  # pylint: disable=W0718
            name = getattr(method, "__name__", "call")
            msg = f"AWS {name} failed: {self._error_text(error=e)}"
            self.logger().exception(msg)
            raise MacieException(msg) from e
        return self._verbatim(value=response)

    @classmethod
    def _verbatim(cls, *, value):
        """a response as JSON: no ResponseMetadata, datetimes as UTC ISO
        8601 strings, which is the API's own wire format"""
        if isinstance(value, dict):
            return {
                k: cls._verbatim(value=v)
                for k, v in value.items()
                if k != "ResponseMetadata"
            }
        if isinstance(value, list):
            return [cls._verbatim(value=v) for v in value]
        if isinstance(value, datetime.datetime):
            return cls._iso(when=value)
        return value

    @classmethod
    def _iso(cls, *, when: datetime.datetime) -> str:
        if when.tzinfo is None:
            when = when.replace(tzinfo=datetime.timezone.utc)
        when = when.astimezone(datetime.timezone.utc)
        spec = "milliseconds" if when.microsecond else "seconds"
        return when.replace(tzinfo=None).isoformat(timespec=spec) + "Z"

    def _now(self) -> str:
        return self._iso(when=self.clock())

    @classmethod
    def _error_code(cls, *, error: Exception) -> str | None:
        response = getattr(error, "response", None)
        if isinstance(response, dict):
            return (response.get("Error") or {}).get("Code")
        return None

    @classmethod
    def _error_text(cls, *, error: Exception) -> str:
        code = cls._error_code(error=error)
        return f"{code}: {error}" if code else f"{error}"

    @classmethod
    def _unique(cls, ids: list[str]) -> list[str]:
        seen, out = set(), []
        for i in ids:
            if i not in seen:
                seen.add(i)
                out.append(i)
        return out

    def _fail(self, msg: str) -> None:
        self.logger().error(msg)
        raise MacieException(msg)
