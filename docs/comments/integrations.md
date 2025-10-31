

# Integration Settings

CsvPath Framework has integrations with many third-party DataOps tools. Examples include:
* Slack
* OpenLineage
* OpenTelemetry
* Databases
* Webhooks
* SQLite files
* SFTP servers

These integrations require:
* Configuration settings
* A trigger to act at certain times

Integration settings look like regular user-defined metadata. Unlike the modes, they do not have a naming pattern that identifies them as an integration setting.

Integration settings apply only to the csvpath they are in. This allows the production environment operator to set a project's `config.ini` to a project default, while allowing csvpath writers to override some settings on a csvpath-by-csvpath basis.

Integration settings will come into effect under conditions specified and documented by the integration developer. For example, the Slack integration sends a message when a CSV or Excel file is invalid if you use the `on-invalid-slack:` field with a webhook URL. It will send a notification to another URL if `on-valid-slack:` is set and the file is evaluated to be valid.

## FlightPath Data

FlightPath Data, the frontend app for CsvPath Framework development and operations, also uses a few special fields.
* `test-data` - Identifies a file that will be used as the input for a test run when the user clicks `Run` or hits `control-r`.
* `test-delimiter` - The delimiter to use with the test data file.
* `test-quotechar` - The quote character to use with the test data file.

These settings are covered in FlightPath's built-in contextual help.



