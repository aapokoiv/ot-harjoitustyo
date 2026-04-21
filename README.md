# Chess app

With this app you can move chess pieces according to their characteristics.
Check based move validation and therefore proper chess is not yet fully working.

## Documentation

- [Requirements specification](documentation/requirements-specification.md)

- [Working hours register](documentation/working-hours-register.md)

- [Changelog](documentation/changelog.md)

- [Architecture](documentation/architecture.md)

## Installation

1. Install dependencies
   
Run this in the project root:
```bash
poetry install
```
2. Start the app

```bash
poetry run invoke start
```


## Testing and linting

1. Make sure poetry is installed

### Unittests

```bash
poetry run invoke test
```

### Pylint

```bash
poetry run invoke lint
```

### Coverage report

```bash
poetry run invoke coverage-report
```
