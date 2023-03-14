# this is not nice, but will do until we can sort jobrunner out
from opensafely._vendor.jobrunner.cli import local_run

from interactive_templates.render import render_analysis
from interactive_templates.schema import Codelist, v2


def test_v2_functional(tmp_path):
    analysis = v2.Analysis(
        id="foo",
        title="AAA and ethnicity codes",
        created_by="user",
        repo="repo",
        codelist_1=Codelist(
            label="Abdominal aortic aneurysm diagnosis codes",
            # organisation="NHSD Primary Care Domain Refsets",
            slug="nhsd-primary-care-domain-refsets/aaa_cod/20210127",
            type="event",
            description="Codelist 1 Description",
        ),
        codelist_2=Codelist(
            label="Active and inactive ethnicity codes",
            # organisation="NHSD Primary Care Domain Refsets",
            slug="nhsd-primary-care-domain-refsets/ethnall_cod/20210127",
            type="medication",
            description="Codelist 2 Description",
        ),
        frequency="monthly",
        time_value="12",
        time_scale="months",
        time_event="before",
        filter_population="adults",
        demographics=["age", "sex", "ethnicity"],
        start_date="2019-09-01",
        end_date="2023-01-01",
    )

    render_analysis(analysis, tmp_path)

    # failing currently
    assert local_run.main(tmp_path, ["run_all"])
    assert (tmp_path / "output/foo/report.html").exists()
