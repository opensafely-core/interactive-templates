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


## Local development environment

Set up a local development environment with:
```
just devenv
```

There are two tests suites.

### Functional tests

The test the full rendering and execution of the analysis templates. They use
`requirements.dev.{in,txt}` to define test requirments, and run in the usual
jusfile venv. 

To run:

```
just test-functional
```


### Unit tests

These test specific things within the analysis code. These run in docker
container based on the OpenSAFELY python image, so that they have the correct
dependencies and environment as they would when run as part of an action.

They have a different set of test dependencies in `requirements.unit.{in,txt}`,
these are installed into the test docker image by default.

To run:

```
just test-unit
```


