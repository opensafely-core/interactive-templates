from hypothesis import given
from hypothesis.extra.pandas import column, data_frames, range_indexes
from hypothesis.strategies import composite, integers, just, one_of

from analysis import measures


@composite
def data_frames_st(draw):
    column_a = column("A", elements=one_of(integers(min_value=0), just(10)))
    return draw(data_frames([column_a], index=range_indexes()))


@given(data_frames_st())
def test_round_column(data_frame):
    # The function modifies the data frame in place, so we create a boolean mask before
    # we pass the data frame to the function.
    redact = data_frame["A"] <= 10

    rounded_data_frame = measures.round_column(data_frame, "A")
    redacted = rounded_data_frame["A"] == 0

    assert data_frame is rounded_data_frame  # data frame modified in place
    assert redact.equals(redacted)
    # Rather than reimplement the rounding function, we test that values are multiples
    # of 10.
    assert rounded_data_frame.loc[:, "A"].mod(10).sum() == 0
