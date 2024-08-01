# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = "3.10"

_lr_method = "LALR"

_lr_signature = "pathALL_LINES ANY FILENAME LEFT_BRACKET MINUS NAME NUMBER PLUS RIGHT_BRACKETpath : FILENAME LEFT_BRACKET expression RIGHT_BRACKETexpression : expression PLUS term\n                      | expression MINUS term\n                      | termterm : NUMBER\n        | NUMBER ALL_LINES\n        | ALL_LINES"

_lr_action_items = {
    "FILENAME": (
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
            8,
        ],
        [
            0,
            -1,
        ],
    ),
    "LEFT_BRACKET": (
        [
            2,
        ],
        [
            3,
        ],
    ),
    "NUMBER": (
        [
            3,
            9,
            10,
        ],
        [
            6,
            6,
            6,
        ],
    ),
    "ALL_LINES": (
        [
            3,
            6,
            9,
            10,
        ],
        [
            7,
            11,
            7,
            7,
        ],
    ),
    "RIGHT_BRACKET": (
        [
            4,
            5,
            6,
            7,
            11,
            12,
            13,
        ],
        [
            8,
            -4,
            -5,
            -7,
            -6,
            -2,
            -3,
        ],
    ),
    "PLUS": (
        [
            4,
            5,
            6,
            7,
            11,
            12,
            13,
        ],
        [
            9,
            -4,
            -5,
            -7,
            -6,
            -2,
            -3,
        ],
    ),
    "MINUS": (
        [
            4,
            5,
            6,
            7,
            11,
            12,
            13,
        ],
        [
            10,
            -4,
            -5,
            -7,
            -6,
            -2,
            -3,
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
    "path": (
        [
            0,
        ],
        [
            1,
        ],
    ),
    "expression": (
        [
            3,
        ],
        [
            4,
        ],
    ),
    "term": (
        [
            3,
            9,
            10,
        ],
        [
            5,
            12,
            13,
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
    ("S' -> path", "S'", 1, None, None, None),
    (
        "path -> FILENAME LEFT_BRACKET expression RIGHT_BRACKET",
        "path",
        4,
        "p_path",
        "scanner.py",
        95,
    ),
    (
        "expression -> expression PLUS term",
        "expression",
        3,
        "p_expression",
        "scanner.py",
        101,
    ),
    (
        "expression -> expression MINUS term",
        "expression",
        3,
        "p_expression",
        "scanner.py",
        102,
    ),
    ("expression -> term", "expression", 1, "p_expression", "scanner.py", 103),
    ("term -> NUMBER", "term", 1, "p_term", "scanner.py", 114),
    ("term -> NUMBER ALL_LINES", "term", 2, "p_term", "scanner.py", 115),
    ("term -> ALL_LINES", "term", 1, "p_term", "scanner.py", 116),
]
