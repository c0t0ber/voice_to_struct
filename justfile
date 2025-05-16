set dotenv-load

default:
    just --list

init-venv:
    uv venv -p 3.12

fmt:
    uv run ruff check --fix-only my_future_data
    uv run isort my_future_data
    uv run ruff format my_future_data

lint:
    uv run isort --check my_future_data
    uv run ruff format --check my_future_data
    uv run ruff check my_future_data
    uv run mypy my_future_data

update-deps:
    uv pip compile --no-header --upgrade pyproject.toml -o requirements.txt

install-deps:
    uv pip install -r requirements.txt

run-pipeline:
    uv run python -m my_future_data process-audio-pipeline
    uv run python -m my_future_data aggregate-files
    uv run python -m my_future_data combine-files
