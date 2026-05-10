from invoke import task
import subprocess

### code that AI helped starting
@task
def start(ctx):
    """Launch the Tk user interface."""
    subprocess.run(
        ["python3", "src/ui.py"],
        stdin=None,
        stdout=None,
        stderr=None
    )
### code that AI helped ending

@task
def test(ctx):
    """Run the project's test suite."""
    ctx.run("pytest src", pty=True)

@task
def coverage(ctx):
    """Run tests with coverage collection enabled."""
    ctx.run("coverage run --branch -m pytest src", pty=True)

@task(coverage)
def coverage_report(ctx):
    """Generate the HTML coverage report after running coverage."""
    ctx.run("coverage html", pty=True)

@task
def lint(ctx):
    """Run pylint for the main source tree."""
    ctx.run(f'pylint --rcfile=".pylintrc" --ignore-patterns="index.py, ui.py" src', pty=True)
