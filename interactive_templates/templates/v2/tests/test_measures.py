import pandas as pd
import pytest
from analysis import measures
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames, range_indexes
from hypothesis.strategies import composite, integers, just, one_of


@composite
def data_frames_st(draw):
    column_a = column("A", elements=one_of(integers(min_value=0), just(10)))
    return draw(data_frames([column_a], index=range_indexes()))


@given(data_frames_st())
def test_redact_and_round_column(data_frame):
    # The function modifies the data frame in place, so we create a boolean mask before
    # we pass the data frame to the function.
    redact = data_frame["A"] < 10

    rounded_data_frame = measures.redact_and_round_column(data_frame, "A")
    redacted = rounded_data_frame["A"] == 0

    assert data_frame is rounded_data_frame  # data frame modified in place
    assert redact.equals(redacted)
    # Rather than reimplement the rounding function, we test that values are multiples
    # of 10.
    assert rounded_data_frame.loc[:, "A"].mod(10).sum() == 0


@pytest.fixture
def filter_data_df():
    return pd.DataFrame(
        {
            "A": [1, 2, 3, 4, 5],
            "B": ["a", "b", "c", "d", "e"],
            "C": [10, 20, 30, 40, 50],
        }
    )


def test_filter_data(filter_data_df):
    filters = {
        "A": [1, 3, 5, 6],
        "B": ["a", "d", "a"],
        "C": [10, 20, 50, 10],
    }

    exp = pd.DataFrame(
        {
            "A": [1],
            "B": ["a"],
            "C": [10],
        }
    )

    obs = measures.filter_data(filter_data_df, filters)
    assert exp.equals(obs)


@st.composite
def input_df(draw):
    nrows = 20

    patient_id = column(
        name="patient_id",
        elements=st.integers(min_value=1, max_value=1000),
        unique=True,
    )

    sex = column(name="sex", elements=st.sampled_from(["M", "F"]), unique=False)

    event_measure = column(
        name="event_measure",
        elements=st.integers(min_value=0, max_value=1),
        unique=False,
    )

    population = column(
        name="population", elements=st.integers(min_value=1, max_value=1), unique=False
    )

    imd = column(
        name="imd", elements=st.integers(min_value=1, max_value=5), unique=False
    )

    return draw(
        data_frames(
            [patient_id, event_measure, population, sex, imd],
            index=range_indexes(min_size=nrows, max_size=nrows),
        )
    )


@given(df=input_df())
def test_calculate_total_counts(df):
    date = "2022-01-01"
    df["date"] = date

    obs = measures.calculate_total_counts(df, date, group="total", group_value="total")

    assert obs["group"].eq("total").all()
    assert obs["group_value"].eq("total").all()

    assert len(obs) == 1
    assert obs.columns.tolist() == [
        "date",
        "event_measure",
        "population",
        "group",
        "group_value",
    ]

    # assert date is correct
    assert obs["date"].eq(date).all()

    # assert that the sum of the event_measure and population columns is correct
    assert obs["event_measure"].iloc[0] == df["event_measure"].sum()
    assert obs["population"].iloc[0] == df["population"].sum()


@given(df=input_df())
def test_calculate_group_counts(df):
    date = "2022-01-01"
    df["date"] = date

    obs = measures.calculate_group_counts(df, "sex", date)

    # there can be samples where there is only 1 unique sex value, so we cant simply assert that the shape is (2,5)
    assert len(obs) == obs["group_value"].nunique()

    assert obs.columns.tolist() == [
        "date",
        "event_measure",
        "population",
        "group",
        "group_value",
    ]

    # assert date is correct
    assert obs["date"].eq(date).all()

    # assert that the sum of the event_measure and population columns is correct
    assert (
        obs.loc[obs["group_value"] == "M", "event_measure"].sum()
        == df.loc[df["sex"] == "M", "event_measure"].sum()
    )
    assert (
        obs.loc[obs["group_value"] == "F", "population"].sum()
        == df.loc[df["sex"] == "F", "population"].sum()
    )
    assert obs["population"].sum() == df["population"].sum()


@st.composite
def measure_df_strategy(draw):
    nrows = 20

    group_value = column(
        name="group_value",
        elements=st.integers(min_value=1, max_value=1000),
        unique=True,
    )

    value = column(
        name="value",
        elements=st.one_of(st.floats(min_value=0, max_value=1), st.just("[Redacted]")),
        unique=False,
    )

    return draw(
        data_frames(
            [group_value, value],
            index=range_indexes(min_size=nrows, max_size=nrows),
        )
    )


@given(input_measure_df=measure_df_strategy())
def test_drop_redacted_rows(input_measure_df: pd.DataFrame):
    result_df = measures.drop_redacted_rows(input_measure_df)

    for group_value in result_df["group_value"].unique():
        group_value_df = input_measure_df.loc[
            input_measure_df["group_value"] == group_value, :
        ]
        redacted_count = group_value_df.loc[group_value_df["value"] == "[Redacted]", :][
            "value"
        ].count()
        total_count = group_value_df["value"].count()

        assert (
            redacted_count / total_count <= 0.5
        ), f"Subgroup {group_value} has more than 50% redacted values"
