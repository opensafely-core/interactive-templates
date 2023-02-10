import copy
import shutil
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


@dataclass
class InteractiveReportTemplate:  # pragma: no cover
    directory: Path
    codelist_keys: list

    EXCLUDES = ["__pycache__", "metadata"]

    @cached_property
    def environment(self):
        return Environment(loader=FileSystemLoader([str(self.directory), "."]))

    def write_codelist(self, output_dir, key, value):
        path = output_dir / "codelists" / f"{key}.csv"

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        r = requests.get(
            f"https://www.opencodelists.org/codelist/{value}/download.csv?fixed-headers=1"
        )
        path.write_text(r.text)
        return path

    def render_to(self, output_dir, context, src_dir=None):
        if src_dir is None:
            src_dir = self.directory

        for src in src_dir.iterdir():
            if src.name in self.EXCLUDES or src.name.startswith("."):
                continue

            if src.is_dir():
                output_subdir = output_dir / src.name
                self.render_to(output_subdir, context, src)
            else:
                dst = output_dir / src.name
                if not dst.parent.exists():
                    dst.parent.mkdir()

                if src.suffix in [".tmpl", ".j2"]:
                    dst = output_dir / src.stem
                    template = self.environment.get_template(str(src))
                    content = template.render(**context)
                    dst.write_text(content)
                else:
                    shutil.copyfile(src, dst)

    def render(self, output_dir, form_data):
        context = copy.deepcopy(form_data)

        for codelist_key in self.codelist_keys:
            codelist = context[codelist_key]
            assert "value" in codelist
            path = self.write_codelist(output_dir, codelist_key, codelist["value"])

            # add path to context
            codelist["path"] = str(path.relative_to(output_dir))

        self.render_to(output_dir, context)


# for manual testing
if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[2])
    else:
        output_dir = Path("rendered")

    inputs = {
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

    report = InteractiveReportTemplate(Path("reports/v2"), ["codelistA", "codelistB"])
    report.render(output_dir, inputs)
