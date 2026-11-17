#
# CSVPATHS reference shapes the estimate is checked against on the corpus
# (validate_orders 3 versions, scan_invoices 2, check_zipcodes 2)
#
VO = "$validate_orders.csvpaths"

SHAPES = [
    f"{VO}.:last()",
    f"{VO}.:all()",
    "$*.csvpaths.:last()",
    "$*.csvpaths.:all()",
    f"{VO}.:last().:from(0)",
    f"{VO}.:last().1",
    "$*.csvpaths.:manifest()",
    "$*.csvpaths.:manifest():last()",
    f"{VO}.:manifest()",
    f"{VO}.:definition()",
    "$*.csvpaths.:definition()",
    f"{VO}.:last():uuid()",
    "$*.csvpaths.:last():named_paths_name()",
    f'{VO}.:having("candy check")',
    "$*.csvpaths.:scripts(:has_value())",
    f"{VO}.:readme()",
    "$:regex(/^v/).csvpaths.:manifest()",
    '$*.csvpaths.:lifecycle("active")',
    f"{VO}.:all():fingerprint()",
    f"{VO}.:manifest():last():uuid()",
    f"{VO}.:first()",
    f"{VO}.:index(1):uuid()",
    "$*.csvpaths.:log()",
]
