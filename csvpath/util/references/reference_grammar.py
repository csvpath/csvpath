from datetime import datetime
from typing import Union, Optional, List, Any
from dataclasses import dataclass

from lark import Lark, Transformer, v_args, Tree, Token
from csvpath.util.references.reference_transformer import ReferenceTransformer


REFERENCE_GRAMMAR = r"""
    ?start: reference

    reference: non_local_reference | local_reference

    non_local_reference: file_reference
                       | results_reference
                       | csvpaths_reference
                       | reference_reference

    local_reference: csvpath_reference
                   | headers_reference
                   | variables_reference
                   | metadata_reference

    file_reference:      "$" root_name  files_type     files_names
    results_reference:   "$" root_name  results_type   results_names
    csvpaths_reference:  "$" root_name  csvpaths_type  csvpaths_names
    reference_reference: "$" root_names reference_type reference_names
    csvpath_reference:   "$."    local_type            local_name_one ("." local_name_two)?
    variables_reference: "$."    local_type            local_name_one ("." local_name_two)?
    metadata_reference:  "$."    local_type            local_name_one ("." local_name_two)?
    headers_reference:   "$."    headers_type          header_name ("." local_name_two)?

    //========================================

    local_type: csvpath_type
              | headers_type
              | variables_type
              | metadata_type

    files_type: ".files."
    csvpaths_type: ".csvpaths."
    results_type: ".results."
    reference_type: ".variables."
    csvpath_type: "csvpath."
    headers_type: "headers."
    variables_type: "variables."
    metadata_type: "metadata."

    //========================================
    //

    files_names: files_fingerprint
               | files_arrival
               | files_arrival files_arrival_ordinal
               | files_arrival files_arrival_range
               | files_arrival files_arrival_range files_arrival_range_ordinal
               | files_arrival files_arrival_range ("." files_arrival_two_arrival) files_arrival_two_arrival_range
               | files_arrival files_arrival_range ("." files_arrival_two_arrival) files_arrival_two_arrival_range files_arrival_two_arrival_range_ordinal

               | files_path
               | files_path files_path_ordinal
               | files_path files_path_range
               | files_path files_path_range files_path_range_ordinal
               | files_path files_path_range
               | files_path files_path_range ("." files_path_range_arrival) files_path_range_arrival_range
               | files_path files_path_range ("." files_path_range_arrival) files_path_range_arrival_range files_path_range_arrival_range_ordinal
               | files_path files_path_range ("." files_path_range_arrival) files_path_range_arrival_ordinal
               | files_path files_path_arrival
               | files_path files_path_arrival files_path_arrival_ordinal
               | files_path files_path_arrival files_path_arrival_range
               | files_path files_path_arrival files_path_arrival_range ("." ":"? files_path_two_arrival) files_path_two_arrival_range
               | files_path files_path_arrival files_path_arrival_range ("." files_path_arrival_range_ordinal)
               | files_path ("." files_path_two_arrival)
               | files_path ("." files_path_two_arrival) files_path_two_arrival_range
               | files_path ("." files_path_two_arrival) files_path_two_arrival_range files_path_two_arrival_range_ordinal
               | files_path ("." files_path_two_arrival) files_path_two_arrival_ordinal

               | files_ordinal
               | files_range
               | files_range files_range_ordinal

    results_names: run_date
                 | run_date ("." run_date_instance)
                 | run_date ("." run_date_instance) run_date_instance_data
                 | run_date ("." run_date_instance) run_date_instance_unmatched

                 | run_date run_date_ordinal
                 | run_date run_date_ordinal ("." run_date_ordinal_instance)
                 | run_date run_date_ordinal ("." run_date_ordinal_instance) run_date_ordinal_instance_data
                 | run_date run_date_ordinal ("." run_date_ordinal_instance) run_date_ordinal_instance_unmatched

                 | run_date run_date_range
                 | run_date run_date_range run_date_range_ordinal
                 | run_date run_date_range run_date_range_ordinal ("." run_date_range_ordinal_instance)
                 | run_date run_date_range run_date_range_ordinal ("." run_date_range_ordinal_instance) run_date_range_ordinal_instance_data
                 | run_date run_date_range run_date_range_ordinal ("." run_date_range_ordinal_instance) run_date_range_ordinal_instance_unmatched
                 | run_date run_date_range ("." run_date_range_date) run_date_range_date_range
                 | run_path

                 | run_path run_path_ordinal
                 | run_path run_path_ordinal ("." run_path_ordinal_instance)
                 | run_path run_path_ordinal ("." run_path_ordinal_instance) run_path_ordinal_instance_data
                 | run_path run_path_ordinal ("." run_path_ordinal_instance) run_path_ordinal_instance_unmatched

                 | run_path run_path_date
                 | run_path run_path_date run_path_date_range
                 | run_path run_path_date run_path_date_range ("." run_path_date_range_date)  run_path_date_range_date_range
                 | run_path run_path_date run_path_date_ordinal
                 | run_path run_path_date run_path_date_ordinal ("." run_path_date_ordinal_instance)
                 | run_path run_path_date run_path_date_ordinal ("." run_path_date_ordinal_instance) run_path_date_ordinal_instance_data
                 | run_path run_path_date run_path_date_ordinal ("." run_path_date_ordinal_instance) run_path_date_ordinal_instance_unmatched

                 | run_path run_path_range
                 | run_path run_path_range run_path_range_ordinal
                 | run_path run_path_range run_path_range_ordinal ("." run_path_range_ordinal_instance)
                 | run_path run_path_range run_path_range_ordinal ("." run_path_range_ordinal_instance) run_path_range_ordinal_instance_data
                 | run_path run_path_range run_path_range_ordinal ("." run_path_range_ordinal_instance) run_path_range_ordinal_instance_unmatched

                 | run_path ("." run_path_instance)
                 | run_path ("." run_path_instance) run_path_instance_data
                 | run_path ("." run_path_instance) run_path_instance_unmatched

                 | results_ordinal
                 | results_ordinal ("." results_ordinal_instance)
                 | results_ordinal ("." results_ordinal_instance) results_ordinal_instance_data
                 | results_ordinal ("." results_ordinal_instance) results_ordinal_instance_unmatched

                 | results_range
                 | results_range results_range_ordinal
                 | results_range results_range_ordinal ("." results_range_ordinal_instance)
                 | results_range results_range_ordinal ("." results_range_ordinal_instance) results_range_ordinal_instance_data
                 | results_range results_range_ordinal ("." results_range_ordinal_instance) results_range_ordinal_instance_unmatched

    // CSVPATHS ALL NAMES
    csvpaths_names: csvpaths_instance_name_one
                  | csvpaths_instance_name_one csvpaths_instance_name_one_range
                  | csvpaths_instance_name_one csvpaths_instance_name_one_range ("." ":"? csvpaths_instance_name_three)
                  | csvpaths_instance_name_one csvpaths_instance_name_one_range ("." ":"? csvpaths_instance_name_three) csvpaths_instance_name_three_range

    csvpaths_instance_name_one_range: range
    csvpaths_instance_name_three_range: range
    csvpaths_instance_name_one: IDENTIFIER | /\d{1,3}/ | ":" /\d{1,3}/
    csvpaths_instance_name_three: IDENTIFIER | /\d{1,3}/ | ":" /\d{1,3}/

    // REFERENCES ALL NAMES
    reference_names: reference_major_name ("." reference_minor_name)?
    reference_major_name: IDENTIFIER
    reference_minor_name: IDENTIFIER

    //========================================
    //
    // run date and run path atoms
    //

    files_arrival: DATETIME
    files_arrival_ordinal: ordinal
    files_arrival_range: no_timebox_range
    files_arrival_range_ordinal: ordinal
    files_arrival_two_arrival: DATETIME
    files_arrival_two_arrival_range: range
    files_arrival_two_arrival_range_ordinal: ordinal
    files_fingerprint: fingerprint
    files_ordinal: ordinal
    files_path: path
    files_path_arrival: point
    files_path_arrival_ordinal: ordinal
    files_path_arrival_range: range
    files_path_arrival_range_ordinal: ordinal
    files_path_two_arrival: DATETIME
    files_path_two_arrival_range: range
    files_path_two_arrival_range_ordinal: ordinal
    files_path_two_arrival_ordinal: ordinal
    files_path_ordinal: ordinal
    files_path_range: range
    files_path_range_arrival: DATETIME
    files_path_range_arrival_ordinal: ordinal
    files_path_range_arrival_range: range
    files_path_range_arrival_range_ordinal: ordinal
    files_path_range_ordinal: ordinal
    files_range: range
    files_range_ordinal: ordinal
    results_ordinal: ordinal
    results_range: range
    results_range_ordinal_instance: IDENTIFIER
    results_range_ordinal_instance_data: ":data"
    results_range_ordinal_instance_unmatched: ":unmatched"
    results_range_ordinal: ordinal
    results_ordinal_instance: IDENTIFIER
    results_ordinal_instance_data: "data"
    results_ordinal_instance_unmatched: ":unmatched"
    run_date: DATETIME
    run_date_instance: IDENTIFIER
    run_date_instance_data: ":data"
    run_date_instance_unmatched: ":unmatched"
    run_date_ordinal: ordinal
    run_date_ordinal_instance: IDENTIFIER
    run_date_ordinal_instance_data: ":data"
    run_date_ordinal_instance_unmatched: ":unmatched"
    run_date_range: no_timebox_range
    run_date_range_date: DATETIME
    run_date_range_date_range: range
    run_date_range_ordinal: ordinal
    run_date_range_ordinal_instance: IDENTIFIER
    run_date_range_ordinal_instance_data: ":data"
    run_date_range_ordinal_instance_unmatched: ":unmatched"
    run_path: path
    run_path_date: point
    run_path_date_ordinal: ordinal
    run_path_date_range: range
    run_path_date_range_date: DATETIME
    run_path_date_range_date_range: range
    run_path_date_ordinal_instance: IDENTIFIER
    run_path_date_ordinal_instance_data: ":data"
    run_path_date_ordinal_instance_unmatched: ":unmatched"
    run_path_range: range
    run_path_range_ordinal: ordinal
    run_path_range_ordinal_instance: IDENTIFIER
    run_path_range_ordinal_instance_data: ":data"
    run_path_range_ordinal_instance_unmatched: ":unmatched"
    run_path_ordinal: ordinal
    run_path_ordinal_instance: IDENTIFIER
    run_path_ordinal_instance_data: ":data"
    run_path_ordinal_instance_unmatched: ":unmatched"
    run_path_instance: IDENTIFIER
    run_path_instance_data: ":data"
    run_path_instance_unmatched: ":unmatched"


    //========================================


    local_name_one: IDENTIFIER
    //local_name_one: header_name
    //              | IDENTIFIER

    local_name_two: IDENTIFIER
    instance_name: IDENTIFIER
    fingerprint: HASH
    //header_name: "'"? IDENTIFIER "'"? | INTEGER
    header_name: HEADER_IDENTIFIER
    //
    //instance_tokens: unmatched
    //               | data
    //
    //tokens: token (token)?
    token: yesterday
          | today
          | last
          | first
          | before
          | after
          | ffrom
          | to
          | all
          | index
          | point
          | data
          | unmatched

    last: ":last"
    first: ":first"

    yesterday: ":yesterday"
    today: ":today"
    before: ":before"
    after: ":after"
    ffrom: ":from"
    to: ":to"
    all: ":all"

    data: ":data"
    unmatched: ":unmatched"
    index: ":" INTEGER
    point: ":" DATETIME

    tofrom: to
          | ffrom

    no_timebox_range: ffrom
                    | to
                    | all
                    | after
                    | before

    range: yesterday
         | today
         | ffrom
         | to
         | all
         | after
         | before

    ordinal: first
           | last
           | index

    // Basic components
    root_names: root_name ("#" root_minor_name)?
    root_name: IDENTIFIER
    root_minor_name: IDENTIFIER
    path: PATH_SEGMENT (("\\" | "/") PATH_SEGMENT?)*

    // Terminals - PATH_SEGMENT now excludes dots to enforce two-dot limit
    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_# \-]*/
    HEADER_IDENTIFIER:  "'"? /[a-zA-Z0-9][a-zA-Z0-9_# \-\|+\? \[\]]*/ "'"?
    PATH_SEGMENT: /[a-zA-Z0-9_\- #]+/

    //HASH: /[abcdef0-9]{64}/
    HASH: /[a-f0-9]{64}/i | /[A-Za-z0-9+\/]{44}/ | /[A-Za-z0-9+\/]{43}=/

    INTEGER: /\d+/
    DATETIME: /\d{4}-/
            | /\d{4}-\d{2}/
            | /\d{4}-\d{2}-/
            | /\d{4}-\d{2}-\d{2}/
            | /\d{4}-\d{2}-\d{2}_/
            | /\d{4}-\d{2}-\d{2}_\d{2}/
            | /\d{4}-\d{2}-\d{2}_\d{2}-/
            | /\d{4}-\d{2}-\d{2}_\d{2}-\d{2}/
            | /\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-/
            | /\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}/

    %import common.WS
    %ignore WS
"""

# =====================================


class QueryParser:
    # ref: "ReferenceParser" disallowed by flake
    def __init__(self, ref):
        self.parser = Lark(REFERENCE_GRAMMAR, parser="earley", debug=True)
        self.ref = ref  # a ReferenceParser

    def parse(self, query: str):
        """Parse a CsvPath query string and return structured representation"""
        if self.ref is None:
            raise RuntimeError("A reference object must be available for parsing")
        result = self.parser.parse(query)
        ReferenceTransformer(self.ref).transform(result)
        return self.ref

    def validate_query(self, query: str) -> bool:
        try:
            self.parse(query)
            return True
        except Exception:
            return False
