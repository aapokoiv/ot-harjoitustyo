# Chess app

With this app you can play chess locally between two people on the same computer. 
Chess rules and the flow of the game have been implemented.
The app provides a GUI that you can play the game from.

*Currently draw by repetition or by 50 move rule are not implemented*

## Documentation

- [User instructions](documentation/user-instructions.md)

- [Requirements specification](documentation/requirements-specification.md)

- [Working hours register](documentation/working-hours-register.md)

- [Changelog](documentation/changelog.md)

- [Architecture](documentation/architecture.md)

## Latest release

[Latest release](https://github.com/aapokoiv/ot-harjoitustyo/releases/tag/viikko6)

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
