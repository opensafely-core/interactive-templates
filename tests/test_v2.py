from pathlib import Path

# this is not nice, but will do until we can sort jobrunner out
from opensafely._vendor.jobrunner.cli import local_run

import smush


# import pytest


def test_v2(tmp_path):
    form_data = {
        "id": "foo",
        "codelist_1": {
            "label": "Abdominal aortic aneurysm diagnosis codes",
            # "organisation": "NHSD Primary Care Domain Refsets",
            "slug": "nhsd-primary-care-domain-refsets/aaa_cod/20210127",
            "type": "codelist_event",
            "system": "snomed",
            "description": "Codelist 1 Description",
        },
        "codelist_2": {
            "label": "Active and inactive ethnicity codes",
            # "organisation": "NHSD Primary Care Domain Refsets",
            "slug": "nhsd-primary-care-domain-refsets/ethnall_cod/20210127",
            "type": "codelist_medication",
            "system": "snomed",
            "description": "Codelist 2 Description",
        },
        "frequency": "monthly",
        "time_value": "12",
        "time_scale": "months",
        "time_event": "before",
        "filter_population": "adults",
        "demographics": ["age", "sex", "ethnicity"],
    }

    report = smush.InteractiveReportTemplate(
        Path("templates/v2"), ["codelist_1", "codelist_2"]
    )
    report.render(tmp_path, form_data)

    # failing currently
    assert local_run.main(tmp_path, ["run_all"])
