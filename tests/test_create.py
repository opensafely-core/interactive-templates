import pytest

from interactive_templates import create
from interactive_templates.schema import Codelist, v2


def commit_in_remote(*, remote, commit):
    ps = create.git("ls-remote", "--heads", remote, capture_output=True)

    return ps.stdout.startswith(commit)


def tag_in_remote(*, remote, tag):
    ps = create.git("ls-remote", "--tags", remote, tag, capture_output=True)

    return ps.stdout.endswith(f"{tag}\n")


def tag_points_at_sha(*, repo, tag, sha):
    ps = create.git("rev-list", "-1", tag, capture_output=True, cwd=repo)

    return ps.stdout == f"{sha}\n"


def test_clean_working_tree(tmp_path):
    one = tmp_path / "1"
    one.mkdir()
    (one / "1").write_text("")
    (one / "2").write_text("")
    (one / "3").write_text("")

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("")

    (tmp_path / "testing").mkdir()

    create.clean_working_tree(tmp_path)

    assert not (tmp_path / "1" / "1").exists()
    assert not (tmp_path / "1" / "2").exists()
    assert not (tmp_path / "1" / "3").exists()
    assert not (tmp_path / "testing").exists()
    assert (tmp_path / ".git" / "config").exists()


@pytest.mark.parametrize(
    "codelist_2,commit_message",
    [
        (None, "Codelist slug-a"),
        (
            Codelist(label="", slug="slug-b", type=""),
            "Codelist slug-a and codelist slug-b",
        ),
    ],
    ids=["with_codelist_2", "without_codelist_2"],
)
def test_commit_and_push(build_repo, remote_repo, codelist_2, commit_message):
    # create the git repo which would be tied to a workspace
    repo = build_repo()

    # set our remote_repo fixture as the remote "origin"
    create.git("remote", "add", "origin", remote_repo, cwd=repo)

    test_id = "test_id"
    analysis = v2.Analysis(
        codelist_1=Codelist(label="", slug="slug-a", type=""),
        codelist_2=codelist_2,
        demographics=[],
        filter_population="all",
        repo=repo,
        id=test_id,
        time_ever=False,
        time_scale="",
        time_value=1,
    )

    (repo / "first.txt").write_text("testing")
    sha = create.commit_and_push(repo, analysis, "token")

    # assert commit is in pushed remote_repo
    assert commit_in_remote(remote=remote_repo, commit=sha)
    assert tag_in_remote(remote=remote_repo, tag=test_id)

    # assert tag is for new commit
    assert tag_points_at_sha(repo=repo, tag=test_id, sha=sha)

    # commit again with the same analysis to test force tagging
    (repo / "second.txt").write_text("testing")
    sha = create.commit_and_push(repo, analysis, force=True)

    # assert new commit is in remote repo
    assert commit_in_remote(remote=remote_repo, commit=sha)
    assert tag_in_remote(remote=remote_repo, tag=test_id)

    # assert tag has been updated to point to second commit
    assert tag_points_at_sha(repo=repo, tag=test_id, sha=sha)


def test_raise_if_commit_exists(tmp_path):
    create.git("init", ".", "--initial-branch", "main", cwd=tmp_path)

    (tmp_path / "first").write_text("")
    create.git("add", "first", cwd=tmp_path)
    create.git(
        "-c",
        "user.email=testing@opensafely.org",
        "-c",
        "user.name=testing",
        "commit",
        "-m",
        "add first",
        cwd=tmp_path,
    )
    create.git("tag", "exists", cwd=tmp_path)

    with pytest.raises(Exception, match="Commit for exists"):
        create.raise_if_commit_exists(tmp_path, "exists")

    assert create.raise_if_commit_exists(tmp_path, "missing") is None


@pytest.mark.parametrize(
    "force", [(True), (False)], ids=["force_commit", "without_force_commit"]
)
def test_create_commit(remote_repo, add_codelist, force):
    # set our remote_repo fixture as the remote "origin"
    create.git("remote", "add", "origin", remote_repo, cwd=remote_repo)

    add_codelist("org/slug-a", "codelist a")
    add_codelist("org/slug-b", "codelist b")

    test_id = "test_id"

    analysis = v2.Analysis(
        id=test_id,
        repo=str(remote_repo),
        codelist_1=Codelist(label="", slug="org/slug-a", type=""),
        codelist_2=Codelist(label="", slug="org/slug-b", type=""),
        demographics=[],
        filter_population="all",
        time_ever=False,
        time_scale="",
        time_value=1,
    )

    sha, project_yaml = create.create_commit(
        analysis,
        token="token",
        force=force,
    )

    # does the remote repo only have the files we expect from our template?
    ps = create.git(
        "ls-tree",
        "--full-tree",
        "--name-only",
        "-r",  # recurse
        "HEAD",
        cwd=remote_repo,
        capture_output=True,
    )

    files = ps.stdout.strip().split("\n")
    assert "interactive_codelists/codelist_1.csv" in files
    assert "interactive_codelists/codelist_2.csv" in files
    assert "project.yaml" in files

    assert commit_in_remote(remote=remote_repo, commit=sha)


def test_get_repo_with_token_returns_correct_url_with_token():
    repo = "https://github.com/opensafely-test/my-test-repo"
    expected_repo = (
        "https://interactive:a_secure_token@github.com/opensafely-test/my-test-repo"
    )

    assert create.get_repo_with_token(repo, "a_secure_token") == expected_repo


@pytest.mark.parametrize(
    "repo",
    [
        "/tmp/opensafely-test/my-test-repo",
        "https://github.com.someothersite.net/opensafely-test/my-test-repo",
    ],
)
def test_get_repo_with_token_returns_same_url_with_no_token(repo):
    assert create.get_repo_with_token(repo, "a_secure_token") == repo
