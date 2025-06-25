import unittest
from csvpath import CsvPath
from csvpath.util.metadata_parser import MetadataParser


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
