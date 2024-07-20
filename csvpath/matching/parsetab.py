# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = "3.10"

_lr_method = "LALR"

_lr_signature = "match_partASSIGNMENT CLOSE_PAREN DATE EQUALS HEADER_SYM LEFT_BRACKET NAME NAME_LINE NUMBER OPEN_PAREN OPERATION QUOTE QUOTED_NAME REGEX RIGHT_BRACKET VAR_SYMmatch_part : LEFT_BRACKET expression RIGHT_BRACKET\n        | LEFT_BRACKET expressions RIGHT_BRACKET\n        expressions : expression\n        | expressions expression\n        expression : function\n        | assignment_or_equality\n        | headerfunction : NAME OPEN_PAREN CLOSE_PAREN\n        | NAME OPEN_PAREN equality CLOSE_PAREN\n        | NAME OPEN_PAREN function CLOSE_PAREN\n        | NAME OPEN_PAREN var_or_header CLOSE_PAREN\n        | NAME OPEN_PAREN term CLOSE_PAREN\n        assignment_or_equality : equality\n        | assignment\n        \n        equality : function op term\n                 | function op function\n                 | function op var_or_header\n                 | var_or_header op function\n                 | var_or_header op term\n                 | var_or_header op var_or_header\n                 | term op var_or_header\n                 | term op term\n                 | term op function\n                 | equality op equality\n                 | equality op term\n                 | equality op function\n        op : EQUALS\n        | OPERATION\n        \n        assignment : var ASSIGNMENT var\n                 | var ASSIGNMENT term\n                 | var ASSIGNMENT function\n                 | var ASSIGNMENT header\n        term : QUOTED_NAME\n        | QUOTE DATE QUOTE\n        | QUOTE NUMBER QUOTE\n        | NUMBER\n        | REGEX\n        var_or_header : header\n        | var\n        var : VAR_SYM NAME\n        | VAR_SYM NAME_LINE\n        header : HEADER_SYM NAME\n        | HEADER_SYM NUMBER\n        | HEADER_SYM NAME_LINE\n        "

_lr_action_items = {
    "LEFT_BRACKET": (
        [
            0,
        ],
        [
            2,
        ],
    ),
    "$end": (
        [
            1,
            20,
            21,
        ],
        [
            0,
            -1,
            -2,
        ],
    ),
    "NAME": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            13,
            14,
            16,
            18,
            19,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            8,
            -3,
            8,
            -5,
            -6,
            -7,
            -13,
            -14,
            30,
            -36,
            -33,
            -37,
            36,
            -4,
            8,
            -27,
            -28,
            8,
            8,
            8,
            8,
            -42,
            -43,
            -44,
            8,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "HEADER_SYM": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            13,
            -3,
            13,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            13,
            -27,
            -28,
            13,
            13,
            13,
            13,
            -42,
            -43,
            -44,
            13,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "QUOTED_NAME": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            16,
            -3,
            16,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            16,
            -27,
            -28,
            16,
            16,
            16,
            16,
            -42,
            -43,
            -44,
            16,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "QUOTE": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            17,
            -3,
            17,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            17,
            -27,
            -28,
            17,
            17,
            17,
            17,
            -42,
            -43,
            -44,
            17,
            61,
            62,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "NUMBER": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            13,
            14,
            16,
            17,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            14,
            -3,
            14,
            -5,
            -6,
            -7,
            -13,
            -14,
            31,
            -36,
            -33,
            35,
            -37,
            -4,
            14,
            -27,
            -28,
            14,
            14,
            14,
            14,
            -42,
            -43,
            -44,
            14,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "REGEX": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            18,
            -3,
            18,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            18,
            -27,
            -28,
            18,
            18,
            18,
            18,
            -42,
            -43,
            -44,
            18,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "VAR_SYM": (
        [
            2,
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            23,
            24,
            25,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            33,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            19,
            -3,
            19,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            19,
            -27,
            -28,
            19,
            19,
            19,
            19,
            -42,
            -43,
            -44,
            19,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "RIGHT_BRACKET": (
        [
            3,
            4,
            5,
            6,
            7,
            9,
            12,
            14,
            16,
            18,
            22,
            30,
            31,
            32,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            57,
            58,
            59,
            60,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            20,
            21,
            -5,
            -6,
            -7,
            -13,
            -14,
            -36,
            -33,
            -37,
            -4,
            -42,
            -43,
            -44,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -29,
            -30,
            -31,
            -32,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "EQUALS": (
        [
            5,
            7,
            9,
            10,
            11,
            14,
            15,
            16,
            18,
            30,
            31,
            32,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            24,
            -38,
            24,
            24,
            24,
            -36,
            -39,
            -33,
            -37,
            -42,
            -43,
            -44,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            24,
            24,
            24,
            24,
            24,
            24,
            24,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "OPERATION": (
        [
            5,
            7,
            9,
            10,
            11,
            14,
            15,
            16,
            18,
            30,
            31,
            32,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            25,
            -38,
            25,
            25,
            25,
            -36,
            -39,
            -33,
            -37,
            -42,
            -43,
            -44,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "OPEN_PAREN": (
        [
            8,
        ],
        [
            26,
        ],
    ),
    "NAME_LINE": (
        [
            13,
            19,
        ],
        [
            32,
            37,
        ],
    ),
    "CLOSE_PAREN": (
        [
            14,
            16,
            18,
            26,
            30,
            31,
            32,
            36,
            37,
            38,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            53,
            54,
            55,
            56,
            61,
            62,
            63,
            64,
            65,
            66,
        ],
        [
            -36,
            -33,
            -37,
            43,
            -42,
            -43,
            -44,
            -40,
            -41,
            -16,
            -15,
            -17,
            -38,
            -39,
            -8,
            63,
            64,
            65,
            66,
            -24,
            -25,
            -26,
            -20,
            -18,
            -19,
            -22,
            -21,
            -23,
            -34,
            -35,
            -9,
            -10,
            -11,
            -12,
        ],
    ),
    "ASSIGNMENT": (
        [
            15,
            36,
            37,
        ],
        [
            33,
            -40,
            -41,
        ],
    ),
    "DATE": (
        [
            17,
        ],
        [
            34,
        ],
    ),
}

_lr_action = {}
for _k, _v in _lr_action_items.items():
    for _x, _y in zip(_v[0], _v[1]):
        if not _x in _lr_action:
            _lr_action[_x] = {}
        _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {
    "match_part": (
        [
            0,
        ],
        [
            1,
        ],
    ),
    "expression": (
        [
            2,
            4,
        ],
        [
            3,
            22,
        ],
    ),
    "expressions": (
        [
            2,
        ],
        [
            4,
        ],
    ),
    "function": (
        [
            2,
            4,
            23,
            26,
            27,
            28,
            29,
            33,
        ],
        [
            5,
            5,
            38,
            45,
            50,
            52,
            56,
            59,
        ],
    ),
    "assignment_or_equality": (
        [
            2,
            4,
        ],
        [
            6,
            6,
        ],
    ),
    "header": (
        [
            2,
            4,
            23,
            26,
            27,
            28,
            29,
            33,
        ],
        [
            7,
            7,
            41,
            41,
            41,
            41,
            41,
            60,
        ],
    ),
    "equality": (
        [
            2,
            4,
            26,
            27,
        ],
        [
            9,
            9,
            44,
            48,
        ],
    ),
    "var_or_header": (
        [
            2,
            4,
            23,
            26,
            27,
            28,
            29,
        ],
        [
            10,
            10,
            40,
            46,
            10,
            51,
            55,
        ],
    ),
    "term": (
        [
            2,
            4,
            23,
            26,
            27,
            28,
            29,
            33,
        ],
        [
            11,
            11,
            39,
            47,
            49,
            53,
            54,
            58,
        ],
    ),
    "assignment": (
        [
            2,
            4,
        ],
        [
            12,
            12,
        ],
    ),
    "var": (
        [
            2,
            4,
            23,
            26,
            27,
            28,
            29,
            33,
        ],
        [
            15,
            15,
            42,
            42,
            42,
            42,
            42,
            57,
        ],
    ),
    "op": (
        [
            5,
            9,
            10,
            11,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
        ],
        [
            23,
            27,
            28,
            29,
            27,
            23,
            28,
            29,
            27,
            29,
            23,
        ],
    ),
}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
    for _x, _y in zip(_v[0], _v[1]):
        if not _x in _lr_goto:
            _lr_goto[_x] = {}
        _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
    ("S' -> match_part", "S'", 1, None, None, None),
    (
        "match_part -> LEFT_BRACKET expression RIGHT_BRACKET",
        "match_part",
        3,
        "p_match_part",
        "matcher.py",
        145,
    ),
    (
        "match_part -> LEFT_BRACKET expressions RIGHT_BRACKET",
        "match_part",
        3,
        "p_match_part",
        "matcher.py",
        146,
    ),
    ("expressions -> expression", "expressions", 1, "p_expressions", "matcher.py", 150),
    (
        "expressions -> expressions expression",
        "expressions",
        2,
        "p_expressions",
        "matcher.py",
        151,
    ),
    ("expression -> function", "expression", 1, "p_expression", "matcher.py", 155),
    (
        "expression -> assignment_or_equality",
        "expression",
        1,
        "p_expression",
        "matcher.py",
        156,
    ),
    ("expression -> header", "expression", 1, "p_expression", "matcher.py", 157),
    (
        "function -> NAME OPEN_PAREN CLOSE_PAREN",
        "function",
        3,
        "p_function",
        "matcher.py",
        164,
    ),
    (
        "function -> NAME OPEN_PAREN equality CLOSE_PAREN",
        "function",
        4,
        "p_function",
        "matcher.py",
        165,
    ),
    (
        "function -> NAME OPEN_PAREN function CLOSE_PAREN",
        "function",
        4,
        "p_function",
        "matcher.py",
        166,
    ),
    (
        "function -> NAME OPEN_PAREN var_or_header CLOSE_PAREN",
        "function",
        4,
        "p_function",
        "matcher.py",
        167,
    ),
    (
        "function -> NAME OPEN_PAREN term CLOSE_PAREN",
        "function",
        4,
        "p_function",
        "matcher.py",
        168,
    ),
    (
        "assignment_or_equality -> equality",
        "assignment_or_equality",
        1,
        "p_assignment_or_equality",
        "matcher.py",
        177,
    ),
    (
        "assignment_or_equality -> assignment",
        "assignment_or_equality",
        1,
        "p_assignment_or_equality",
        "matcher.py",
        178,
    ),
    ("equality -> function op term", "equality", 3, "p_equality", "matcher.py", 184),
    (
        "equality -> function op function",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        185,
    ),
    (
        "equality -> function op var_or_header",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        186,
    ),
    (
        "equality -> var_or_header op function",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        187,
    ),
    (
        "equality -> var_or_header op term",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        188,
    ),
    (
        "equality -> var_or_header op var_or_header",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        189,
    ),
    (
        "equality -> term op var_or_header",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        190,
    ),
    ("equality -> term op term", "equality", 3, "p_equality", "matcher.py", 191),
    ("equality -> term op function", "equality", 3, "p_equality", "matcher.py", 192),
    (
        "equality -> equality op equality",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        193,
    ),
    ("equality -> equality op term", "equality", 3, "p_equality", "matcher.py", 194),
    (
        "equality -> equality op function",
        "equality",
        3,
        "p_equality",
        "matcher.py",
        195,
    ),
    ("op -> EQUALS", "op", 1, "p_op", "matcher.py", 204),
    ("op -> OPERATION", "op", 1, "p_op", "matcher.py", 205),
    (
        "assignment -> var ASSIGNMENT var",
        "assignment",
        3,
        "p_assignment",
        "matcher.py",
        211,
    ),
    (
        "assignment -> var ASSIGNMENT term",
        "assignment",
        3,
        "p_assignment",
        "matcher.py",
        212,
    ),
    (
        "assignment -> var ASSIGNMENT function",
        "assignment",
        3,
        "p_assignment",
        "matcher.py",
        213,
    ),
    (
        "assignment -> var ASSIGNMENT header",
        "assignment",
        3,
        "p_assignment",
        "matcher.py",
        214,
    ),
    ("term -> QUOTED_NAME", "term", 1, "p_term", "matcher.py", 223),
    ("term -> QUOTE DATE QUOTE", "term", 3, "p_term", "matcher.py", 224),
    ("term -> QUOTE NUMBER QUOTE", "term", 3, "p_term", "matcher.py", 225),
    ("term -> NUMBER", "term", 1, "p_term", "matcher.py", 226),
    ("term -> REGEX", "term", 1, "p_term", "matcher.py", 227),
    (
        "var_or_header -> header",
        "var_or_header",
        1,
        "p_var_or_header",
        "matcher.py",
        235,
    ),
    ("var_or_header -> var", "var_or_header", 1, "p_var_or_header", "matcher.py", 236),
    ("var -> VAR_SYM NAME", "var", 2, "p_var", "matcher.py", 241),
    ("var -> VAR_SYM NAME_LINE", "var", 2, "p_var", "matcher.py", 242),
    ("header -> HEADER_SYM NAME", "header", 2, "p_header", "matcher.py", 248),
    ("header -> HEADER_SYM NUMBER", "header", 2, "p_header", "matcher.py", 249),
    ("header -> HEADER_SYM NAME_LINE", "header", 2, "p_header", "matcher.py", 250),
]
