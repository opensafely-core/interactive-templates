import subprocess
import sys


def test_render_cli(tmp_path):
    subprocess.run(
        [
            sys.executable,
            "-m",
            "interactive_templates.render",
            f"--output-dir={tmp_path}",
            "v2",
            "title=TESTTITLE",
        ],
        check=True,
    )

    project = tmp_path / "project.yaml"
    assert "TESTTITLE" in project.read_text()
