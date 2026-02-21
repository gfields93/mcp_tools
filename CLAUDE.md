# Claude Instructions

## Git

- Always ask for explicit permission before pushing to any remote repository.

## Query Authoring

- Never use `SELECT *` in query SQL. All columns must be listed explicitly.
- Every new query's `return_values` must document each column that appears in the SELECT list.

## Testing

- Run tests with `.venv/bin/pytest` from the project root.
- Test results are written to `test-results.xml` (JUnit XML) in the project directory.
- Coverage HTML report is written to `htmlcov/` in the project directory.
- Both `test-results.xml` and `htmlcov/` are gitignored.
