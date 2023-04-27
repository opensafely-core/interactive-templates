import json
import shutil
from importlib.resources import files
from pathlib import Path

import requests
from attrs import asdict
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from interactive_templates.schema import Codelist


SESSION = requests.Session()
TEMPLATE_ROOT = files("interactive_templates") / "templates"
CODELIST_URL = "https://www.opencodelists.org/codelist/{}/download.csv?fixed-headers=1"
GITIGNORE_PATTERNS = []
CODELIST_DOWNLOAD_DIR = "interactive_codelists"

# directories or files generated in a template dir during local development
DEV_FILES = [
    CODELIST_DOWNLOAD_DIR,
    "output",
    "metadata",
    "project.yaml",
]

# these fildirectory shouldn't be copied from template dirs, as the are developement only
IGNORE_DIRS = ["tests"] + DEV_FILES

ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATE_ROOT)),
    undefined=StrictUndefined,
)


def render_analysis(schema, output_dir):
    """Render the analysis code for named templates into output_dir using schema as context."""
    template_dir = TEMPLATE_ROOT / schema.analysis_name
    if not template_dir.is_dir():
        raise Exception(
            f"{schema.analysis_name} template dir not found in {TEMPLATE_ROOT}"
        )

    print(
        f"Rendering {schema.analysis_name} templates from {template_dir} into {output_dir}"
    )
    _render(
        schema=schema,
        template_dir=template_dir,
        output_dir=output_dir,
    )

    readme = output_dir / "README.md"
    # this allows actions to template their own readme if needed
    if not readme.exists():
        _, _, repo_name = schema.repo.rpartition("/")
        readme_template = ENVIRONMENT.get_template("README.md.tmpl")
        readme.write_text(readme_template.render(repo=repo_name))


def render_analysis_development(schema, directory):
    """Render the analysis code locally in the same directory."""
    print(
        f"DEV: rendering {schema.analysis_name} templates from {directory} into {directory}"
    )
    _render(
        schema=schema,
        template_dir=directory,
        output_dir=directory,
        dev_mode=True,
    )


def _render(schema, template_dir, output_dir, dev_mode=False):
    # write any codelists
    write_codelists(schema, output_dir)

    config = output_dir / "config.json"
    config.write_text(json.dumps(asdict(schema), indent=2))

    context = asdict(schema)

    # recursively render/copy files into output_dir
    _render_to(
        output_dir,
        context=context,
        current_dir=template_dir,
        dev_mode=dev_mode,
    )

    return context


def write_codelists(schema, output_dir):
    """Download the specified codelists to the correct path within the output_dir."""
    codelists = [(k, v) for k, v in vars(schema).items() if isinstance(v, Codelist)]
    for key, codelist in codelists:
        path = output_dir / CODELIST_DOWNLOAD_DIR / f"{key}.csv"

        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        url = CODELIST_URL.format(codelist.slug)
        resp = SESSION.get(url)
        resp.raise_for_status()

        path.write_text(resp.text)
        codelist.path = str(path.relative_to(output_dir))


def _render_to(output_dir, context, current_dir, dev_mode=False):
    """Recursively walk the src tree, and copy/render files across to the output_dir."""

    for src in current_dir.iterdir():
        # skip files we don't want
        if src.name.startswith(".") or src.name in IGNORE_DIRS:
            continue

        if src.is_dir():
            output_subdir = output_dir / src.name
            _render_to(output_subdir, context, src, dev_mode=dev_mode)
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
            elif not dev_mode:  # do not copy in dev mode
                shutil.copyfile(src, dst)


def main():
    import argparse
    import importlib

    parser = argparse.ArgumentParser("render")
    parser.add_argument(
        "--output-dir",
        help="directory to render analysis code",
        default="rendered",
        type=Path,
    )
    parser.add_argument(
        "analysis", help="name of analysis (or path to directory for local development)"
    )
    parser.add_argument(
        "context",
        nargs=argparse.REMAINDER,
        help="template context args [name=value...]",
    )

    args = parser.parse_args()

    # have we been give a path or a name?
    analysis_path = Path(args.analysis)
    if analysis_path.exists():
        analysis_name = analysis_path.name
        dev_mode = True
    else:
        analysis_name = args.analysis
        dev_mode = False

    module = importlib.import_module(f"interactive_templates.schema.{analysis_name}")

    def set_value(d, name, value):
        """Set dotted values in a nested dictlike object."""
        if "." not in name:
            if "," in value:
                d[name] = value.split(",")
            elif value.lower() == "none":
                d[name] = None
            else:
                d[name] = value
        else:
            key, rest = name.split(".", 2)
            set_value(d[key], rest, value)

    kwargs = module.TEST_DEFAULTS.copy()
    for c in args.context:
        name, value = c.split("=", 2)
        set_value(kwargs, name, value)

    # TODO: smell: this requires the class to be called Analysis
    schema = module.Analysis(**kwargs)

    if dev_mode:
        render_analysis_development(schema, analysis_path)
    else:
        if args.output_dir.exists():
            shutil.rmtree(args.output_dir)
            args.output_dir.mkdir()
        render_analysis(schema, args.output_dir)


if __name__ == "__main__":
    main()
