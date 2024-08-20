class Save:
    @classmethod
    def _save(self, path, name):
        path._save_scan_dir = "tests/grammar/scan"
        path._save_match_dir = "tests/grammar/match"
        path._run_name = name
