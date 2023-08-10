from analysis.top_5 import (
    add_description,
    apply_rounding,
    calculate_proportion,
    create_top_5_code_table,
    group_low_values,
    handle_edge_case_percentages,
    round_values,
)
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames


codes_strategy = st.text(min_size=1, max_size=1).map(str)
count_strategy = st.integers(min_value=0, max_value=100)

df_strategy = data_frames(
    [
        column("code", elements=codes_strategy, unique=True),
        column("num", elements=count_strategy),
    ]
)


class TestGroupLowValues:
    @given(df=df_strategy)
    def test_values_above_threshold(self, df):
        result = group_low_values(df, "num", "code", 5)
        assert (
            result["num"] > 5
        ).all(), "Values below the threshold were not redacted."

    @given(df=df_strategy)
    def test_redacted_rows_grouped_into_other(self, df):
        result = group_low_values(df, "num", "code", 5)
        if (result["code"] == "Other").any():
            assert (
                result.loc[result["code"] == "Other", "num"].sum() >= 5
            ), "'Other' row sum is below threshold."

    @given(df=df_strategy)
    def test_all_zero_values_are_suppressed(self, df):
        if df["num"].sum() == 0:
            result = group_low_values(df, "num", "code", 5)
            assert result.empty, "Zero values were not suppressed."

    @given(df=df_strategy)
    def test_no_redaction_when_all_values_above_threshold(self, df):
        if df["num"].all() > 5:
            result = group_low_values(df, "num", "code", 5)
            assert result.equals(
                df
            ), "Redaction happened when all values were above the threshold."
