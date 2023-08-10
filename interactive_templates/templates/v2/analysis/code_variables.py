from cohortextractor import codelist, patients


def generate_code_variables(
    code_list_1, codelist_1_type, code_list_2, codelist_2_type, start_date, end_date
):
    def make_variable(code, codelist_type, start_date, end_date):
        if codelist_type == "event":
            return {
                f"count_{code}": (
                    patients.with_these_clinical_events(
                        codelist([code], system="snomed"),
                        between=[start_date, end_date],
                        returning="number_of_matches_in_period",
                        return_expectations={
                            "incidence": 0.1,
                            "int": {"distribution": "normal", "mean": 3, "stddev": 1},
                        },
                    )
                )
            }
        elif codelist_type == "medication":
            return {
                f"count_{code}": (
                    patients.with_these_medications(
                        codelist([code], system="snomed"),
                        between=[start_date, end_date],
                        returning="number_of_matches_in_period",
                        return_expectations={
                            "incidence": 0.1,
                            "int": {"distribution": "normal", "mean": 3, "stddev": 1},
                        },
                    )
                )
            }

    variables = {}
    for code in code_list_1:
        variables.update(make_variable(code, codelist_1_type, start_date, end_date))

    for code in code_list_2:
        variables.update(make_variable(code, codelist_2_type, start_date, end_date))
    return variables
