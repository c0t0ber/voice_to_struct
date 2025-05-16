# My Future Data

## Continuous Integration

The project uses GitHub Actions for continuous integration to ensure code quality. The CI workflow:

- Runs on Python 3.12
- Checks code formatting with isort and ruff format
- Runs linting with ruff
- Performs static type checking with mypy

### CI Workflow

The CI pipeline runs automatically on:
- Push to main/master branch
- Pull requests to main/master branch

### Local Development

Before pushing code, you can run the same checks locally using just:

```bash
just fmt    # Format code
just lint   # Run linting and type checks
```

To update dependencies:

```bash
just update-deps   # Update dependencies
just install-deps  # Install updated dependencies
```
