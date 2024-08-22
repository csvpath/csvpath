import traceback


class LogUtility:
    def log_brief_trace(self, logger) -> None:
        trace = "".join(traceback.format_stack())
        i = 13
        lines = trace.split("\n")
        while i > 0:
            i = i - 1
            aline = lines[len(lines) - i - 1]
            aline = aline.strip()
            if aline[0:4] != "File":
                continue
            logger.info(f"{aline}")
