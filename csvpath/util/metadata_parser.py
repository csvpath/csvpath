from typing import Tuple
from .config_exception import ConfigurationException
from .exceptions import InputException


class MetadataParser:
    def __init__(self, csvpath) -> None:
        if not hasattr(csvpath, "logger"):
            raise ConfigurationException(
                "Log holder cannot be Nothing. You must pass a CsvPaths or CsvPath to MetadataParser."
            )
        self.log_holder = csvpath

    def extract_metadata(self, *, instance, csvpath: str) -> str:
        """extracts metadata from a comment. the comment is removed.
        at this time we're expecting 0 or 1 comments above the csvpath.
        we do not look below or for secondary comments. both would
        cause errors. we are also not looking within the csvpath. that
        is handled by the matcher's parser and we do not collect
        metadata from internal comments at this time. in principle we
        could run the comments the matching parser finds through this
        parser in order to extract metadata fields. not today's problem
        though.
        """
        self.log_holder.logger.debug(
            "Beginning to extract metadata from csvpath: %s", csvpath
        )
        csvpath = csvpath.strip()
        if not csvpath[0] in ["$", "~"]:
            raise InputException(f"Csvpath must start with ~ or $, not {csvpath[0]}")
        csvpath2, comment = self.extract_csvpath_and_comment(csvpath)
        comment = comment.strip()
        # if there are any characters in the comment we should parse. 3 is
        # the minimum metadata, because "x:y", but there could be a number or something.
        if len(comment) > 0:
            self.collect_metadata(instance, comment)
            # keep the original comment for future ref
            if not instance.metadata:
                instance.metadata = {}
            instance.metadata["original_comment"] = comment
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

    def collect_metadata(self, instance, comment) -> None:
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
                if metafield is not None:
                    metafield += c
                current_word = ""
        if metaname:
            metadata_fields[metaname] = (
                metafield.strip() if metafield is not None else None
            )
        # add found metadata to instance. keys will overwrite preexisting.
        if not instance.metadata:
            instance.metadata = {}
        for k, v in metadata_fields.items():
            instance.metadata[k] = v
