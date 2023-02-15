from pathlib import Path

# this is not nice, but will do until we can sort jobrunner out
from opensafely._vendor.jobrunner.cli import local_run

import smush


# import pytest


def test_v2(tmp_path):
    form_data = {
        "id": "foo",
        "codelistA": {
            "label": "Abdominal aortic aneurysm diagnosis codes",
            "organisation": "NHSD Primary Care Domain Refsets",
            "value": "nhsd-primary-care-domain-refsets/aaa_cod/20210127",
            "type": "codelist_event",
            "system": "snomed",
        },
        "codelistB": {
            "label": "Active and inactive ethnicity codes",
            "organisation": "NHSD Primary Care Domain Refsets",
            "value": "nhsd-primary-care-domain-refsets/ethnall_cod/20210127",
            "type": "codelist_medication",
            "system": "snomed",
        },
        "frequency": "monthly",
        "timeValue": "12",
        "timeScale": "months",
        "timeEvent": "before",
        "filterPopulation": "adults",
        "demographics": ["age", "sex", "ethnicity"],
    }

    report = smush.InteractiveReportTemplate(
        Path("templates/v2"), ["codelistA", "codelistB"]
    )
    report.render(tmp_path, form_data)

    # failing currently
    assert local_run.main(tmp_path, ["run_all"])
