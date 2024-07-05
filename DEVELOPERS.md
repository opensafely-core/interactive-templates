# Notes for developers

## System requirements

### just

```sh
# macOS
brew install just

# Linux
# Install from https://github.com/casey/just/releases

# Add completion for your shell. E.g. for bash:
source <(just --completions bash)

# Show all available commands
just #  shortcut for just --list
```


## Local development

There are multiple independendant codebases in this repo - multiple templated
interactive analysis code in `interactive_templates/templates`, and the
framework to render these in `interactive_templates/{render.py,schema/}


### Render code

To render the code for an analysis in `./rendered` directory, using test
template context:

```
just render v2
```

You can overide template context with `key=value` cli args:

```
just render v2 codelist_1.slug="org/slug"
```



### Analysis Code

Each directory in `interactive_templates/templates/` contains templated
interactive analysis code, which is designed to be run on an OpenSAFELY
backend.

To work on one of these intractive analyses, `cd` into that directory,
work on the code like it was a normal study, and run `just test` to run tests.
This will run any *unit* tests in this template dir.

e.g.

```
cd interactive_templates/templates/v2
just test
```

From the root directory, running `just test-unit v2` will run the unit tests
for the v2 template dir - omitting the name will run the unit tests for *all*
templated analyses.

These unit tests test specific things within the analysis code. These run in
docker container based on the OpenSAFELY python image, so that they have the
correct dependencies and environment as they would when run as part of an
action.

They have a different set of test dependencies in `requirements.unit.{in,txt}`,
these are installed into the test docker image by default.



### Rendering code

The rendering code uses the default virtualenv manage by the justfile in the usual way for an OpenSAFELY project.

It has a functional test suite, which will render every templated analyses dir
in `interactive_templates/templates` and then execute it with `opensafely run`
to check it works.

To run these tests:

```
just test-functional
```


### Github auto PR Token

The workflow in `.github/workflows/create-job-server-pr.yml` needs a fine
grained PAT as a repository secret in order to work.

Any tech team member can generate a PAT using their account, as the
fine-grained nature means we can restrict it appropriately.

1. Go to https://github.com/settings/tokens?type=beta
1. Generate New Token:
    1. Name: `JOB_SERVER_PR_TOKEN`
    1. Expiry: 90 days
    1. Description: "Token to allow interactive-templates to create job-server PRs"
    1. Resource Owner: opensafely-core
    1. Repository Access: Only Select Respositories, select `job-server`.
    1. Account Permissions:
        1. Contents - Read and Write
        1. Pull Requests - Read and Write
1. Add token value as repository secret `JOB_SERVER_PR_TOKEN`

## Releasing a new version

After merging some changes to `main` that you want to include in a new version:

1. Run `just release` — this updates the [`version`](version) file and
   creates a new branch named after the release date/time.
1. Merge the pull request for that release branch.
1. Ensure the build completes on `main` after merge,
   and a new tag is generated for the release.
1. A successful build should also result in a pull request open on job-server
   via the [`create-job-server-pr.yml`](.github/workflows/create-job-server-pr.yml) workflow.
   Review and merge that pull request for job-server.
