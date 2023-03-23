from attrs import field, validators

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
    demographics: list = field(validator=validators.instance_of(list))
    filter_population: str
    repo: str
    time_scale: str
    time_value: int = field(converter=int)
    id: str | None = None  # noqa: A003
    frequency: str = "monthly"
    time_event: str = "before"
    start_date: str = None
    end_date: str = None
    time_ever: bool = field(converter=bool, default=False)
    week_of_latest_extract: str = None


TEST_DEFAULTS = dict(
    codelist_1=Codelist(
        label="DMARDs",
        slug="opensafely/dmards/2020-06-23",
        type="medication",
    ),
    codelist_2=Codelist(
        label="Care planning medication review simple reference set - NHS Digital",
        slug="opensafely/care-planning-medication-review-simple-reference-set-nhs-digital/61b13c39",
        type="event",
    ),
    created_by="test_user",
    demographics=["age", "ethnicity", "sex", "imd", "region"],
    filter_population="adults",
    repo="https://github.com/test/repo",
    time_scale="weeks",
    time_value="4",
    time_ever=False,
    id="id",
    start_date="2019-01-01",
    end_date="2022-12-31",
    week_of_latest_extract="2023-01-01",
)
