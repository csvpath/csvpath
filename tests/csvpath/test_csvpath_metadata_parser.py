import unittest
import pytest
from csvpath import CsvPath
from csvpath.util.metadata_parser import MetadataParser
from csvpath.util.exceptions import InputException


class TestCsvPathMetadataParser(unittest.TestCase):
    def test_metadata_parser1(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        csvpath = """
                ~ Check the file length ~

                $[*][
                    import("top_matter_import")

                    below(total_lines(), 27) ->
                      print.once("File has too few data lines: $.csvpath.total_lines", fail_and_stop())

                ]
        """
        csvpath2 = MetadataParser(path).extract_metadata(instance=path, csvpath=csvpath)
        assert csvpath2.find("~ Check the file length ~") == -1
        assert path.metadata is not None
        assert "original_comment" in path.metadata
        assert path.metadata["original_comment"] == "Check the file length"

    def test_metadata_parser2(self):
        path = CsvPath()
        path.config.add_to_config("errors", "csvpath", "raise")
        csvpath = """
                ~ Check the file length
                    name: hey
                    id: mee
                    description: mo! mo!
                ~

                $[*][ import("top_matter_import") ]
        """
        csvpath2 = MetadataParser(path).extract_metadata(instance=path, csvpath=csvpath)
        assert csvpath2.find("~ Check the file length ~") == -1
        assert path.metadata is not None
        assert "name" in path.metadata
        assert "id" in path.metadata
        assert "description" in path.metadata
        assert path.metadata["description"] == "mo! mo!"
        assert path.identity == "mee"

    def test_metadata_parser_no_comment_leaves_metadata_untouched(self):
        path = CsvPath()
        csvpath = "$[*][ import(\"top_matter_import\") ]"
        csvpath2 = MetadataParser(path).extract_metadata(instance=path, csvpath=csvpath)
        assert csvpath2 == csvpath
        assert path.metadata == {}

    def test_metadata_parser_requires_dollar_or_tilde_start(self):
        with pytest.raises(InputException):
            MetadataParser().collect_metadata({}, "no leading marker here")

    def test_metadata_parser_reuses_existing_metadata_dict(self):
        path = CsvPath()
        path.metadata = {"already": "here"}
        csvpath = "~ name: hey ~\n$[*][ import(\"top_matter_import\") ]"
        MetadataParser(path).extract_metadata(instance=path, csvpath=csvpath)
        assert path.metadata["already"] == "here"
        assert path.metadata["name"] == "hey"

    #
    # extract_csvpath_and_comment()
    #
    def test_extract_csvpath_and_comment_no_comment(self):
        mp = MetadataParser()
        csvpath2, comment = mp.extract_csvpath_and_comment("$[*][ length(#0) ]")
        assert comment == ""
        assert csvpath2 == "$[*][ length(#0) ]"

    def test_extract_csvpath_and_comment_toggles_on_second_tilde(self):
        mp = MetadataParser()
        csvpath2, comment = mp.extract_csvpath_and_comment(
            "~ hello world ~\n$[*][ length(#0) ]"
        )
        assert comment.strip() == "hello world"
        assert "hello world" not in csvpath2
        assert csvpath2.strip() == "$[*][ length(#0) ]"

    def test_extract_csvpath_and_comment_dollar_inside_comment_is_kept(self):
        # a literal $ inside the comment body is comment text, not the
        # start of the csvpath
        mp = MetadataParser()
        csvpath2, comment = mp.extract_csvpath_and_comment(
            "~ price is $5 ~\n$[*][ length(#0) ]"
        )
        assert "$5" in comment
        assert csvpath2.strip() == "$[*][ length(#0) ]"

    def test_extract_csvpath_and_comment_nested_brackets_not_mistaken_for_end(self):
        # state only drops out of "inside" at the last ']' in the string, so
        # a csvpath body containing its own ']' (e.g. an index reference)
        # does not truncate collection early
        mp = MetadataParser()
        csvpath2, comment = mp.extract_csvpath_and_comment(
            "~ note ~\n$[*][ @x = #0[0] ]"
        )
        assert comment.strip() == "note"
        assert csvpath2.strip() == "$[*][ @x = #0[0] ]"

    #
    # _collect_metadata()
    #
    def test_collect_metadata_multiple_fields(self):
        mp = MetadataParser()
        mdata = {}
        mp._collect_metadata(mdata, "a: 1 b: 2")
        assert mdata == {"a": "1", "b": "2"}

    def test_collect_metadata_bare_word_without_colon_is_dropped(self):
        mp = MetadataParser()
        mdata = {}
        mp._collect_metadata(mdata, "lonelyword")
        assert mdata == {}

    def test_collect_metadata_mid_value_punctuation_kept(self):
        mp = MetadataParser()
        mdata = {}
        mp._collect_metadata(mdata, "name: a|b")
        assert mdata == {"name": "a|b"}

    def test_collect_metadata_leading_punctuation_value_lost(self):
        # documenting a known limitation (see the commented-out FlightPath
        # fix in metadata_parser.py): a value that is pure punctuation with
        # no alphanumeric character never gets metafield initialized, so it
        # is silently dropped -- the key ends up mapped to None.
        mp = MetadataParser()
        mdata = {}
        mp._collect_metadata(mdata, "delimited:|")
        assert mdata == {"delimited": None}
