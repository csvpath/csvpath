import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from csvpath.odcs.conversion_report import ConversionReport
from csvpath.odcs.csvpath_text_utility import CsvPathTextUtility as csut

from .arn_utility import ArnUtility as arut
from .custom_identifier import CustomIdentifier
from .macie_exceptions import MacieException
from .macie_wrapper_loader import MacieWrapperLoader
from .regex_utility import RegexUtility as reut


@dataclass
class MacieConversion:
    """the result of converting one Macie wrapper.

    name:    the csvpath's id, and the named-paths group name to use
    csvpath: the csvpath text. With no data file path its root is $[1*],
             ready to be loaded into a named-paths group.
    report:  what was not translated, e.g. managed identifiers, text allow
             lists and findings filters, plus the wrapper's own warnings
    """

    name: str
    csvpath: str
    report: ConversionReport = field(default_factory=ConversionReport)


class MacieConverter:
    """converts a Macie wrapper into one csvpath of CsvPath Validation
    Language: one wrapper, one csvpath, one named-paths group.

        wrapper = MacieWrapperLoader.from_path(path="hr-employee-ids.macie.json")
        conversion = MacieConverter(wrapper=wrapper).convert()
        conversion.csvpath           # csvpath text
        conversion.report.skipped    # what was not translated

    Translated today: custom data identifiers (macie_cdi) and regex allow
    lists (macie_allow_regex). Reported as skipped: managed identifiers,
    text allow lists (they need load_list(), #470) and findings filters,
    which act on findings after detection.

    A value the csvpath can't express, e.g. a keyword containing a double
    quote or "|", fails the conversion: skipping part of an identifier
    would silently change what it detects.

    The design is in specs/macie/transpile-design.md."""

    #
    # the generated csvpath's own modes. see the spec for why each is set.
    #
    MODES = [
        ("logic-mode", "OR"),
        ("print-mode", "separate"),
        ("validation-mode", "collect, match, no-print, no-raise, no-fail, no-stop"),
    ]
    MAX_FINDINGS = 10000
    MAX_DETAIL = 15
    #
    # names become the csvpath id and the named-paths group name
    #
    NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")

    def __init__(self, *, wrapper: dict) -> None:
        if wrapper is None:
            raise ValueError("wrapper cannot be None")
        self.wrapper = MacieWrapperLoader.validate(wrapper=wrapper)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def convert(
        self,
        *,
        name: str | None = None,
        path: str | None = None,
        max_findings: int = MAX_FINDINGS,
        max_detail: int = MAX_DETAIL,
    ) -> MacieConversion:
        """name defaults to the Macie job's or template's name; a
        handcrafted wrapper must be given one. path, if given, is a data
        file the csvpath can run against stand-alone."""
        path = csut.existing_data_path(path=path)
        for n, v, minimum in [
            ("max_findings", max_findings, 1),
            ("max_detail", max_detail, 0),
        ]:
            if not isinstance(v, int) or isinstance(v, bool) or v < minimum:
                raise ValueError(f"{n} must be an int of at least {minimum}, not {v!r}")
        name = self._name(name=name)
        report = ConversionReport()
        body = []
        body += self._allow_lists(name=name, report=report)
        body += self._custom_identifiers()
        if not any(b.startswith("macie_cdi(") for b in body):
            self._fail(
                f"Macie wrapper for {name} has no custom data identifiers to convert"
            )
        self._skip_managed(name=name, report=report)
        self._skip_findings_filters(name=name, report=report)
        self._report_warnings(name=name, report=report)
        body.append("last.nocontrib() -> macie_report()")
        metadata = self._metadata(
            name=name, max_findings=max_findings, max_detail=max_detail
        )
        csvpath = self._text(metadata=metadata, path=path, body=body)
        return MacieConversion(name=name, csvpath=csvpath, report=report)

    # =============
    # parts
    # =============

    def _name(self, *, name: str | None) -> str:
        if name is None:
            aws = self.wrapper.get("aws") or {}
            source = aws.get("classificationJob") or aws.get(
                "sensitivityInspectionTemplate"
            )
            name = source.get("name") if source else None
        if name is None:
            self._fail("A handcrafted Macie wrapper needs a name to convert")
        if not isinstance(name, str) or self.NAME.fullmatch(name) is None:
            self._fail(
                f"Name {name!r} must be letters, digits, '.', '_' or '-', starting "
                "with a letter or digit; pass a name to convert()"
            )
        return name

    def _metadata(
        self, *, name: str, max_findings: int, max_detail: int
    ) -> list[tuple[str, str]]:
        source = self.wrapper["source"]
        origin = source["origin"]
        md = [("id", name), ("macie-origin", origin)]
        if origin == "job":
            md.append(("macie-job-id", source["job_id"]))
        elif origin == "template":
            md.append(("macie-template-id", source["template_id"]))
        if origin != "handcrafted":
            md.append(("macie-account", source["account_id"]))
            md.append(("macie-region", source["region"]))
        arn = self._source_arn()
        if arn is not None:
            md.append(("macie-source-arn", arut.to_metadata(arn=arn)))
        if origin != "handcrafted":
            md.append(
                (
                    "macie-downloaded-at",
                    self._basic_time(value=source["downloaded_at"]),
                )
            )
        md.append(("macie-max-findings", f"{max_findings}"))
        md.append(("macie-max-detail", f"{max_detail}"))
        md += self.MODES
        for k, v in md:
            if ":" in v or "~" in v or "\n" in v:
                self._fail(f"Metadata {k} value {v!r} would break the csvpath comment")
        return md

    def _source_arn(self) -> str | None:
        aws = self.wrapper.get("aws") or {}
        job = aws.get("classificationJob")
        if job is not None:
            return job.get("jobArn")
        template = aws.get("sensitivityInspectionTemplate")
        if template is not None:
            return template.get("arn")
        return None

    def _allow_lists(self, *, name: str, report: ConversionReport) -> list[str]:
        out = []
        for i, a in enumerate(self.wrapper.get("allowLists") or []):
            settings = a["settings"]
            criteria = settings["criteria"]
            if "regex" in criteria:
                out.append(
                    "macie_allow_regex.nocontrib("
                    f"{self._string(value=settings['name'])}, "
                    f"{self._regex(pattern=criteria['regex'])})"
                )
            else:
                report.skip(
                    obj=name,
                    location=f"allowLists[{i}]",
                    feature="allowList.s3WordsList",
                    reason=(
                        f"Text allow list {settings['name']} is not translated yet: "
                        "it needs load_list() (#470)"
                    ),
                )
        return out

    def _custom_identifiers(self) -> list[str]:
        out = []
        for c in self.wrapper.get("customDataIdentifiers") or []:
            #
            # builds and checks the identifier exactly as macie_cdi() will
            #
            cdi = CustomIdentifier.from_aws(cdi=c)
            arn = c.get("arn")
            if arn is not None:
                arut.check(arn=arn)
            args = [
                self._string(value=cdi.name),
                self._string(value="" if arn is None else arn),
                self._regex(pattern=cdi.pattern),
                self._entries(name=cdi.name, kind="keyword", entries=cdi.keywords),
                self._entries(
                    name=cdi.name, kind="ignore word", entries=cdi.ignore_words
                ),
                f"{cdi.distance}",
                self._string(value=cdi.severity.to_text()),
            ]
            lines = ",\n        ".join(args)
            out.append(f"macie_cdi(\n        {lines}\n    )")
        return out

    def _skip_managed(self, *, name: str, report: ConversionReport) -> None:
        managed = self.wrapper.get("managedDataIdentifiers") or {}
        for i, mdi in enumerate(managed.get("resolved") or []):
            report.skip(
                obj=name,
                location=f"managedDataIdentifiers.resolved[{i}]",
                feature="managedDataIdentifier",
                reason=f"Managed data identifier {mdi} is not translated yet",
            )

    def _skip_findings_filters(self, *, name: str, report: ConversionReport) -> None:
        for i, f in enumerate(self.wrapper.get("findingsFilters") or []):
            report.skip(
                obj=name,
                location=f"findingsFilters[{i}]",
                feature="findingsFilter",
                reason=(
                    f"Findings filter {f.get('name')} acts on findings after "
                    "detection and is not translated"
                ),
            )

    def _report_warnings(self, *, name: str, report: ConversionReport) -> None:
        for i, w in enumerate(self.wrapper.get("warnings") or []):
            report.skip(
                obj=name,
                location=f"warnings[{i}]",
                feature=f"warning.{w['code']}",
                reason=w.get("message") or w["code"],
            )

    def _text(self, *, metadata: list, path: str, body: list[str]) -> str:
        md = "\n".join(f"  {k}: {v}" for k, v in metadata)
        lines = "\n".join(f"    {b}" for b in body)
        return f"~\n{md}\n~\n${path}[1*][\n{lines}\n]\n"

    # =============
    # values
    # =============

    def _string(self, *, value: str) -> str:
        try:
            return csut.string(value=value)
        except ValueError as e:
            self._fail(f"{e}")

    def _entries(self, *, name: str, kind: str, entries: list[str]) -> str:
        for e in entries:
            if "|" in e:
                self._fail(
                    f"The {kind} {e!r} of {name} contains '|', which separates "
                    f"{kind}s in macie_cdi()"
                )
        return self._string(value="|".join(entries))

    def _regex(self, *, pattern: str) -> str:
        """a /.../ regex literal holding the Macie pattern as written. The
        pattern must translate and compile as macie_cdi() will compile it.
        Slashes are escaped so the literal ends where it should."""
        reut.compile(pattern=pattern)
        out = []
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "\\" and i + 1 < len(pattern):
                out.append(pattern[i : i + 2])
                i += 2
                continue
            out.append("\\/" if c == "/" else c)
            i += 1
        return f"/{''.join(out)}/"

    def _basic_time(self, *, value: str) -> str:
        """an ISO 8601 UTC time in basic format, e.g. 20261029T174000Z: the
        extended format's ':' would break the metadata. The wrapper schema
        has already required UTC with a trailing Z."""
        try:
            t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError) as e:
            self.logger.exception("Bad downloaded_at %r", value)
            raise MacieException(f"Bad downloaded_at {value!r}: {e}") from e
        return t.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _fail(self, msg: str) -> None:
        self.logger.error(msg)
        raise MacieException(msg)
