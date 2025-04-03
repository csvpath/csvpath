import os
import json
from csvpath.managers.metadata import Metadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.util.var_utility import VarUtility
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader
from csvpath.matching.util.expression_utility import ExpressionUtility
from .webhook_listener import WebhookListener, WebhookException


class WebhookResultsListener(WebhookListener):
    def __init__(self, config=None):
        WebhookListener.__init__(self, config=config)

    #
    # TODO: add mode and result listener
    # this is probably a good model for the result csvpath-by-csvpath mode, but not the results
    #
    """
    @property
    def url(self):
        if self._url is None:
            if self.result is None:
                self.csvpaths.logger.info(
                    "Cannot send to webhook because there is no result"
                )
            self._url = self.csvpath.metadata.get("webhook-url")
            if self._url is not None:
                self._url = self._url.strip()
        return self._url
    """

    def _run(self, mdata: Metadata, atype: str) -> bool:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if not isinstance(mdata, ResultsMetadata):
            return False
        if atype is None:
            raise ValueError("Type cannot be None")
        #
        # we don't care about run starts
        #
        if mdata.time_completed is None:
            return False
        #
        # type checks
        #
        if atype.find("invalid") > -1:
            if mdata.all_valid is True:
                return False
            return True
        if atype.find("valid") > -1:
            if mdata.all_valid is not True:
                return False
            return True
        if atype.find("errors") > -1:
            i = ExpressionUtility.to_int(mdata.error_count)
            #
            # shouldn't happen. if it does should we raise?
            #
            if not isinstance(i, int):
                return False
            if i <= 0:
                return False
        return True

    def _url_for_type(self, mdata: Metadata, atype: str):
        cfg = self.csvpaths.paths_manager.get_config_for_paths(mdata.named_paths_name)
        if cfg is None:
            return None
        return cfg.get(atype)

    def _payload_for_type(self, mdata: Metadata, atype: str) -> dict:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if atype is None:
            raise ValueError("Type cannot be None")
        if not isinstance(mdata, ResultsMetadata):
            raise WebhookException(
                "Cannot create a payload for a {type(mdata)}. Check your config."
            )
        if self.csvpaths is None:
            raise ValueError("CsvPaths cannot be None")
        #
        # find the named-paths config. look for a webhook definition.
        #
        # in _config we get like: "on_complete_valid_webhook":["key":"static value or var|name or meta|name]
        #
        # if we are sending errors we don't need anything in cfg. we just attach the errors.json list
        # like { errors:[], fields:[] }
        #
        cfg = self.csvpaths.paths_manager.get_config_for_paths(mdata.named_paths_name)
        if cfg is None:
            return {}
        on = cfg.get(atype)
        if on and len(on) > 0:
            if atype == WebhookListener.ON_ERRORS:
                return self._errors(atype=atype, mdata=mdata, cfg=cfg)
            return self._payload(atype=atype, mdata=mdata, cfg=cfg)
        return None

    def _payload(self, *, mdata: Metadata, atype: str, cfg) -> dict:
        metadata = self.get_data(mdata, "meta.json")
        variables = self.get_data(mdata, "vars.json")
        v = cfg.get(atype)
        pairs = VarUtility.get_value_pairs_from_value(
            metadata=metadata, variables=variables, value=v
        )
        payload = {}
        for pair in pairs:
            payload[pair[0]] = pair[1]
        return payload

    def _errors(self, *, mdata: Metadata, atype: str, cfg) -> dict:
        payload = self._payload(mdata=mdata, atype=atype, cfg=cfg)
        errors = self.csvpaths.results_manager.get_errors(mdata.named_results_name)
        if errors is None:
            errors = []
        errors = [e.to_json() for e in errors]
        payload["errors"] = errors
        return payload

    def instance_homes(self, mdata: Metadata) -> list[str]:
        p = mdata.run_home
        nos = Nos(p)
        lst = nos.listdir()
        homes = []
        for f in lst:
            f = os.path.join(p, f)
            nos.path = f
            if nos.isfile():
                continue
            homes.append(f)
        return homes

    def get_data(self, mdata: Metadata, filename: str) -> dict:
        m = {}
        homes = self.instance_homes(mdata)
        for f in homes:
            f = os.path.join(f, filename)
            nos = Nos(f)
            if nos.exists():
                with DataFileReader(f) as file:
                    j = json.load(file.source)
                    if filename == "meta.json":
                        j = j.get("metadata")
                    m = {**m, **j}
        return m
