import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from interactive_templates.render import render_analysis


def clean_working_tree(path):
    """Remove all files (except .git)"""
    for f in path.glob("**/*"):
        relative = f.relative_to(path)

        if str(relative) == ".git" or str(relative).startswith(".git/"):
            continue

        print(f, relative)

        f.unlink() if f.is_file() else shutil.rmtree(f)


def commit_and_push(working_dir, analysis, force=False):
    force_args = ["--force"] if force else []

    git("add", ".", cwd=working_dir)

    second_codelist = ""
    if analysis.codelist_2:
        second_codelist = f" and codelist {analysis.codelist_2.slug}"
    msg = f"Codelist {analysis.codelist_1.slug}{second_codelist} ({analysis.id})"

    git(
        # -c arguments are instead of having to having to maintain stateful git config
        "-c",
        "user.email=interactive@opensafely.org",
        "-c",
        "user.name=OpenSAFELY Interactive",
        "commit",
        "--author",
        f"{analysis.created_by} <{analysis.created_by}>",
        "-m",
        msg,
        cwd=working_dir,
    )
    ps = git("rev-parse", "HEAD", capture_output=True, cwd=working_dir)
    commit_sha = ps.stdout.strip()

    # this is an super important step, makes it much easier to track commits
    git("tag", analysis.id, *force_args, cwd=working_dir)

    # push to main. Note: we technically wouldn't need this from a pure git
    # pov, as a tag would be enough, but job-runner explicitly checks that
    # a commit is on the branch history, for security reasons
    git("push", "origin", "main", "--force-with-lease", cwd=working_dir)

    # push the tag once we know the main push has succeeded
    git("push", "origin", analysis.id, *force_args, cwd=working_dir)
    return commit_sha


def get_repo_with_token(repo, token):
    scheme, netloc, path, params, query, fragment = urlparse(repo)
    if scheme == "https" and netloc == "github.com":
        new_netloc = f"interactive:{token}@{netloc}"
        return urlunparse((scheme, new_netloc, path, params, query, fragment))

    return repo


def create_commit(
    analysis,
    token,
    force=False,
):
    repo_url = get_repo_with_token(analysis.repo, token=token)

    if not force:
        # check this commit does not already exist
        raise_if_commit_exists(repo_url, analysis.id)

    # 1. create tempdir with AR.pk suffix
    suffix = f"repo-{analysis.id}"
    with tempfile.TemporaryDirectory(suffix=suffix) as repo_dir:
        repo_dir = Path(repo_dir)

        # 2. clone the given interactive repo
        git("clone", "--depth", "1", repo_url, repo_dir, token=token)

        # 3. clear working directory because each analysis is fresh set of files
        clean_working_tree(repo_dir)

        # 4. render the files into the interactive repo
        render_analysis(analysis, repo_dir)

        # 5. write a commit to the given interactive repo
        sha = commit_and_push(repo_dir, analysis)

        # 6. return contents of project.yaml (from disk) and sha
        project_yaml = (repo_dir / "project.yaml").read_text()

    return sha, project_yaml


def git(*args, check=True, text=True, token=None, **kwargs):
    """
    Wrapper around subprocess.run for git commands.

    Changes the defaults: check=True and text=True, and prints the command run
    for logging.
    """
    cmd = ["git"] + [str(arg) for arg in args]

    cwd = kwargs.get("cwd", os.getcwd())
    if token:
        cleaned = [arg.replace(token, "*****") for arg in cmd]
    else:
        cleaned = cmd
    sys.stderr.write(f"{' '.join(cleaned)} (in {cwd})\n")

    # disable reading the user's gitconfig, to give us a more expected environment
    # when developing and testing locally.
    env = {"GIT_CONFIG_GLOBAL": "1"}

    return subprocess.run(cmd, check=check, text=text, env=env, **kwargs)


def raise_if_commit_exists(repo, tag):
    ps = git(
        "ls-remote",
        "--tags",
        repo,
        f"refs/tags/{tag}",
        capture_output=True,
    )
    if ps.stdout != "":
        raise Exception(f"Commit for {tag} already exists in {repo}")
