import shutil
from importlib.resources import files
from pathlib import Path

import requests
from attrs import asdict
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from interactive_templates.schema import Codelist


SESSION = requests.Session()
CODELIST_URL = "https://www.opencodelists.org/codelist/{}/download.csv?fixed-headers=1"
EXCLUDES = ["__pycache__", "metadata"]
TEMPLATE_ROOT = files("interactive_templates") / "templates"
ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATE_ROOT)),
    undefined=StrictUndefined,
)


def render_analysis(schema, output_dir):
    """Render the analysis code for name into output_dir using schema as context."""
    template_dir = TEMPLATE_ROOT / schema.analysis_name

    if not template_dir.is_dir():
        raise Exception(
            f"{schema.analysis_name} template dir not found in {TEMPLATE_ROOT}"
        )

    # are there any codelists that need downloading?
    codelists = [(k, v) for k, v in vars(schema).items() if isinstance(v, Codelist)]
    for key, codelist in codelists:
        codelist.path = write_codelist(key, codelist, output_dir)

    # recursively render/copy files into output_dir
    _render_to(
        output_dir,
        context=asdict(schema),
        current_dir=template_dir,
    )


def write_codelist(key, codelist, output_dir):
    """Download the specified codelist to a path within the output_dir."""
    path = output_dir / "codelists" / f"{key}.csv"

    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

    url = CODELIST_URL.format(codelist.slug)
    resp = SESSION.get(url)
    resp.raise_for_status()

    path.write_text(resp.text)
    return path.relative_to(output_dir)


def _render_to(output_dir, context, current_dir):
    """Recursively walk the src tree, and copy/render files across to the output_dir."""

    for src in current_dir.iterdir():
        if src.name in EXCLUDES or src.name.startswith("."):
            continue

        if src.is_dir():
            output_subdir = output_dir / src.name
            _render_to(output_subdir, context, src)
        else:
            dst = output_dir / src.name
            if not dst.parent.exists():
                dst.parent.mkdir()

            if src.suffix in [".tmpl", ".j2"]:
                dst = output_dir / src.stem
                relative_template_path = src.relative_to(TEMPLATE_ROOT)
                template = ENVIRONMENT.get_template(str(relative_template_path))
                content = template.render(**context)
                dst.write_text(content)
            else:
                shutil.copyfile(src, dst)


if __name__ == "__main__":
    import argparse
    import importlib

    parser = argparse.ArgumentParser("render")
    parser.add_argument(
        "--output-dir",
        default="rendered",
        help="directory to render analysis code",
        type=Path,
    )
    parser.add_argument("name", help="name of analysis to render")
    parser.add_argument(
        "context",
        nargs=argparse.REMAINDER,
        help="template context args [name=value...]",
    )

    args = parser.parse_args()
    module = importlib.import_module(f"interactive_templates.schema.{args.name}")

    def set_value(d, name, value):
        """Set dotted values in a nested dictlike object."""
        if "." not in name:
            d[name] = value
        else:
            key, rest = name.split(".", 2)
            set_value(d[key], rest, value)

    kwargs = module.TEST_DEFAULTS.copy()
    for c in args.context:
        name, value = c.split("=", 2)
        set_value(kwargs, name, value)

    schema = module.Analysis(**kwargs)

    shutil.rmtree(args.output_dir)
    render_analysis(schema, args.output_dir)
