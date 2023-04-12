import pandas as pd
from analysis.event_counts import get_summary_stats, round_to_nearest
from hypothesis import given
from hypothesis import strategies as st


@given(
    st.integers(max_value=100_000_000, min_value=0), st.integers(min_value=1)
)  # Generate random integers for x and base (base > 0)
# Possible values for x are clamped. For large numbers (much greater than the max value used here) the test will
# fail due to the limited precision of floating-point arithmetic. The max value here is a reasonable upper bound for
# the values of x we expect to see in practice.
def test_round_to_nearest(x, base):
    result = round_to_nearest(x, base=base)

    # Check if the result is a multiple of base
    assert result % base == 0

    # Check the result is rounded to the nearest value of base and not further away
    assert result - x >= -base / 2
    assert result - x <= base / 2


def test_get_summary_stats():
    data = {
        "patient_id": [1, 1, 2, 3, 4],
        "event_measure": [1, 0, 1, 1, 0],
        "practice": ["A", "A", "B", "C", "C"],
    }
    df = pd.DataFrame(data)
    summary_stats = get_summary_stats(df)

    assert (summary_stats["unique_patients"] == [1, 2, 3, 4]).all()
    assert summary_stats["num_events"] == 3
    assert (summary_stats["unique_practices"] == ["A", "B", "C"]).all()
    assert (summary_stats["patients_with_events"] == [1, 2, 3]).all()
