from typing import Tuple
from .config_exception import ConfigurationException
from .exceptions import InputException


class MetadataParser:
    def __init__(self, csvpath=None) -> None:
        # we were passing in csvpath to get a logger but we
        # weren't actually using it and it complicates using
        # the parser in new ways.
        ...

    def extract_metadata(self, *, instance, csvpath: str) -> str:
        mdata = instance.metadata
        if mdata is None:
            mdata = {}
            instance.metadata = mdata
        return self.collect_metadata(mdata, csvpath)

    def collect_metadata(self, mdata: dict, csvpath: str) -> str:
        """collects metadata from a comment into the dict passed in. the
        comment is removed. at this time we're expecting 0 or 1 comments
        above the csvpath. we do not look below or for secondary comments.
        we do not collect metadata from internal comments at this time.
        """
        csvpath = csvpath.strip()
        if not csvpath[0] in ["$", "~"]:
            raise InputException(
                f"Csvpath must start with ~ or $, not {csvpath[0]} in {csvpath}"
            )
        csvpath2, comment = self.extract_csvpath_and_comment(csvpath)
        comment = comment.strip()
        # if there are any characters in the comment we should parse. 3 is
        # the minimum metadata, because "x:y", but there could be a number or something.
        if len(comment) > 0:
            self._collect_metadata(mdata, comment)
            mdata["original_comment"] = comment
        return csvpath2

    def extract_csvpath_and_comment(self, csvpath) -> Tuple[str, str]:
        csvpath2 = ""
        comment = ""
        state = 0  # 0 == outside, 1 == outer comment, 2 == inside
        for i, c in enumerate(csvpath):
            if c == "~":
                if state == 0:
                    state = 1
                elif state == 1:
                    state = 0
                elif state == 2:
                    csvpath2 += c
            elif c == "[":
                state = 2
                csvpath2 += c
            elif c == "]":
                t = csvpath[i + 1 :]
                _ = t.find("]")
                if state == 2 and _ == -1:
                    state = 0
                csvpath2 += c
            elif c == "$":
                if state == 0:
                    state = 2
                    csvpath2 += c
                elif state == 1:
                    comment += c
                else:
                    csvpath2 += c
            else:
                if state == 0:
                    pass
                elif state == 1:
                    comment += c
                elif state == 2:
                    csvpath2 += c
        return csvpath2, comment

    def _collect_metadata(self, mdata: dict, comment: str) -> None:
        #
        # pull the metadata out of the comment
        #
        current_word = ""
        metadata_fields = {}
        metaname = None
        metafield = None
        for c in comment:
            if c == ":":
                if metaname is not None:
                    metafield = metafield[0 : len(metafield) - len(current_word)]
                    metadata_fields[metaname] = (
                        metafield.strip() if metafield is not None else None
                    )
                    metaname = None
                    metafield = None
                metaname = current_word.strip()
                current_word = ""
            elif c.isalnum() or c == "-" or c == "_":
                current_word += c
                if metaname is not None:
                    if metafield is None:
                        metafield = c
                    else:
                        metafield += c
            elif c in [" ", "\n", "\r", "\t"]:
                if metaname is not None:
                    if metafield is not None:
                        metafield += c
                current_word = ""
            else:
                """ """
                if metafield is not None:
                    metafield += c
                current_word = ""
                """
                #
                # exp! 29 apr 2025. change made for FlightPath. the
                # change was intended to support delimited:| or quotechar:"
                #
                # it worked for that purpose but played hell with csvpath unit tests.
                # we still need a solution because we need to be able to set the
                # delimiter and quotechar. we could make people write them out: pipe,
                # quote, etc. that wouldn't be terrible. and much less fraught than
                # letting more punctuation into metadata comments.
                #
                print(f"flightpath change to mdata parser. check!")
                if metafield is None:
                    metafield = ""
                metafield += c
                current_word = ""
                """
        if metaname:
            metadata_fields[metaname] = (
                metafield.strip() if metafield is not None else None
            )
        # add found metadata to instance. keys will overwrite preexisting.
        for k, v in metadata_fields.items():
            mdata[k] = v
