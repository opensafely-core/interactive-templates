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
            "id=1234",
        ],
        check=True,
    )

    project = tmp_path / "project.yaml"
    assert "output/1234" in project.read_text()
    assert (tmp_path / "config.json").exists()
    assert (tmp_path / "README.md").exists()
