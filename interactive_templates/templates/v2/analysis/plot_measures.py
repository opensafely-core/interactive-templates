import argparse
from pathlib import Path

import pandas as pd
import seaborn as sns
from report_utils import deciles_chart, plot_measures


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--breakdowns", action="append", default=[], help="breakdowns to use"
    )
    parser.add_argument("--input-dir", help="input directory", required=True)
    parser.add_argument("--output-dir", help="output directory", required=True)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    sns.set_style("darkgrid")

    df = pd.read_csv(f"{ args.input_dir }/measure_all.csv", parse_dates=["date"])

    # subset of the measures file that is used for plotting in this script
    df = df.loc[~(df["group"].isin(["event_1_code", "event_2_code", "practice"])), :]

    Path(f"{args.output_dir}/for_checking").mkdir(parents=True, exist_ok=True)
    df.to_csv(
        f"{ args.output_dir }/for_checking/plot_measure_for_checking.csv", index=False
    )

    df = df.loc[df["value"] != "[Redacted]", :]
    df["value"] = df["value"].astype(float)

    df_total = df.loc[df["group"] == "total", :]

    if not df_total.empty:
        plot_measures(
            df_total,
            filename=f"{ args.output_dir }/plot_measures",
            column_to_plot="value",
            y_label="Rate per 1000",
            category=None,
        )

    for breakdown in breakdowns:
        df_subset = df.loc[df["group"] == breakdown, :]

        if breakdown == "imd":
            plot_measures(
                df_subset,
                filename=f"{ args.output_dir }/plot_measures_{breakdown}",
                column_to_plot="value",
                y_label="Rate per 1000",
                category="group_value",
                category_order=[
                    "Most deprived",
                    "2",
                    "3",
                    "4",
                    "Least deprived",
                ],
            )

        elif breakdown == "age":
            plot_measures(
                df_subset,
                filename=f"{ args.output_dir }/plot_measures_{breakdown}",
                column_to_plot="value",
                y_label="Rate per 1000",
                category="group_value",
                category_order=[
                    "0-5",
                    "6-10",
                    "11-17",
                    "0-17",
                    "18-29",
                    "30-39",
                    "40-49",
                    "50-59",
                    "60-69",
                    "70-79",
                    "80+",
                ],
            )

        else:
            plot_measures(
                df_subset,
                filename=f"{ args.output_dir }/plot_measures_{breakdown}",
                column_to_plot="value",
                y_label="Rate per 1000",
                category="group_value",
            )

    practice_df = pd.read_csv(
        f"{ args.output_dir }/measure_practice_rate_deciles.csv",
        parse_dates=["date"],
    )
    deciles_chart(
        practice_df,
        f"{ args.output_dir }/deciles_chart.png",
        period_column="date",
        column="value",
        ylabel="rate per 1000",
    )


if __name__ == "__main__":
    main()
