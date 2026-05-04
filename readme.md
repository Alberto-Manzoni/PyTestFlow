# PyTestFlow

PyTestFlow is a Python test executive built on top of Prefect.
It turns decorated Python functions into traceable test steps and runs them in
ordered flows.

> Requires `prefect>=3.4` and Python 3.10+.

## Repositories

- Engine: https://github.com/Alberto-Manzoni/PyTestFlow
- Frontend: https://github.com/Alberto-Manzoni/PyTestFlow-FrontEnd

## Installation

```bash
python -m pip install "git+https://github.com/Alberto-Manzoni/PyTestFlow.git@main"
```

### Init the workspace

```bash
pytestflow init
```

Set the environment variable as suggested from the CLI


## Usage

```bash
pytestflow start
```
Open the web gui at the url indicated by the CLI.



## Core concepts

- Steps are Prefect tasks via `@step` and specialized decorators.
- `TestSequence` are Prefect flows that aggregate child states.
- `ptf_context` shares `globals`, `locals`, `results`, and `current_step`.
- `SequentialProcessModel` orchestrates callbacks in this order:
  `pre_uut -> main_sequence -> post_uut -> report -> database_logging`.
- Process model main output is stored as both `main_results` and `main_result`
  for compatibility.

## Project structure

1. `pytestflow/core`: wrappers, context, states, sequence execution.
2. `pytestflow/steps`: built-in step decorators.
3. `pytestflow/flow_utils`: flow helper utilities.
4. `pytestflow/reporting`: HTML/JSON reporting helpers.

