import json
import pytest
from pydantic import ValidationError

from csvpath.managers.files.file_descriptor import Config, OnArrival, ServerConfig


class TestCsvPathsManagersFileDescriber:
    def round_trip(self, definition: Config) -> Config:
        """Serialize to JSON string, then parse back — mimics file write + read."""
        raw = definition.model_dump_json(exclude_none=True)
        return Config.model_validate_json(raw)

    @pytest.fixture
    def minimal_definition(self) -> Config:
        """Only the fields that must always be present — everything else absent."""
        return Config()

    @pytest.fixture
    def full_definition(self) -> Config:
        return Config(
            template=":0/:3/my/:filename",
            on_arrival=OnArrival(
                named_paths_group="order validations",
                run_method="collect_paths",
            ),
            sources={
                "qa": ServerConfig(
                    address="localhost",
                    port=2022,
                    username="LOCAL_USER",
                    password="LOCAL_PASS",
                ),
                "prod": ServerConfig(
                    address="192.168.1.181",
                    port=22,
                    username="USER",
                    password="PASS",
                ),
            },
        )

    # ----------------------
    # Round-trip tests
    # ----------------------

    def test_paths_descriptor_full_definition_round_trips(self, full_definition):
        restored = self.round_trip(full_definition)
        assert restored == full_definition

    def test_paths_descriptor_minimal_definition_round_trips(self, minimal_definition):
        restored = self.round_trip(minimal_definition)
        assert restored == minimal_definition

    def test_paths_descriptor_round_trip_via_dict(self, full_definition):
        """model_dump / model_validate path (dict, not JSON string)."""
        data = full_definition.model_dump(exclude_none=True)
        restored = Config.model_validate(data)
        assert restored == full_definition

    def test_paths_descriptor_exclude_none_omits_missing_fields(
        self, minimal_definition
    ):
        data = minimal_definition.model_dump(exclude_none=True)
        assert data == {}

    def test_paths_descriptor_json_structure_matches_expected_shape(
        self, full_definition
    ):
        """Sanity-check the serialized JSON keys match what definition.json expects."""
        data = json.loads(full_definition.model_dump_json(exclude_none=True))
        assert "template" in data
        assert "on_arrival" in data
        assert "named_paths_group" in data["on_arrival"]
        assert "run_method" in data["on_arrival"]
        assert "sources" in data
        assert "qa" in data["sources"]
        assert "prod" in data["sources"]

    # ----------------------
    # ServerConfig — port
    # ----------------------

    def test_paths_descriptor_port_int_accepted(self):
        s = ServerConfig(address="localhost", port=22, username="u", password="p")
        assert s.port == 22

    def test_paths_descriptor_port_string_coerced(self):
        s = ServerConfig(address="localhost", port="2022", username="u", password="p")
        assert s.port == 2022
        assert isinstance(s.port, int)

    def test_paths_descriptor_port_string_survives_round_trip(self):
        """Port arrives as a string from JSON and must round-trip as int."""
        raw = '{"address":"localhost","port":"2022","username":"u","password":"p"}'
        s = ServerConfig.model_validate_json(raw)
        assert s.port == 2022

    def test_paths_descriptor_invalid_port_raises(self):
        with pytest.raises(ValidationError):
            ServerConfig(
                address="localhost", port="not-a-number", username="u", password="p"
            )

    # ----------------------
    # Config — partial data
    # ----------------------

    def test_paths_descriptor_template_only(self):
        d = Config(template=":0/:3/my/:filename")
        restored = self.round_trip(d)
        assert restored.template == ":0/:3/my/:filename"
        assert restored.on_arrival is None
        assert restored.sources is None

    def test_paths_descriptor_on_arrival_only(self):
        d = Config(on_arrival=OnArrival(named_paths_group="group-a"))
        restored = self.round_trip(d)
        assert restored.on_arrival.named_paths_group == "group-a"
        assert restored.on_arrival.run_method is None

    def test_paths_descriptor_sources_without_on_arrival(self):
        d = Config(
            sources={
                "dev": ServerConfig(
                    address="localhost", port=22, username="u", password="p"
                )
            }
        )
        restored = self.round_trip(d)
        assert restored.sources["dev"].address == "localhost"
        assert restored.on_arrival is None

    def test_paths_descriptor_empty_sources_dict(self):
        d = Config(sources={})
        restored = self.round_trip(d)
        assert restored.sources == {}

    def test_paths_descriptor_extra_keys_preserved(self):
        """extra='allow' means unknown keys survive a round-trip."""
        raw = '{"template": "t", "future_field": "some_value"}'
        d = Config.model_validate_json(raw)
        assert d.future_field == "some_value"  # type: ignore[attr-defined]
