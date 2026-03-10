import unittest
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from csvpath.util.date_util import DateUtility as daut


class TestDateUtility(unittest.TestCase):
    @classmethod
    def set_up(cls):
        daut.OFFSET_DAYS = 0
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0

    @classmethod
    def tearDownClass(cls):
        daut.OFFSET_DAYS = 0
        daut.OFFSET_MONTHS = 0
        daut.OFFSET_YEARS = 0

    # ====================

    def test_date_utility_no_offset_is_close_to_real_now(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        result = daut.now()
        after = datetime.now(timezone.utc)
        assert before <= result <= after

    def test_date_utility_day_offset_negative(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        daut.OFFSET_DAYS = -4
        result = daut.now()
        after = datetime.now(timezone.utc)
        expected_early = before + relativedelta(days=-4)
        expected_late = after + relativedelta(days=-4)
        assert expected_early <= result <= expected_late

    def test_date_utility_day_offset_positive(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        daut.OFFSET_DAYS = 10
        result = daut.now()
        after = datetime.now(timezone.utc)
        expected_early = before + relativedelta(days=10)
        expected_late = after + relativedelta(days=10)
        assert expected_early <= result <= expected_late

    def test_date_utility_month_offset(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        daut.OFFSET_MONTHS = -3
        result = daut.now()
        after = datetime.now(timezone.utc)
        expected_early = before + relativedelta(months=-3)
        expected_late = after + relativedelta(months=-3)
        assert expected_early <= result <= expected_late

    def test_date_utility_year_offset(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        daut.OFFSET_YEARS = -1
        result = daut.now()
        after = datetime.now(timezone.utc)
        expected_early = before + relativedelta(years=-1)
        expected_late = after + relativedelta(years=-1)
        assert expected_early <= result <= expected_late

    def test_date_utility_combined_offsets(self):
        TestDateUtility.set_up()
        before = datetime.now(timezone.utc)
        daut.OFFSET_DAYS = -4
        daut.OFFSET_MONTHS = -2
        daut.OFFSET_YEARS = -1
        result = daut.now()
        after = datetime.now(timezone.utc)
        expected_early = before + relativedelta(days=-4, months=-2, years=-1)
        expected_late = after + relativedelta(days=-4, months=-2, years=-1)
        assert expected_early <= result <= expected_late

    def test_date_utility_offset_does_not_mutate_across_calls(self):
        TestDateUtility.set_up()
        daut.OFFSET_DAYS = -4
        first = daut.now()
        second = daut.now()
        delta = second - first
        assert abs(delta.total_seconds()) < 1
