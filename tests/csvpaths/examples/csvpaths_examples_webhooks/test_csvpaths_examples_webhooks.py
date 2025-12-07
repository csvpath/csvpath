import unittest
import os
from csvpath import CsvPaths
from csvpath.managers.integrations.webhook.webhook_listener import (
    WebhookException,
    WebhookListener,
)
from csvpath.managers.integrations.webhook.webhook_results_listener import (
    WebhookResultsListener,
)
from csvpath.managers.test_listener import TestListener


class TestCsvPathsExamplesWebhooks(unittest.TestCase):
    def test_webhooks_1(self):
        try:
            paths = CsvPaths()
            paths.config.add_to_config("errors", "csvpath", "collect, print")
            paths.config.add_to_config("errors", "csvpaths", "collect, print")
            paths.config.add_to_config("webhook", "timeout", ".25")

            paths.file_manager.add_named_file(
                name="hooks",
                path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvs{os.sep}hooks.csv",
            )
            paths.paths_manager.add_named_paths_from_json(
                file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths{os.sep}hooks.json"
            )
            paths.fast_forward_paths(pathsname="hooks", filename="hooks")
            #
            # this will blow up under some adverse conditions and will itself
            # raise for a non-200. but don't yet have a good way to know it ran
            # and that the right stuff happened without looking at the test
            # container.  :/
            #
        except WebhookException as e:
            # presumably the webhook test container is not working. this is not
            # a serious automated test. but it's useful for more manual runs.
            #
            print(f"test_webhooks_1: error: {type(e)}: {e}")

    def test_webhooks_2(self) -> None:
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "collect, print")
        paths.config.add_to_config("errors", "csvpaths", "collect, print")
        paths.config.add_to_config(
            "listeners",
            "test.results",
            "from csvpath.managers.test_listener import TestListener",
        )
        paths.config.add_to_config("listeners", "groups", "test")

        paths.paths_manager.add_named_paths_from_json(
            file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths{os.sep}hooks.json"
        )
        self._do_test(paths, paths_name="hooks")

    def _do_test(self, paths, paths_name):
        print(f"paths: {paths}")
        print(f"paths.config: {paths.config}")
        print(f"paths.config.configpath: {paths.config.configpath}")
        print(
            f"paths.config.namedpaths: {paths.config.get(section='inputs', name='csvpaths')}"
        )
        paths.file_manager.add_named_file(
            name="hooks",
            path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvs{os.sep}hooks.csv",
        )
        paths.paths_manager.add_named_paths_from_dir(
            name="hooks2",
            directory=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths",
        )
        paths.fast_forward_paths(pathsname=paths_name, filename="hooks")
        #
        # get the metadata from ^^^^ for replay
        #
        mdata = TestListener.METADATA
        #
        # setup the URLS and HOOKS
        #
        wl = WebhookListener(paths.config)
        wl.csvpaths = paths
        #
        # create the listener under test
        #
        listener = WebhookResultsListener(paths.config)
        listener.csvpaths = paths
        #
        # get the data
        #
        htype = WebhookListener.HOOKS[0]
        url = listener._url_for_type(mdata, WebhookListener.URLS[htype])
        payload = listener._payload_for_type(mdata, htype)
        #
        # check it
        #
        assert url == "http://localhost:8000/json-hook"
        """
            {
              "type": "all",
              "me": "one",
              "name": "many one",
              "time": "2025-04-03 14:11:23.353189+00:00"
            }
        """
        assert payload.get("type") == "all"
        assert payload.get("me") in ["one", "two"]
        assert payload.get("name") in ["many one", "many_two"]
        assert payload.get("time") is not None
        #
        # check errors
        #
        htype = WebhookListener.HOOKS[3]
        url = listener._url_for_type(mdata, WebhookListener.URLS[htype])
        payload = listener._payload_for_type(mdata, htype)
        assert "errors" in payload
        assert len(payload.get("errors")) > 0

    def test_store_webhooks_for_paths(self):
        #
        # 1. load a named-paths group w/o a json
        # 2. get the config dict from the group
        # 3. setup the webhook
        # 4. store the json with the updated config
        #
        paths = CsvPaths()
        paths.config.add_to_config("errors", "csvpath", "collect, print")
        paths.config.add_to_config("errors", "csvpaths", "collect, print")
        paths.config.add_to_config(
            "listeners",
            "test.results",
            "from csvpath.managers.test_listener import TestListener",
        )
        paths.config.add_to_config("listeners", "groups", "test")

        paths.paths_manager.add_named_paths_from_dir(
            name="hooks2",
            directory=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths",
        )
        cfg = paths.paths_manager.get_config_for_paths("hooks2")
        hooks2 = cfg.get("hooks2")
        if hooks2 is None:
            hooks2 = {}
            cfg["hooks2"] = hooks2
        hooks2[
            "on_complete_all_webhook"
        ] = "type > all, me > var|me, name > meta|name, time > var|now"
        hooks2[
            "on_complete_valid_webhook"
        ] = "type > valid, me > var|me, name > meta|name, time > var|now"
        hooks2[
            "on_complete_invalid_webhook"
        ] = "type > invalid, me > var|me, name > meta|name, time > var|now"
        hooks2[
            "on_complete_errors_webhook"
        ] = "type > errors, me > var|me, name > meta|name, time > var|now"

        hooks2["all_webhook_url"] = "http://localhost:8000/json-hook"
        hooks2["valid_webhook_url"] = "http://localhost:8000/json-hook"
        hooks2["invalid_webhook_url"] = "http://localhost:8000/json-hook"
        hooks2["errors_webhook_url"] = "http://localhost:8000/json-hook"

        paths.paths_manager.store_config_for_paths("hooks2", cfg)

        self._do_test(paths, paths_name="hooks2")
