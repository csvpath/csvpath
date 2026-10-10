import pytest
from unittest.mock import MagicMock, patch

from csvpath import CsvPath
from csvpath.managers.metadata import Metadata
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.integrations.ol.v2.util.protocol_utility import ProtocolUtility

# derived from the class so the patch targets always match the import above
MODULE = ProtocolUtility.__module__

DEFAULTS = dict(files="/data/files", csvpaths="/data/paths", archive="/data/archive")


# ---------------------------------------------------------------- helpers


class FakeNos:
    """Deterministic stand-in for Nos so tests never touch fs/network."""

    def __init__(self, path):
        self.path = str(path)
        self.is_azure = self.path.startswith("azure://")
        self.is_local = not any(
            self.path.startswith(p) for p in ("azure://", "gs://", "s3://", "sftp://")
        )


def bare_config(**values):
    """
    MagicMock config whose get() returns values[name] when present, else the
    default= the caller passed. Lets us exercise "key not configured" paths,
    and gives us a mock logger to assert on.
    """
    cfg = MagicMock()

    def get(*, section=None, name=None, default=None):
        return values.get(name, default)

    cfg.get.side_effect = get
    return cfg


def file_md(name="myfile"):
    m = MagicMock(spec=FileMetadata)
    m.named_file_name = name
    return m


def paths_md(name="mypaths"):
    m = MagicMock(spec=PathsMetadata)
    m.named_paths_name = name
    return m


def results_md(name="myresults"):
    m = MagicMock(spec=Metadata)
    m.named_results_name = name
    return m


# --------------------------------------------------------------- fixtures


@pytest.fixture(autouse=True)
def fake_nos():
    with patch(f"{MODULE}.Nos", FakeNos):
        yield


@pytest.fixture
def azure_protocol():
    with patch(f"{MODULE}.azut") as azut:
        azut.my_protocol.return_value = "wasbs"
        yield azut


@pytest.fixture
def config():
    """A real Config, with every key the class reads set explicitly."""
    cfg = CsvPath().config
    cfg.set(section="inputs", name="files", value="/data/files")
    cfg.set(section="inputs", name="csvpaths", value="/data/paths")
    cfg.set(section="results", name="archive", value="/data/archive")
    cfg.set(section="openlineage", name="namespace_pattern", value="{root_path}")
    cfg.set(section="openlineage", name="namespace_prefix", value="")
    cfg.set(section="openlineage", name="path_separator", value=".")
    return cfg


# ------------------------------------------------------------------ tests


class TestCsvPathsExamplesOpenLineageProtocolUtility:
    # ------------------------------------------- update_protocol_if_2 (wiring)

    def test_csvpaths_examples_ol_config_none_raises(self):
        with pytest.raises(ValueError, match="Config"):
            ProtocolUtility.update_protocol_if_2(config=None, mdata=file_md())

    def test_csvpaths_examples_ol_metadata_none_raises(self, config):
        with pytest.raises(ValueError, match="Metadata"):
            ProtocolUtility.update_protocol_if_2(config=config, mdata=None)

    def test_csvpaths_examples_ol_empty_pattern_propagates_valueerror(self, config):
        # _pattern runs before _transform, so this is not swallowed
        config.set(section="openlineage", name="namespace_pattern", value="")
        with pytest.raises(ValueError, match="pattern"):
            ProtocolUtility.update_protocol_if_2(
                config=config, mdata=file_md(), root="/x"
            )

    @pytest.mark.parametrize("empty_root", [None, "", "   "])
    @pytest.mark.parametrize(
        "factory,expected",
        [
            (file_md, "/data/files"),
            (paths_md, "/data/paths"),
            (results_md, "/data/archive"),
        ],
    )
    def test_csvpaths_examples_ol_empty_root_defaults_by_metadata_type(
        self, config, empty_root, factory, expected
    ):
        out = ProtocolUtility.update_protocol_if_2(
            config=config, mdata=factory(), root=empty_root
        )
        assert out == expected

    def test_csvpaths_examples_ol_protocol_stripped_end_to_end(self, config):
        out = ProtocolUtility.update_protocol_if_2(
            config=config, mdata=file_md(), root="s3://bucket/a/b"
        )
        assert out == "bucket/a/b"

    def test_csvpaths_examples_ol_combined_pattern_end_to_end(self, config):
        config.set(section="openlineage", name="namespace_prefix", value="ns")
        config.set(
            section="openlineage",
            name="namespace_pattern",
            value="{prefix}|{root_path_separated}|{root_name}|{entity_name}",
        )
        out = ProtocolUtility.update_protocol_if_2(
            config=config, mdata=file_md("f"), root="s3://bucket/x/y"
        )
        assert out == "ns|bucket.x.y|y|f"

    def test_csvpaths_examples_ol_protocol_root_path_end_to_end_local(
        self, config, tmp_path
    ):
        config.set(
            section="openlineage",
            name="namespace_pattern",
            value="{protocol_root_path}",
        )
        out = ProtocolUtility.update_protocol_if_2(
            config=config, mdata=file_md(), root=str(tmp_path)
        )
        assert out == tmp_path.as_uri()

    def test_csvpaths_examples_ol_protocol_root_path_end_to_end_azure(
        self, config, azure_protocol
    ):
        config.set(
            section="openlineage",
            name="namespace_pattern",
            value="{protocol_root_path}",
        )
        out = ProtocolUtility.update_protocol_if_2(
            config=config, mdata=file_md(), root="azure://c/b"
        )
        assert out == "wasbs://c/b"

    def test_csvpaths_examples_ol_bad_pattern_returns_empty_string_and_logs(self):
        cfg = bare_config(namespace_pattern="{nope}")
        out = ProtocolUtility.update_protocol_if_2(
            config=cfg, mdata=file_md(), root="/a"
        )
        assert out == ""
        cfg.logger.exception.assert_called_once()

    # ----------------------------------------------------------------- _root

    @pytest.mark.parametrize("empty_root", [None, "", "   "])
    @pytest.mark.parametrize(
        "factory,expected",
        [
            (file_md, "/data/files"),
            (paths_md, "/data/paths"),
            (results_md, "/data/archive"),
        ],
    )
    def test_csvpaths_examples_ol_root_defaults(self, empty_root, factory, expected):
        out = ProtocolUtility._root(
            config=bare_config(**DEFAULTS), mdata=factory(), root=empty_root
        )
        assert out == expected

    def test_csvpaths_examples_ol_root_explicit_is_stripped(self):
        out = ProtocolUtility._root(
            config=bare_config(**DEFAULTS), mdata=file_md(), root="  /a/b  "
        )
        assert out == "/a/b"

    def test_csvpaths_examples_ol_root_configured_default_is_stripped(self):
        cfg = bare_config(files="  /padded  ")
        out = ProtocolUtility._root(config=cfg, mdata=file_md(), root=None)
        assert out == "/padded"

    def test_csvpaths_examples_ol_root_explicit_ignores_config(self):
        cfg = bare_config(**DEFAULTS)
        assert ProtocolUtility._root(config=cfg, mdata=file_md(), root="/x") == "/x"
        cfg.get.assert_not_called()

    def test_csvpaths_examples_ol_root_metadata_none_raises(self):
        with pytest.raises(ValueError, match="Metadata"):
            ProtocolUtility._root(config=bare_config(**DEFAULTS), mdata=None, root="/x")

    def test_csvpaths_examples_ol_root_config_none_raises(self):
        with pytest.raises(ValueError, match="Config"):
            ProtocolUtility._root(config=None, mdata=file_md(), root="/x")

    @pytest.mark.parametrize("missing", [None, "", "   "])
    @pytest.mark.parametrize("factory", [file_md, paths_md, results_md])
    def test_csvpaths_examples_ol_root_missing_from_config_raises(
        self, factory, missing
    ):
        # no root passed, and config has nothing usable for this metadata type
        cfg = bare_config(files=missing, csvpaths=missing, archive=missing)
        with pytest.raises(ValueError, match="Root path"):
            ProtocolUtility._root(config=cfg, mdata=factory(), root=None)

    def test_csvpaths_examples_ol_root_key_absent_from_config_raises(self):
        with pytest.raises(ValueError, match="Root path"):
            ProtocolUtility._root(config=bare_config(), mdata=file_md(), root="")

    def test_csvpaths_examples_ol_root_missing_raises_through_public_method(self):
        with pytest.raises(ValueError, match="Root path"):
            ProtocolUtility.update_protocol_if_2(
                config=bare_config(), mdata=file_md(), root=None
            )

    # --------------------------------------------------------------- _pattern

    def test_csvpaths_examples_ol_pattern_configured(self):
        cfg = bare_config(namespace_pattern="{prefix}{root_name}")
        out = ProtocolUtility._pattern(config=cfg, root="/a")
        assert out == "{prefix}{root_name}"

    def test_csvpaths_examples_ol_pattern_not_configured_defaults_to_root(self):
        # documents current behavior: the default is the raw root, protocol included
        out = ProtocolUtility._pattern(config=bare_config(), root="s3://bucket/key")
        assert out == "s3://bucket/key"

    @pytest.mark.parametrize("bad", ["", "None", "   "])
    def test_csvpaths_examples_ol_pattern_empty_raises(self, bad):
        cfg = bare_config(namespace_pattern=bad)
        with pytest.raises(ValueError, match="pattern"):
            ProtocolUtility._pattern(config=cfg, root="/a")

    # ------------------------------------------------------------- _root_path

    @pytest.mark.parametrize(
        "root,expected",
        [
            ("s3://bucket/a/b", "bucket/a/b"),
            ("file:///a/b", "/a/b"),
            ("bucket/a/b", "bucket/a/b"),
            ("/a/b", "/a/b"),
            ("", ""),
            ("a://b://c", "b://c"),  # only the first :// counts
        ],
    )
    def test_csvpaths_examples_ol_root_path(self, root, expected):
        assert ProtocolUtility._root_path(root) == expected

    # ---------------------------------------------------------------- _gather

    def test_csvpaths_examples_ol_gather_all_tokens_with_config(self):
        cfg = bare_config(namespace_prefix="p", path_separator="-")
        t = ProtocolUtility._gather(
            config=cfg, mdata=file_md("f"), root="s3://bucket/a/b"
        )
        assert t == {
            "prefix": "p",
            "root_path": "bucket/a/b",
            "protocol_root_path": "s3://bucket/a/b",
            "root_path_separated": "bucket-a-b",
            "root_name": "b",
            "entity_name": "f",
        }

    def test_csvpaths_examples_ol_gather_defaults_for_prefix_and_separator(self):
        t = ProtocolUtility._gather(
            config=bare_config(), mdata=file_md("f"), root="s3://bucket/a/b"
        )
        assert t["prefix"] == ""
        assert t["root_path_separated"] == "bucket.a.b"

    def test_csvpaths_examples_ol_gather_separates_backslashes(self):
        t = ProtocolUtility._gather(
            config=bare_config(), mdata=file_md(), root="a\\b\\c"
        )
        assert t["root_path_separated"] == "a.b.c"

    # -------------------------------------------------------------- _transform

    def test_csvpaths_examples_ol_transform_formats_tokens(self):
        out = ProtocolUtility._transform(
            config=MagicMock(),
            pattern="{prefix}-{entity_name}",
            tokens={"prefix": "p", "entity_name": "e"},
        )
        assert out == "p-e"

    def test_csvpaths_examples_ol_transform_ignores_unused_tokens(self):
        out = ProtocolUtility._transform(
            config=MagicMock(), pattern="{a}", tokens={"a": "1", "b": "2"}
        )
        assert out == "1"

    def test_csvpaths_examples_ol_transform_none_value_formats_as_string_none(self):
        out = ProtocolUtility._transform(
            config=MagicMock(), pattern="{entity_name}", tokens={"entity_name": None}
        )
        assert out == "None"

    @pytest.mark.parametrize(
        "bad_pattern",
        [
            "{nope}",  # KeyError
            "{",  # ValueError
            "{}",  # IndexError (positional)
            "{0}",  # IndexError
            "{a.nope}",  # AttributeError
        ],
    )
    def test_csvpaths_examples_ol_transform_bad_pattern_returns_empty_and_logs(
        self, bad_pattern
    ):
        cfg = MagicMock()
        out = ProtocolUtility._transform(
            config=cfg, pattern=bad_pattern, tokens={"a": "1"}
        )
        assert out == ""
        cfg.logger.exception.assert_called_once()

    # ----------------------------------------------------------- _entity_name

    def test_csvpaths_examples_ol_entity_name_file(self):
        assert ProtocolUtility._entity_name(file_md("f1")) == "f1"

    def test_csvpaths_examples_ol_entity_name_paths(self):
        assert ProtocolUtility._entity_name(paths_md("p1")) == "p1"

    def test_csvpaths_examples_ol_entity_name_results(self):
        assert ProtocolUtility._entity_name(results_md("r1")) == "r1"

    def test_csvpaths_examples_ol_entity_name_file_reference_resolved(self):
        out = ProtocolUtility._entity_name(file_md("$my.files.x:first"))
        assert out == "my"

    def test_csvpaths_examples_ol_entity_name_paths_reference_resolved(self):
        out = ProtocolUtility._entity_name(paths_md("$my.csvpaths.xyz:from"))
        assert out == "my"

    def test_csvpaths_examples_ol_entity_name_results_not_reference_resolved(self):
        # the results branch does not call _from_root_major_if
        assert ProtocolUtility._entity_name(results_md("$raw")) == "$raw"

    @pytest.mark.parametrize("factory", [file_md, paths_md, results_md])
    def test_csvpaths_examples_ol_entity_name_none_passes_through(self, factory):
        assert ProtocolUtility._entity_name(factory(None)) is None

    # --------------------------------------------------------- _protocol_root

    def test_csvpaths_examples_ol_protocol_root_file_scheme_passthrough(self):
        assert ProtocolUtility._protocol_root("file:///a/b") == "file:///a/b"

    def test_csvpaths_examples_ol_protocol_root_local_absolute(self, tmp_path):
        # On Windows "/a/b" has no drive letter, so pathlib treats it as relative
        # and as_uri() raises. Use a genuinely absolute path on any OS instead.
        assert ProtocolUtility._protocol_root(str(tmp_path)) == tmp_path.as_uri()

    def test_csvpaths_examples_ol_protocol_root_local_relative_falls_back(self):
        # Relative on every OS: Path.as_uri() raises ValueError and the fallback
        # simply prefixes "file://" to the string as given.
        assert ProtocolUtility._protocol_root("rel/path") == "file://rel/path"

    def test_csvpaths_examples_ol_protocol_root_azure_blob(self, azure_protocol):
        assert ProtocolUtility._protocol_root("azure://c/b") == "wasbs://c/b"

    def test_csvpaths_examples_ol_protocol_root_azure_datalake(self, azure_protocol):
        azure_protocol.my_protocol.return_value = "abfss"
        assert ProtocolUtility._protocol_root("azure://c/b") == "abfss://c/b"

    @pytest.mark.parametrize(
        "root", ["s3://bucket/key", "gs://bucket/key", "sftp://host/path"]
    )
    def test_csvpaths_examples_ol_protocol_root_other_passthrough(self, root):
        assert ProtocolUtility._protocol_root(root) == root

    # ------------------------------------------------------ _from_root_major_if

    def test_csvpaths_examples_ol_from_root_major_none(self):
        assert ProtocolUtility._from_root_major_if(None) is None

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_csvpaths_examples_ol_from_root_major_blank_returns_empty_string(
        self, blank
    ):
        assert ProtocolUtility._from_root_major_if(blank) == ""

    def test_csvpaths_examples_ol_from_root_major_plain_name(self):
        assert ProtocolUtility._from_root_major_if("plain") == "plain"

    def test_csvpaths_examples_ol_from_root_major_strips_whitespace(self):
        assert ProtocolUtility._from_root_major_if("  plain  ") == "plain"

    def test_csvpaths_examples_ol_from_root_major_reference(self):
        out = ProtocolUtility._from_root_major_if("$my.csvpaths.named-paths:from")
        assert out == "my"

    def test_csvpaths_examples_ol_from_root_major_reference_with_whitespace(self):
        out = ProtocolUtility._from_root_major_if("  $my.csvpaths.named-paths:from ")
        assert out == "my"
