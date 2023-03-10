from interactive_templates.schema import Codelist, interactive_schema


# the name should match the name of the directory where the templates are stored
@interactive_schema(name="v2")
class Analysis:
    """
    Encapsulate all the data for an analysis to pass between layers

    We expect to need a different object of this sort for each different analysis,
    to capture all the details for a given analysis.
    """

    codelist_1: Codelist
    codelist_2: Codelist | None
    created_by: str
    demographics: str
    filter_population: str
    repo: str
    time_scale: str
    time_value: str
    title: str
    id: str | None = None  # noqa: A003
    frequency: str = "monthly"
    time_event: str = "before"
    start_date: str = None
    end_date: str = None
