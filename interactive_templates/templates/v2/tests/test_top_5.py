import numpy as np
import pandas as pd

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

description_strategy = st.text(min_size=1, max_size=20).map(str)

code_df_strategy = data_frames(
    [
        column("code", elements=codes_strategy, unique=True),
        column("term", elements=description_strategy),
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


class TestRoundValues:
    @given(x=st.floats(allow_nan=True, allow_infinity=False), base=st.integers(1, 10))
    def test_rounding_floats(self, x, base):
        result = round_values(x, base)

        if np.isnan(x):
            assert np.isnan(result), f"Expected NaN but got {result} for input {x}"
        else:
            expected = int(base * round(x / base))
            assert (
                result == expected
            ), f"Expected {expected} but got {result} for input {x}"

    @given(x=st.integers(min_value=0, max_value=100_000_000), base=st.integers(1, 10))
    def test_rounding_integers(self, x, base):
        result = round_values(x, base)
        expected = int(base * round(x / base))
        assert result == expected, f"Expected {expected} but got {result} for input {x}"

    @given(x=st.text())
    def test_non_numeric_input(self, x):
        result = round_values(x)
        assert result == x, f"Expected {x} but got {result} for non-numeric input"


@given(df=df_strategy, rounding_base=st.integers(1, 10))
def test_apply_rounding(df, rounding_base):
    result_df = apply_rounding(df.copy(), rounding_base)

    # All numbers should be rounded to the nearest multiple of rounding_base
    for num in result_df["num"]:
        assert num % rounding_base == 0, f"{num} not rounded to nearest {rounding_base}"


@given(df=df_strategy)
def test_calculate_proportion(df):
    result_df = calculate_proportion(df.copy())

    total = result_df["num"].sum()

    if total == 0:
        assert all(
            pd.isna(result_df["Proportion of codes (%)"])
        ), "Proportion should be NaN when total is 0."
    else:
        for _, row in result_df.iterrows():
            expected_proportion = round((row["num"] / total) * 100, 2)
            assert (
                row["Proportion of codes (%)"] == expected_proportion
            ), f"Expected {expected_proportion} but got {row['Proportion of codes (%)']} for count {row['num']}"


@given(event_counts=df_strategy, code_df=code_df_strategy)
def test_add_description(event_counts, code_df):
    result = add_description(event_counts, code_df, "code", "term")

    # Ensure that the Description column exists
    assert "Description" in result.columns

    # Ensure that the 'Description' column is filled correctly
    for _, row in result.iterrows():
        if row["code"] == "Other":
            assert row["Description"] == "-"
        elif row["code"] in code_df["code"].values:
            assert (
                row["Description"]
                == code_df[code_df["code"] == row["code"]]["term"].iloc[0]
            )
        else:
            assert row["Description"] == "-"

    # Ensure that no rows were lost
    assert len(result) == len(event_counts)


@given(df=df_strategy)
def test_handle_edge_case_percentages(df):
    df_with_proportions = calculate_proportion(df.copy())
    result_df = handle_edge_case_percentages(df_with_proportions.copy())

    for _, row in result_df.iterrows():
        if (row["Proportion of codes (%)"] == 0) and (row["num"] > 0):
            assert (
                row["Proportion of codes (%)"] == "<0.001"
            ), f"Expected '<0.001' but got {row['Proportion of codes (%)']} for num {row['num']}"

        if (row["Proportion of codes (%)"] == 100) and (row["num"] < df["num"].sum()):
            assert (
                row["Proportion of codes (%)"] == ">99.99"
            ), f"Expected '>99.99' but got {row['Proportion of codes (%)']} for num {row['num']}"
