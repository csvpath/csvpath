"""
    The CsvPath Framework makes it easy to pre-board external data files. It sits between Managed File Transfer and the data lake or applications. CsvPath provides durable dataset identification, validation and canonicalization, and stages data for internal use as a known-good raw data source. The goal is to automate the pre-boarding process.

CsvPath Language is the core validation and canonicalization engine of the Framework. The validation files can be developed without coding using the CLI. When you are ready to automate pre-boarding you will use the classes documented here, in particular csvpath.CsvPath, csvpath.CsvPaths, and the managers in csvpath.managers:

- csvpath.managers.files.file_manager
- csvpath.managers.paths.paths_manager
- csvpath.managers.results.results_manager

You access the managers from a csvpath.CsvPaths instance. You should not construct your own.

There are many other classes you could potentially use in some specific and narrow cases, such as building a new integration, a new function, or a new type of printer. But for 99% of automation use cases these classes are all you need.
"""

from csvpath.csvpath import CsvPath
from csvpath.csvpaths import CsvPaths

__all__ = ["CsvPath", "CsvPaths"]
