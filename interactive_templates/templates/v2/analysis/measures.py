import argparse
from pathlib import Path

import pandas as pd
from analysis.report_utils import get_date_input_file, match_input_files


def round_column(df, col, decimals=-1):
    """Redact values less-than or equal-to 10 and then round values to nearest 10."""
    df[col] = df[col].apply(lambda x: x if x > 10 else 0)
    # `Series.round` introduces scaling and precision errors, meaning some numbers
    # aren't rounded. This isn't the case for the `round` builtin.
    df[col] = df[col].apply(round, ndigits=decimals)
    return df


def filter_data(df, filters):
    """
    Filter a DataFrame based on specified columns and their corresponding filter values.

    Args:
        df (pd.DataFrame): The input DataFrame to be filtered.
        filters (dict): A dictionary where keys are column names and values are lists of
                        the desired values for that column.

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """
    for column, filter_values in filters.items():
        if column in df.columns:
            df = df.loc[df[column].isin(filter_values), :]
    return df


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--breakdowns", type=str, required=True)
    parser.add_argument("--input_dir", type=str, required=True)
    parser.add_argument("--measure", type=str, required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.breakdowns == "":
        breakdowns = [x for x in args.breakdowns.split(",")]
    else:
        breakdowns = []

    breakdowns.extend(["practice", "event_1_code", "event_2_code"])
    data = {"total": []}
    for b in breakdowns:
        data[b] = []

    for file in Path(args.input_dir).iterdir():
        if match_input_files(file.name):
            date = get_date_input_file(file.name)

            filters = {
                "sex": ["M", "F"],
                "age_band": [
                    "18-19",
                    "20-29",
                    "30-39",
                    "40-49",
                    "50-59",
                    "60-69",
                    "70-79",
                    "80+",
                ],
            }

            df = pd.read_csv(file).pipe(filter_data, filters).assign(date=date)

            count = df.loc[:, "event_measure"].sum()
            population = df.loc[:, "event_measure"].count()
            value = (count / population) * 1000
            row_dict = {
                "date": pd.Series([date]),
                "event_measure": pd.Series([count]),
                "population": pd.Series([population]),
                "value": pd.Series([value]),
            }

            # make df from row_dict

            df_row = pd.DataFrame(row_dict)

            data["total"].append(df_row)

            for breakdown in breakdowns:
                counts = df.groupby(by=[breakdown])[["event_measure"]].sum()
                counts["population"] = df.groupby(by=[breakdown])[
                    ["event_measure"]
                ].count()
                counts["value"] = (
                    counts["event_measure"] / counts["population"]
                ) * 1000
                counts = counts.reset_index()
                counts["date"] = date
                data[breakdown].append(counts)

    df = pd.concat(data["total"])
    # sort by date
    df = df.sort_values(by=["date"])
    df = round_column(df, "event_measure", decimals=-1)
    df = round_column(df, "population", decimals=-1)
    df["value"] = df["event_measure"] / df["population"] * 1000
    df.loc[(df["event_measure"] == 0) | (df["population"] == 0), "value"] = "[Redacted]"

    df.to_csv(f"{args.input_dir}/measure_total_rate.csv", index=False)
    for breakdown in breakdowns:
        df = pd.concat(data[breakdown])

        # sort by date
        df = df.sort_values(by=["date"])

        # if practice breakdown, we dont want to redact as we'll be aggregating to deciles
        if breakdown != "practice":
            df = round_column(df, "event_measure", decimals=-1)
            df = round_column(df, "population", decimals=-1)
            df["value"] = df["event_measure"] / df["population"] * 1000
            df.loc[
                (df["event_measure"] == 0) | (df["population"] == 0), "value"
            ] = "[Redacted]"

        else:
            df["value"] = df["event_measure"] / df["population"] * 1000

        df.to_csv(f"{args.input_dir}/measure_{breakdown}_rate.csv", index=False)


if __name__ == "__main__":
    main()
