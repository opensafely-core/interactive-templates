import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def write_csv(df, path, **kwargs):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, **kwargs)


def group_low_values(df, count_column, code_column, threshold):
    """Suppresses low values and groups suppressed values into
    a new row "Other".

    Args:
        df: A measure table of counts by code.
        count_column: The name of the count column in the measure table.
        code_column: The name of the code column in the codelist table.
        threshold: Redaction threshold to use
    Returns:
        A table with redacted counts
    """

    # get sum of any values <= threshold
    suppressed_count = df.loc[df[count_column] <= threshold, count_column].sum()
    suppressed_df = df.loc[df[count_column] > threshold, count_column]

    # if suppressed values >0 ensure total suppressed count > threshold.
    # Also suppress if all values 0
    if (suppressed_count > 0) | (
        (suppressed_count == 0) & (len(suppressed_df) != len(df))
    ):
        # redact counts <= threshold
        df.loc[df[count_column] <= threshold, count_column] = np.nan

        # If all values 0, suppress them
        if suppressed_count == 0:
            df.loc[df[count_column] == 0, :] = np.nan

        else:
            # if suppressed count <= threshold redact further values
            while suppressed_count <= threshold:
                suppressed_count += df[count_column].min()
                df.loc[df[count_column].idxmin(), :] = np.nan

        # drop all rows where count column is null
        df = df.loc[df[count_column].notnull(), :]

        # add suppressed count as "Other" row (if > threshold)
        if suppressed_count > threshold:
            suppressed_count = {code_column: "Other", count_column: suppressed_count}
            df = pd.concat([df, pd.DataFrame([suppressed_count])], ignore_index=True)

    return df


def round_values(x, base=5):
    rounded = x
    if isinstance(x, (int, float)):  # noqa: UP038
        if np.isnan(x):
            rounded = np.nan
        else:
            rounded = int(base * round(x / base))
    return rounded


def create_top_5_code_table(
    df, code_df, code_column, term_column, low_count_threshold, rounding_base, nrows=5
):
    """Creates a table of the top 5 codes recorded with the number of events and % makeup of each code.
    Args:
        df: A measure table.
        code_df: A codelist table.
        code_column: The name of the code column in the codelist table.
        term_column: The name of the term column in the codelist table.
        measure: The measure ID.
        low_count_threshold: Value to use as threshold for disclosure control.
        rounding_base: Base to round to.
        nrows: The number of rows to display.
    Returns:
        A table of the top `nrows` codes.
    """

    event_counts = group_low_values(df, "num", code_column, low_count_threshold)
    event_counts = event_counts.copy()

    event_counts["num"] = event_counts["num"].apply(
        lambda x: round_values(x, rounding_base)
    )

    # calculate % makeup of each code
    total_events = event_counts["num"].sum()

    event_counts["Proportion of codes (%)"] = round(
        (event_counts["num"] / total_events) * 100, 2
    )

    # Gets the human-friendly description of the code for the given row
    # e.g. "Systolic blood pressure".
    code_df = code_df.set_index(code_column).rename(
        columns={term_column: "Description"}
    )

    event_counts = event_counts.set_index(code_column).join(code_df).reset_index()

    event_counts.loc[event_counts[code_column] == "Other", "Description"] = "-"

    event_counts.rename(columns={code_column: "Code"}, inplace=True)

    # sort by proportion of codes
    event_counts = event_counts.sort_values(
        ascending=False, by="Proportion of codes (%)"
    )

    event_counts_with_counts = event_counts.copy()

    event_counts = event_counts.loc[
        :, ["Code", "Description", "Proportion of codes (%)"]
    ]
    # return top n rows
    return event_counts.head(5), event_counts_with_counts


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--codelist-1-path",
        type=str,
        help="Path to codelist for event 1",
    )
    parser.add_argument(
        "--codelist-2-path",
        type=str,
        help="Path to codelist for event 2",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    codelist_1_path = args.codelist_1_path
    codelist_2_path = args.codelist_2_path

    Path(args.output_dir / "for_checking").mkdir(parents=True, exist_ok=True)

    input_df = pd.read_feather(args.output_dir / "input_end.feather")

    use_cols = [col for col in input_df.columns if col.startswith("count")] + [
        "patient_id"
    ]
    input_df = input_df.loc[:, use_cols]
    code_counts = input_df.sum().reset_index()
    code_counts.columns = ["code", "num"]

    code_counts["code"] = code_counts["code"].str.replace("count_", "")

    for codelist_path in [codelist_1_path, codelist_2_path]:
        codelist = pd.read_csv(codelist_path, dtype={"code": str})
        codes = codelist["code"].to_list()
        code_counts_subset = code_counts.loc[code_counts["code"].isin(codes), :]

        top_5_code_table, top_5_code_table_with_counts = create_top_5_code_table(
            df=code_counts_subset,
            code_df=codelist,
            code_column="code",
            term_column="term",
            low_count_threshold=7,
            rounding_base=7,
        )
        codelist_number = codelist_path.split("/")[-1].split(".")[0].split("_")[-1]
        top_5_code_table.to_csv(
            args.output_dir / f"top_5_code_table_{codelist_number}.csv", index=False
        )

        top_5_code_table_with_counts.to_csv(
            args.output_dir
            / f"for_checking/top_5_code_table_with_counts_{codelist_number}.csv",
            index=False,
        )


if __name__ == "__main__":
    main()
