import unittest
import json
from pathlib import Path
from csvpath.managers.paths.paths_descriptor import (
    Transfer,
    Transfers,
    GroupTransfers,
    GroupConfig,
    Config,
)
from csvpath.util.file_readers import DataFileReader


class TestCsvPathsExamplesTransfersLoad(unittest.TestCase):
    def test_transfer_loads(self):
        t = Transfer(file="data", transfer_to="var_one")
        assert t is not None

    def test_transfers_loads(self):
        t = Transfers(
            on_complete_all=[
                Transfer(file="data", transfer_to="var_one"),
                Transfer(file="printouts", transfer_to="var_two"),
            ],
            on_complete_invalid=[
                Transfer(file="unmatched", transfer_to="dumpme"),
            ],
            on_complete_valid=[
                Transfer(file="vars.json", transfer_to="test"),
            ],
        )
        assert t is not None

    def test_group_transfers_loads(self):
        gt = GroupTransfers(
            path_transfers={
                "output": Transfers(
                    on_complete_all=[
                        Transfer(file="data", transfer_to="var_one"),
                        Transfer(file="printouts", transfer_to="var_two"),
                    ],
                    on_complete_invalid=[
                        Transfer(file="unmatched", transfer_to="dumpme"),
                    ],
                    on_complete_valid=[
                        Transfer(file="vars.json", transfer_to="test"),
                    ],
                )
            }
        )
        assert gt is not None

    def test_group_config_loads(self):
        gc = GroupConfig(
            transfers=GroupTransfers(
                path_transfers={
                    "output": Transfers(
                        on_complete_all=[
                            Transfer(file="data", transfer_to="var_one"),
                            Transfer(file="printouts", transfer_to="var_two"),
                        ],
                    )
                }
            )
        )
        assert gc is not None

    def test_config_loads(self):
        config = Config(
            groups={
                "order validations": GroupConfig(
                    transfers=GroupTransfers(
                        path_transfers={
                            "output": Transfers(
                                on_complete_all=[
                                    Transfer(file="data", transfer_to="var_one"),
                                    Transfer(file="printouts", transfer_to="var_two"),
                                ],
                                on_complete_invalid=[
                                    Transfer(file="unmatched", transfer_to="dumpme"),
                                ],
                                on_complete_valid=[
                                    Transfer(file="vars.json", transfer_to="test"),
                                ],
                            )
                        }
                    )
                )
            }
        )
        assert config is not None

    def test_load_path_description_from_file(self) -> None:
        path = (
            Path(".")
            / "tests"
            / "csvpaths"
            / "examples"
            / "csvpaths_examples_transfers"
            / "definition.json"
        )
        path = str(path)

        with DataFileReader(path) as file:
            j = json.load(file.source)
            GroupConfig(**j["_config"])
