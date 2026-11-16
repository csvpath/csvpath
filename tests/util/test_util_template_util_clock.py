import unittest
from datetime import datetime, timezone

from csvpath.util.date_util import DateUtility as daut
from csvpath.util.template_util import TemplateUtility as temu


class TestTemplateClockTokensUseDateUtility(unittest.TestCase):
    #
    # issue #437: clock tokens read DateUtility.now(), so they honour the
    # OFFSET_* settings exactly as RunHomeMaker's run-dir timestamp does
    #
    def setUp(self):
        daut.OFFSET_DAYS = 0
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0

    def tearDown(self):
        daut.OFFSET_DAYS = 0
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0

    def test_no_offset_is_the_real_date(self):
        now = datetime.now(timezone.utc)
        t = temu.transform_template(":year/:month")
        assert t == f"{now.year}/{now.month}"

    def test_a_year_offset_moves_the_year(self):
        daut.OFFSET_YEARS = -3
        real_year = datetime.now(timezone.utc).year
        t = temu.transform_template(":year")
        assert t == str(real_year - 3)

    def test_a_month_offset_moves_the_month_name(self):
        daut.OFFSET_MONTHS = -1
        expected = daut.now().strftime("%B")
        real = datetime.now(timezone.utc).strftime("%B")
        t = temu.transform_template(":month_name")
        assert t == expected
        assert t != real

    def test_a_file_template_uses_the_offset(self):
        daut.OFFSET_YEARS = -2
        real_year = datetime.now(timezone.utc).year
        t = temu.transform_file_template(
            file="orders/march.csv", template="orders/:year/:filename"
        )
        assert t == f"orders/{real_year - 2}/march.csv"
