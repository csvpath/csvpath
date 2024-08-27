class MetadataParser:
    def extract_metadata(self, *, instance, csvpath: str) -> str:
        """extracts metadata from comments. the comments are removed."""

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
            elif c.isalnum():
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
                current_word = ""
        if metaname:
            metadata_fields[metaname] = (
                metafield.strip() if metafield is not None else None
            )

        if len(metadata_fields) > 0:
            instance.metadata = metadata_fields

        return csvpath2
