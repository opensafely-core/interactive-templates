# just has no idiom for setting a default value for an environment variable
# so we shell out, as we need VIRTUAL_ENV in the justfile environment
export VIRTUAL_ENV  := `echo ${VIRTUAL_ENV:-.venv}`

export BIN := VIRTUAL_ENV + if os_family() == "unix" { "/bin" } else { "/Scripts" }
export PIP := BIN + if os_family() == "unix" { "/python -m pip" } else { "/python.exe -m pip" }

export DEFAULT_PYTHON := if os_family() == "unix" { "python3.11" } else { "python" }

export DOCKER_BUILDKIT := "1"
export COMPOSE_DOCKER_CLI_BUILD := "1"

export UID := `id -u`
export GID := `id -g`


# list available commands
default:
    @"{{ just_executable() }}" --list

# clean up development files
clean:
    rm -rf .venv
    # remove any local dev files
    rm -rf $(grep 'interactive_templates/templates/*' .gitignore)

# ensure valid virtualenv
virtualenv:
    #!/usr/bin/env bash
    # allow users to specify python version in .env
    PYTHON_VERSION=${PYTHON_VERSION:-$DEFAULT_PYTHON}

    # create venv and upgrade pip
    test -d $VIRTUAL_ENV || { $PYTHON_VERSION -m venv $VIRTUAL_ENV && $PIP install --upgrade pip; }

    # ensure we have pip-tools so we can run pip-compile
    test -e $BIN/pip-compile || $PIP install pip-tools


_compile src dst *args: virtualenv
    #!/usr/bin/env bash
    set -eu
    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o {{ src }} -nt {{ dst }} || exit 0
    $BIN/pip-compile --allow-unsafe --generate-hashes --output-file={{ dst }} {{ src }} {{ args }}


# update requirements.prod.txt if requirements.prod.in has changed
requirements-prod *args:
    "{{ just_executable() }}" _compile pyproject.toml requirements.prod.txt {{ args }}


# update requirements.dev.txt if requirements.dev.in has changed
requirements-dev *args: requirements-prod
    "{{ just_executable() }}" _compile requirements.dev.in requirements.dev.txt {{ args }}

# update requirments for analysis unit tests
requirements-unit *args:
    #!/usr/bin/env bash
    # exit if src file is older than dst file (-nt = 'newer than', but we negate with || to avoid error exit code)
    test "${FORCE:-}" = "true" -o requirements.unit.in -nt requirements.unit.txt || exit 0
    docker compose run unit-tests pip-compile requirements.unit.in {{ args }}


# ensure prod requirements installed and up to date
prodenv: requirements-prod
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.prod.txt -nt $VIRTUAL_ENV/.prod || exit 0

    $PIP install -r requirements.prod.txt
    touch $VIRTUAL_ENV/.prod

# && dependencies are run after the recipe has run. Needs just>=0.9.9. This is
# a killer feature over Makefiles.
#
# ensure dev requirements installed and up to date
devenv: prodenv requirements-dev && install-precommit
    #!/usr/bin/env bash
    # exit if .txt file has not changed since we installed them (-nt == "newer than', but we negate with || to avoid error exit code)
    test requirements.dev.txt -nt $VIRTUAL_ENV/.dev || exit 0

    $PIP install -r requirements.dev.txt
    touch $VIRTUAL_ENV/.dev


# ensure precommit is installed
install-precommit:
    #!/usr/bin/env bash
    BASE_DIR=$(git rev-parse --show-toplevel)
    test -f $BASE_DIR/.git/hooks/pre-commit || $BIN/pre-commit install


# upgrade dev or prod dependencies (specify package to upgrade single package, all by default)
upgrade env package="": virtualenv
    #!/usr/bin/env bash
    opts="--upgrade"
    test -z "{{ package }}" || opts="--upgrade-package {{ package }}"
    FORCE=true "{{ just_executable() }}" requirements-{{ env }} $opts


# *args is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the rendering functional tests
test-functional *args: devenv
    $BIN/coverage run --module pytest tests {{ args }}
    $BIN/coverage report || $BIN/coverage html

docker-build:
    docker compose build unit-tests

# Run unit tests for templated analysis code in templates/
test-unit *args: requirements-unit docker-build
    #!/usr/bin/env bash
    set -eu
    args="{{ args }}"
    test -z "$args" && args=$(ls interactive_templates/templates/)
    for analysis in $args
    do
        path=interactive_templates/templates/$analysis
        test -d $path/tests || continue
        echo "Running unit tests for analysis $analysis in $path..."
        docker compose run -e PYTHONPATH=$path unit-tests env -C $path python -m pytest --disable-warnings
    done

test:
    #!/usr/bin/env bash
    set -eu
    if [[ "{{ invocation_directory() }}" = *interactive_templates/templates/* ]]; then
        {{ just_executable() }} test-unit $(basename {{ invocation_directory() }})
    else
        {{ just_executable() }} test-all
    fi

#run all tests
test-all: test-unit test-functional


package-build: virtualenv
    rm -rf dist

    $PIP install build
    $BIN/python -m build


package-test type: package-build
    #!/usr/bin/env bash
    VENV="test-{{ type }}"
    distribution_suffix="{{ if type == "wheel" { "whl" } else { "tar.gz" } }}"

    # build a fresh venv
    python -m venv $VENV

    # clean up after ourselves, even if there are errors
    trap 'rm -rf $VENV' EXIT

    # ensure a modern pip
    $VENV/bin/pip install pip --upgrade

    # install the wheel distribution
    $VENV/bin/pip install dist/*."$distribution_suffix"

    # Minimal check that it has actually built correctly
    $VENV/bin/python -c "import interactive_templates"

    # check we haven't packaged tests with it
    unzip -Z -1 dist/*.whl | grep -vq "^tests/"


black *args=".": devenv
    $BIN/black --check {{ args }}

check-manifest *args="": devenv
    $BIN/check-manifest {{ args }}

ruff *args=".": devenv
    $BIN/ruff check {{ args }}


# run the various dev checks but does not change any files
check: black check-manifest ruff


# fix formatting and import sort ordering
fix: devenv
    $BIN/black .
    $BIN/isort .

# This recipe works from either the root project dir or one of the analysis
# dirs, in which case it will use devmode
#
# Render an analysis with test data
render analysis="v2" *args="": devenv
    #!/usr/bin/env bash
    set -eu
    if [[ "{{ invocation_directory() }}" = *interactive_templates/templates/* ]]; then
        $BIN/python -m interactive_templates.render {{ invocation_directory() }} {{ args }}
    else
        $BIN/python -m interactive_templates.render {{ analysis }} {{ args }}
    fi


# Cut a release of this package
release:
    #!/usr/bin/env bash
    set -euo pipefail

    CALVER=$(date -u +"%Y.%m.%d.%H%M%S")

    git checkout main
    git pull
    git checkout -b release-$CALVER
    echo $CALVER > version
    git add version
    git commit --message "Release $CALVER"
    gh pr create --fill
