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


## Releasing a new version

After merging some changes to `main` that you want to include in a new version:

1. Run `just release` — this updates the [`version`](version) file and
   creates a new branch named after the release date/time.
1. Merge the pull request for that release branch.
1. Ensure the build completes on `main` after merge,
   and a new tag is generated for the release.
1. The job-server repository has a [workflow](https://github.com/opensafely-core/job-server/actions/workflows/update-interactive-templates.yml)
   to regularly check for a new version of interactive-templates,
   and create a pull request in the job-server repository if there is.
   This runs on a schedule.
   If you need an update sooner, you can run the job-server workflow manually.
1. Review, approve and merge that newly created pull request for job-server.
