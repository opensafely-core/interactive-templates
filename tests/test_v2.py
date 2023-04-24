# this is not nice, but will do until we can sort jobrunner out
from opensafely._vendor.jobrunner.cli import local_run

from interactive_templates.render import render_analysis
from interactive_templates.schema import v2


def test_v2_functional(tmp_path):
    analysis = v2.Analysis(**v2.TEST_DEFAULTS)

    render_analysis(analysis, tmp_path)

    assert local_run.main(tmp_path, ["run_all"])
    assert (tmp_path / "output/id/report.html").exists()


def test_v2_functional_time_value_zero(tmp_path):
    analysis = v2.Analysis(**v2.TEST_DEFAULTS)
    analysis.time_value = 0

    render_analysis(analysis, tmp_path)

    assert local_run.main(tmp_path, ["run_all"])
    assert (tmp_path / "output/id/report.html").exists()


def test_v2_functional_time_ever(tmp_path):
    kwargs = v2.TEST_DEFAULTS.copy()
    kwargs["time_ever"] = "true"
    kwargs["time_scale"] = None
    kwargs["time_value"] = None
    analysis = v2.Analysis(**kwargs)
    render_analysis(analysis, tmp_path)

    # speed things up by only testing the base study definition
    assert local_run.main(tmp_path, ["generate_study_population_weekly_id"])
    assert (
        tmp_path / f"output/id/input_weekly_{ analysis.week_of_latest_extract }.csv.gz"
    ).exists()
