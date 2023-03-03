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


def get_data(
    report_title="",
    population="all",
    breakdowns="",
    codelist_1_name="",
    codelist_1_link="",
    codelist_2_name="",
    codelist_2_link="",
    time_value="",
    time_scale="",
    time_event="",
    start_date="",
    end_date="",
    num_practices=0,
    request_id="",
):
    """
    Get data to render the report
    Args:
        report_title (str): title of the report
        population (str): population of the report
        breakdowns (str): comma delimited string of demographic breakdowns
        codelist_1_name (str): name of the first codelist
        codelist_1_link (str): link to the first codelist (OpenCodelists)
        codelist_2_name (str): name of the second codelist
        codelist_2_link (str): link to the second codelist (OpenCodelists)
        time_value (str): time value for the report
        time_scale (str): time scale for the report
        time_event (str): time event for the report
        start_date (str): start date for the report
        end_date (str): end date for the report
        num_practices (int): number of practices in the report
        request_id (str): request id - this dictates the path to the data
    Returns:
        dict containing the data
    """

    breakdowns = breakdowns.split(",")

    codelist_url_root = "https://opencodelists.org/codelist/"
    codelist_1_link = codelist_url_root + codelist_1_link
    codelist_2_link = codelist_url_root + codelist_2_link

    top_5_1_path = f"output/{request_id}/joined/top_5_code_table_1.csv"
    top_5_2_path = f"output/{request_id}/joined/top_5_code_table_2.csv"
    summary_table_path = f"output/{request_id}/event_counts.json"

    top_5_1_data = data_from_csv(top_5_1_path)
    top_5_2_data = data_from_csv(top_5_2_path)
    summary_table_data = data_from_json(summary_table_path)

    figure_paths = {
        "decile": "joined/deciles_chart_practice_rate_deciles.png",
        "population": "plot_measures.png",
        "sex": "plot_measures_sex.png",
        "age": "plot_measures_age.png",
        "imd": "plot_measures_imd.png",
        "region": "plot_measures_region.png",
        "ethnicity": "plot_measures_ethnicity.png",
    }

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
    # open file from root directory
    breakdowns = [breakdowns_options[breakdown] for breakdown in breakdowns]

    # population logic

    if population == "adults":
        population_definition = "all registered patients aged 18 and over"

    elif population == "children":
        population_definition = "all registered patients aged under 18"

    else:
        population_definition = "all registered patients"

    report_data = {
        "title": report_title,
        "population": population_definition,
        "decile": figure_paths["decile"],
        "population_plot": figure_paths["population"],
        "breakdowns": breakdowns,
        "top_5_1_data": top_5_1_data,
        "top_5_2_data": top_5_2_data,
        "summary_table_data": summary_table_data,
        "figures": figure_paths,
        "codelist_1_link": codelist_1_link,
        "codelist_2_link": codelist_2_link,
        "codelist_1_name": codelist_1_name,
        "codelist_2_name": codelist_2_name,
        "start_date": start_date,
        "end_date": end_date,
        "time_value": time_value,
        "time_scale": time_scale,
        "time_event": time_event,
        "num_practices": num_practices,
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
    parser.add_argument("--report-title", type=str, default="Report Title")
    parser.add_argument("--population", type=str, default="all")
    parser.add_argument("--breakdowns", type=str, default="")
    parser.add_argument("--start-date", type=str, default="")
    parser.add_argument("--end-date", type=str, default="")
    parser.add_argument("--codelist-1-name", type=str, default="")
    parser.add_argument("--codelist-2-name", type=str, default="")
    parser.add_argument("--codelist-1-link", type=str, default="")
    parser.add_argument("--codelist-2-link", type=str, default="")
    parser.add_argument("--time-value", type=str, default="")
    parser.add_argument("--time-scale", type=str, default="")
    parser.add_argument("--time-event", type=str, default="")
    parser.add_argument("--num-practices", type=int, default=0)
    parser.add_argument("--request-id", type=str, default="")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    output_dir = f"output/{args.request_id}"

    report_data = get_data(
        report_title=args.report_title,
        population=args.population,
        breakdowns=args.breakdowns,
        codelist_1_name=args.codelist_1_name,
        codelist_1_link=args.codelist_1_link,
        codelist_2_name=args.codelist_2_name,
        codelist_2_link=args.codelist_2_link,
        time_value=args.time_value,
        time_scale=args.time_scale,
        time_event=args.time_event,
        start_date=args.start_date,
        end_date=args.end_date,
        num_practices=args.num_practices,
        request_id=args.request_id,
    )

    html = render_report("analysis/report_template.html", report_data)
    write_html(html, output_dir)
