import argparse
from pathlib import Path

import pandas as pd
from analysis.report_utils import calculate_rate, get_date_input_file, match_input_files


def redact_and_round_column(df, col, decimals=-1):
    """Redact values less-than or equal-to 10 and then round values to nearest 10."""
    df[col] = df[col].apply(lambda x: x if x >= 10 else 0)
    # `Series.round` introduces scaling and precision errors, meaning some numbers
    # aren't rounded. This isn't the case for the `round` builtin.
    df[col] = df[col].apply(round, ndigits=decimals)
    return df


def calculate_and_redact_values(df):
    """
    Calculate the values for each group and redact where necessary.

    Args:
        df (pd.DataFrame): The input DataFrame. Should contain columns "event_measure", "population" and "group".

    Returns:
        pd.DataFrame: A DataFrame containing the calculated values.
    """

    df = redact_and_round_column(df, "event_measure", decimals=-1)
    df = redact_and_round_column(df, "population", decimals=-1)
    df.loc[:, "value"] = calculate_rate(df, "event_measure", "population")
    df.loc[
        (df["event_measure"] == 0) | (df["population"] == 0),
        "value",
    ] = "[Redacted]"

    return df


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    measure_df = pd.DataFrame(columns=["date", "event_measure", "population"])

    for file in Path(args.input_dir).iterdir():
        if match_input_files(file.name):
            date = get_date_input_file(file.name)
            file_path = str(file.absolute())
            df = pd.read_feather(file_path)
            df["date"] = date

            total_count = (
                df.groupby(by=["date"])["event_measure"]
                .agg(["sum", "count"])
                .reset_index()
                .rename(columns={"sum": "event_measure", "count": "population"})
            )

            measure_df = pd.concat([measure_df, total_count], ignore_index=True)

    measure_df = measure_df.sort_values(by=["date"])

    measure_df = calculate_and_redact_values(measure_df)

    measure_df.to_csv(args.output_dir / "measure_all_weekly.csv", index=False)


if __name__ == "__main__":
    main()
