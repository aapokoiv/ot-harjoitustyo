# Chess app

With this app you can play and review chess games locally between two people. 
The app provides a GUI that you can play and review the games from.

The app needs python version 3.12 or higher. It has been tested with 3.12.

## Documentation

- [User instructions](documentation/user-instructions.md)

- [Requirements specification](documentation/requirements-specification.md)

- [Working hours register](documentation/working-hours-register.md)

- [Changelog](documentation/changelog.md)

- [Architecture](documentation/architecture.md)

- [Testing](documentation/testing.md)

## Latest release

[Latest](https://github.com/aapokoiv/ot-harjoitustyo/releases/tag/viikko6)

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
