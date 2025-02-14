class Const:

    SPLASH = """
          *** *            ******        **  **
        ***  **   *        **  **      **** **
       **        ** **  * ** *** ***** **  *****
       **    * **** **** ***** *** ** **  ** **
       **   **** ****** **     ** ** *** ** ** **
         ***   **** *  **      *** ** ****   **
***************************
CsvPath Command Line Interface
Try tab completion and menu-by-key.
For help see https://www.csvpath.org
"""

    ITALIC = "\033[3m"
    SIDEBAR_COLOR = "\033[36m"
    REVERT = "\033[0m"
    STOP_HERE = f"{SIDEBAR_COLOR}{ITALIC}... done picking dir{REVERT}"
    STOP_HERE2 = "👍 pick this dir"
    CANCEL = f"{SIDEBAR_COLOR}{ITALIC}... cancel{REVERT}"
    CANCEL2 = "← cancel"
    QUIT = "← quit"
    NAMED_FILES = "register data"
    NAMED_PATHS = "load csvpaths"
    ARCHIVE = "access the archive"
