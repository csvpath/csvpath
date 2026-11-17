import json

import pytest

from csvpath.util.json_file_utility import JsonFileUtility as jsut

#
# RC triage A19 part 3 (David, 2026-11-16): a corrupt framework JSON file
# raises a ValueError naming the file and the likely cause, not a bare
# json.JSONDecodeError with neither
#


def _write(tmp_path, text: str) -> str:
    path = tmp_path / "manifest.json"
    path.write_text(text)
    return str(path)


def test_a_valid_file_loads(tmp_path):
    assert jsut.load(path=_write(tmp_path, '[{"uuid": "u1"}]')) == [{"uuid": "u1"}]


def test_an_empty_file_was_probably_interrupted(tmp_path):
    path = _write(tmp_path, "  \n")
    with pytest.raises(ValueError, match="is empty: a write was probably interrupted") as e:
        jsut.load(path=path)
    assert path in str(e.value)
    assert isinstance(e.value.__cause__, json.JSONDecodeError)


def test_two_values_probably_mean_two_writes_landed_on_each_other(tmp_path):
    # the #609 shape: a {} on top of a full manifest
    path = _write(tmp_path, '{}  {"time": "2026-11-14"}')
    with pytest.raises(ValueError, match="holds more than one JSON value"):
        jsut.load(path=path)


def test_a_file_that_stops_mid_entry_was_probably_interrupted(tmp_path):
    path = _write(tmp_path, '[{"uuid": "u1"}, {"uuid": "u2"')
    with pytest.raises(ValueError, match="ends partway through an entry"):
        jsut.load(path=path)


def test_anything_else_may_be_a_hand_edit(tmp_path):
    path = _write(tmp_path, '[{"uuid": "u1",, }]')
    with pytest.raises(ValueError, match="not valid JSON at line 1, column .*edited by hand"):
        jsut.load(path=path)


def test_every_message_says_how_to_recover(tmp_path):
    with pytest.raises(ValueError, match="restore it from a backup"):
        jsut.load(path=_write(tmp_path, "["))


def test_the_error_is_logged(tmp_path, caplog):
    with pytest.raises(ValueError):
        jsut.load(path=_write(tmp_path, "["))
    assert "manifest.json" in caplog.text


@pytest.mark.parametrize("bad", [None, "", "  "])
def test_a_missing_path_raises(bad):
    with pytest.raises(ValueError):
        jsut.load(path=bad)
