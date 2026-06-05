import json
import os
import unittest
from unittest.mock import patch, MagicMock

from csvpath import CsvPaths
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


class TestWebhookListener2(unittest.TestCase):
    def _make_mock_response(self, status_code=200, json_body=None):
        """Build a fake requests.Response-like object."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = json.dumps(json_body or {"ok": True})
        mock_response.json.return_value = json_body or {"ok": True}
        return mock_response

    def test_webhooks_1_deterministic(self):
        # Patch _do_send on the class so no real HTTP call is made.
        # The mock returns a controlled 200 response every time it's called.
        mock_response = self._make_mock_response(
            status_code=200, json_body={"ok": True}
        )

        with patch(
            "csvpath.managers.integrations.webhook.webhook_listener.WebhookListener._do_send",
            return_value=mock_response,
        ) as mock_send:
            paths = CsvPaths()

            # --- existing setup ---
            g = paths.config.get(section="listeners", name="groups")
            li = paths.config.get(section="listeners", name="webhook.results")
            if li is None:
                paths.config.set(
                    section="listeners",
                    name="webhook.results",
                    value="from csvpath.managers.integrations.webhook.webhook_results_listener import WebhookResultsListener",
                )
            paths.config.set(section="listeners", name="groups", value=f"{g},webhook")
            paths.config.add_to_config("errors", "csvpath", "collect, print")
            paths.config.add_to_config("errors", "csvpaths", "collect, print")
            paths.config.add_to_config("webhook", "timeout", ".25")

            if paths.file_manager.has_named_file("hooks"):
                paths.file_manager.remove_named_file("hooks")
            if paths.paths_manager.has_named_paths("hooks"):
                paths.paths_manager.remove_named_paths("hooks")

            paths.file_manager.add_named_file(
                name="hooks",
                path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvs{os.sep}hooks.csv",
            )
            paths.paths_manager.add_named_paths_from_json(
                file_path=f"tests{os.sep}csvpaths{os.sep}examples{os.sep}csvpaths_examples_webhooks{os.sep}csvpaths{os.sep}hooks.json"
            )

            ref = paths.fast_forward_paths(pathsname="hooks", filename="hooks")

            # No time.sleep needed — _do_send returns instantly
            paths.config.set(section="listeners", name="groups", value=g)

            # --- assertions ---
            results = paths.results_manager.get_named_results(ref)
            self.assertIsNotNone(results)
            self.assertEqual(len(results), 2)

            rundir = results[0].run_dir
            self.assertIsNotNone(rundir)

            path = Nos(rundir).join("webhook-on_complete_all.json")
            self.assertTrue(
                Nos(path).exists(), f"Expected webhook output file at: {path}"
            )

            with DataFileReader(path) as file:
                js = json.load(file.source)
                self.assertIsNotNone(js)
                self.assertIn("url", js)
                self.assertIn("response", js)
                self.assertIn("code", js["response"])
                self.assertEqual(js["response"]["code"], 200)

            # Verify _do_send was actually called (guards against the hook being skipped)
            self.assertTrue(
                mock_send.called,
                "_do_send was never called — webhook may not have fired",
            )
