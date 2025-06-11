class DateCompleter:
    @classmethod
    def get(cls, n: str) -> str:
        if len(n) < 5:
            raise ValueError(
                "Cannot complete a date without at least a year ending in a -"
            )

        dat = ""
        chk = 0
        for c in n:
            #
            # 2025-03-23_13-30-00
            #
            if chk == 0:
                if c != "2":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 2, not {c}"
                    )
            elif chk == 1:
                if c != "0":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0, not {c}"
                    )
            elif chk in [2, 3, 6, 12, 15, 18]:
                if c not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be an integer, not {c}"
                    )
            elif chk in [4, 7, 13, 16] and c != "-":
                raise ValueError(
                    f"Character in position 5 of date string {n} must be a '-', not {c}"
                )
            elif chk == 5:
                if c not in ["0", "1", "2", "3"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 3, not {c}"
                    )
            elif chk == 11:
                if c not in ["0", "1", "2"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 2, not {c}"
                    )
            elif chk in [14, 17]:
                if c not in ["0", "1", "2", "3", "4", "5"]:
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be 0 - 5, not {c}"
                    )
            elif chk == 10:
                if c != "_":
                    raise ValueError(
                        f"Character in position {chk} of date string {n} must be an '_', not {c}"
                    )
            chk += 1
        t = "2025-01-01_00-00-00"
        dat = n
        dat = f"{n}{t[chk:]}"
        return dat
