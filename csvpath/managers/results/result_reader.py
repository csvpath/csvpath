import os
import json


class ResultReader:
    @classmethod
    def manifest(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "manifest.json")
        if not os.path.exists(mp):
            with open(mp, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=2)
                return {}
        with open(mp, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None

    @classmethod
    def meta(self, result_home: str) -> dict | None:
        mp = os.path.join(result_home, "meta.json")
        if not os.path.exists(mp):
            with open(mp, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=2)
                return {}
        with open(mp, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None
