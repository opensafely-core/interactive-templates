import pytest
from analysis.report_utils import calculate_variable_windows_codelist_2


@pytest.mark.parametrize(
    "codelist_1_date_range, codelist_2_comparison_date, codelist_2_period_start, codelist_2_period_end, expected_date_range",
    [
        (
            ["index_date", "last_day_of_month(index_date"],
            "end_date",
            "- 0 days",
            "",
            ["index_date - 0 days", "last_day_of_month(index_date"],
        ),
    ],
)
def test_calculate_variable_windows_codelist_2(
    codelist_1_date_range,
    codelist_2_comparison_date,
    codelist_2_period_start,
    codelist_2_period_end,
    expected_date_range,
):
    assert (
        calculate_variable_windows_codelist_2(
            codelist_1_date_range,
            codelist_2_comparison_date,
            codelist_2_period_start,
            codelist_2_period_end,
        )
        == expected_date_range
    )
