import subprocess
import venv

import pytest


@pytest.fixture()
def git_archive(tmp_path):
    """Create a git archive of the current working tree as a zip."""
    # create a temporary commit of current tree, including local modifications,
    # but doesn't actually put it on the stash
    commit = subprocess.check_output(["git", "stash", "create"], text=True).strip()
    if not commit:
        # we have no local changes
        commit = "HEAD"

    # make a zip archive from that commit
    archive = tmp_path / "git_archive.zip"
    subprocess.run(["git", "archive", commit, "-o", archive], check=True)
    yield archive

    if commit != "HEAD":
        # clean up the commit cos its the right thing to do
        subprocess.run(["git", "prune", commit], check=True)


def test_packaging_install_from_archive(tmp_path, git_archive):
    venv_path = tmp_path / "venv"
    venv.create(venv_path, clear=True, with_pip=True)

    subprocess.run([venv_path / "bin/pip", "install", git_archive], check=True)

    expected_data_files = [
        "templates/README.md.tmpl",
        "templates/v2/project.yaml.tmpl",
        "templates/v2/codelists/codelists.txt",
        "templates/v2/codelists/opensafely-ethnicity-snomed-0removed.csv",
    ]

    pkg_location = venv_path / "lib/python3.11/site-packages/interactive_templates"
    for path in expected_data_files:
        p = pkg_location / path
        assert p.exists()
