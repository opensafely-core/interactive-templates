import argparse
import csv
import json

from jinja2 import Template


def data_from_csv(path):
    """
    Read data from a csv file
    Args:
        path: path to the csv file
    Reuturns:
        list of lists (rows) containing the data
    """
    with open(path, "r") as f:
        reader = csv.reader(f)
        return [row for row in reader]


def data_from_json(path):
    """
    Read data from a json file
    Args:
        path: path to the json file
    Reuturns:
        dict containing the data
    """
    with open(path, "r") as f:
        return json.load(f)


def get_data(report_title, report_description, population, breakdowns):
    """
    Get data to render the report
    Args:
        report_title (str): title of the report
        report_description (str): description of the report
        population (str): population of the report
        breakdowns (str): comma delimited string of demographic breakdowns
    Returns:
        dict containing the data
    """

    breakdowns = breakdowns.split(",")

    top_5_1_path = "output/foo/joined/top_5_code_table_1.csv"
    top_5_2_path = "output/foo/joined/top_5_code_table_2.csv"
    summary_table_path = "output/foo/event_counts.json"
    figure_paths = {
        "decile": "joined/deciles_chart_practice_rate_deciles.png",
        "population": "plot_measures.png",
        "sex": "plot_measures_sex.png",
        "age": "plot_measures_age.png",
        "imd": "plot_measures_imd.png",
        "region": "plot_measures_region.png",
        "ethnicity": "plot_measures_ethnicity.png",
    }

    top_5_1_data = data_from_csv(top_5_1_path)
    top_5_2_data = data_from_csv(top_5_2_path)
    summary_table_data = data_from_json(summary_table_path)

    breakdowns_options = {
        "age": {
            "title": "Age",
            "description": "Age breakdown",
            "figure": figure_paths["age"],
        },
        "ethnicity": {
            "title": "Ethnicity",
            "description": "Ethnicity breakdown",
            "figure": figure_paths["ethnicity"],
        },
        "sex": {
            "title": "Sex",
            "description": "Sex breakdown",
            "figure": figure_paths["sex"],
        },
        "imd": {
            "title": "Index of Multiple Deprivation",
            "description": "Index of Multiple Deprivation breakdown",
            "figure": figure_paths["imd"],
        },
        "region": {
            "title": "Region",
            "description": "Region breakdown",
            "figure": figure_paths["region"],
        },
    }
    # open file from roort directory
    breakdowns = [breakdowns_options[breakdown] for breakdown in breakdowns]

    report_data = {
        "title": report_title,
        "description": report_description,
        "population": population,
        "decile": figure_paths["decile"],
        "population_plot": figure_paths["population"],
        "breakdowns": breakdowns,
        "top_5_1_data": top_5_1_data,
        "top_5_2_data": top_5_2_data,
        "summary_table_data": summary_table_data,
        "figures": figure_paths,
    }
    return report_data


def render_report(report_path, data):
    """
    Render the report template with data
    Args:
        report_path: path to the report template
        data: data to render

    """
    with open(report_path, "r") as f:
        template = Template(f.read())
        return template.render(data)


def write_html(html, output_dir):
    """
    Write the html to a file in the output directory
    Args:
        html: html to write
        output_dir: directory to write to
    """
    with open(output_dir + "/report.html", "w") as f:
        f.write(html)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, default="output/foo")
    parser.add_argument("--report-title", type=str, default="Report Title")
    parser.add_argument("--report-description", type=str, default="Report Description")
    parser.add_argument("--population", type=str, default="all")
    parser.add_argument("--breakdowns", type=str, default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_dir = args.output_dir
    report_title = args.report_title
    report_description = args.report_description
    population = args.population
    breakdowns = args.breakdowns

    report_data = get_data(report_title, report_description, population, breakdowns)

    html = render_report("analysis/report_template.html", report_data)
    write_html(html, args.output_dir)
