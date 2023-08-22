import datetime

from attrs import field, validators

from interactive_templates import dates, schema


def int_or_none(v):
    "int converter that allows None"
    if v is None:
        return None
    else:
        return int(v)


def date_string(instance, attr, value):
    "validator for YYYY-MM-DD strings"
    try:
        datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{attr} is invalid: {exc}")


# the name should match the name of the directory where the templates are stored
@schema.interactive_schema(name="v2")
class Analysis:
    """
    Encapsulate all the data for an analysis to pass between layers

    We expect to need a different object of this sort for each different analysis,
    to capture all the details for a given analysis.
    """

    # analsysis data
    #
    # mandatory attributres have to come first in the class list
    demographics: list = field(
        validator=validators.deep_iterable(
            member_validator=validators.in_(
                ["age", "sex", "region", "imd", "ethnicity"]
            ),
            iterable_validator=validators.instance_of(list),
        ),
    )

    codelist_1: schema.Codelist = field(
        validator=validators.instance_of(schema.Codelist)
    )
    codelist_2: schema.Codelist | None = field(
        validator=validators.optional(validators.instance_of(schema.Codelist)),
        default=None,
    )

    filter_population: str = field(
        validator=validators.in_(["all", "children", "adults"]),
        default="all",
    )
    time_value: int | None = field(converter=int_or_none, default=None)
    time_scale: str | None = field(
        validator=validators.in_([None, "weeks", "months", "years", ""]),
        default="months",
    )
    time_ever: bool | None = field(converter=bool, default=None)
    time_event: str = field(
        validator=validators.in_(["before"]),
        default="before",
    )
    frequency: str = field(
        validator=validators.in_(["weekly", "monthly"]),
        default="monthly",
    )
    start_date: str = field(validator=date_string, default=dates.START_DATE)
    end_date: str = field(validator=date_string, default=dates.END_DATE)
    week_of_latest_extract: str = field(
        validator=date_string, default=dates.WEEK_OF_LATEST_EXTRACT
    )
    week_of_latest_extract_7w: str = field(
        validator=date_string, default=dates.WEEK_OF_LATEST_EXTRACT_7W
    )

    # request data filled in later
    created_by: str | None = None
    repo: str | None = None
    id: str | None = None  # noqa: A003


TEST_DEFAULTS = dict(
    codelist_1=schema.Codelist(
        label="DMARDs",
        slug="opensafely/dmards/2020-06-23",
        type="medication",
    ),
    codelist_2=schema.Codelist(
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
    time_ever=None,
    id="id",
    start_date=dates.START_DATE,
    end_date=dates.END_DATE,
)
