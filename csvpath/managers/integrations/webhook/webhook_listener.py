import requests
import threading

from abc import ABC
from csvpath.util.box import Box
from csvpath.managers.metadata import Metadata
from csvpath.managers.listener import Listener
from csvpath.matching.util.expression_utility import ExpressionUtility

#
# ~
#    webhook-url: https://zapier.com/hooks/asdf
#    webhook-data: name > var|name, phone > $mygroup#result.variables.cell, $.csvpath.total_lines
#
#
#    webhook-file: $.results.files.data, $mygroup#myinstance.results.files.errors
#    $.results.
#    $clean-invoices.results.acme/invoices/2025/Feb:0.step-three#var|cell
#    $mygroup#myinstance.variables.cell
#
# ~
#


class WebhookException(Exception):
    ...


class WebhookListener(Listener, threading.Thread):
    ON_ALL = "on_complete_all_webhook"
    ON_VALID = "on_complete_valid_webhook"
    ON_INVALID = "on_complete_invalid_webhook"
    ON_ERRORS = "on_complete_errors_webhook"

    HOOKS = None
    URLS = None

    ALL_URL = "all_webhook_url"
    VALID_URL = "valid_webhook_url"
    INVALID_URL = "invalid_webhook_url"
    ERRORS_URL = "errors_webhook_url"

    def __init__(self, config=None):
        super().__init__(config)
        self._url = None
        self.csvpaths = None
        self.result = None
        self.metadata = None
        self._timeout = -1
        if WebhookListener.HOOKS is None:
            WebhookListener.HOOKS = [
                WebhookListener.ON_ALL,
                WebhookListener.ON_VALID,
                WebhookListener.ON_INVALID,
                WebhookListener.ON_ERRORS,
            ]
        if WebhookListener.URLS is None:
            WebhookListener.URLS = {
                WebhookListener.ON_ALL: WebhookListener.ALL_URL,
                WebhookListener.ON_VALID: WebhookListener.VALID_URL,
                WebhookListener.ON_INVALID: WebhookListener.INVALID_URL,
                WebhookListener.ON_ERRORS: WebhookListener.ERRORS_URL,
            }

    @property
    def timeout(self) -> int:
        if self._timeout == -1:
            t = self.csvpaths.config.get(section="webhook", name="timeout", default=3)
            t = ExpressionUtility.to_float(t)
            if isinstance(t, float):
                self._timeout = t
            else:
                self._timeout = 3
        return self._timeout

    @property
    def csvpath(self):
        return self.result.csvpath

    def run(self):
        self._metadata_update(self.metadata)
        self.csvpaths.wrap_up()

    def metadata_update(self, mdata: Metadata) -> None:
        self.metadata = mdata
        self.start()

    def _metadata_update(self, mdata: Metadata) -> None:
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        for t in WebhookListener.HOOKS:
            try:
                self._do_hook_if(mdata=mdata, atype=t)
            except Exception as e:
                if isinstance(e, WebhookException):
                    raise
                msg = f"WebhookListener could not call {t} webhook: {type(e)}: {e}"
                self.csvpaths.logger.error(msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise WebhookException(msg)

    def _do_hook_if(self, *, mdata: Metadata, atype: str) -> None:
        if not self._run(mdata, atype):
            return
        url = self._url_for_type(mdata, WebhookListener.URLS[atype])
        if url is None:
            self.csvpaths.logger.debug(
                "Nothing to do for webhook url %s", WebhookListener.URLS[atype]
            )
            return
        payload = self._payload_for_type(mdata, atype)
        #
        # prep request
        #
        headers = {"Content-Type": "application/json"}
        #
        # send
        #
        x = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if x and x.status_code != 200:
            if self.csvpaths is not None:
                self.csvpaths.logger.warning(
                    "WebhookListener received status code %s from %s",
                    x.status_code,
                    "",
                )
            elif self.result is not None:
                self.result.csvpath.logger.warning(
                    "WebhookListener received status code %s from %s",
                    x.status_code,
                    "",
                )
            else:
                msg = f"WebhookListener received status code {x.status_code} from {self.url}"
                self.csvpaths.logger.error(msg)
                if self.csvpaths.ecoms.do_i_raise():
                    raise WebhookException(msg)
