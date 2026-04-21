from invoke import task
import subprocess

### code that AI helped starting
@task
def start(ctx):
    subprocess.run(
        ["python3", "src/ui.py"],
        stdin=None,
        stdout=None,
        stderr=None
    )
### code that AI helped ending

@task
def test(ctx):
    ctx.run("pytest src", pty=True)

@task
def coverage(ctx):
    ctx.run("coverage run --branch -m pytest src", pty=True)

@task(coverage)
def coverage_report(ctx):
    ctx.run("coverage html", pty=True)

@task
def lint(ctx):
    ctx.run(f'pylint --rcfile=".pylintrc" --ignore-patterns="index.py, ui.py" src', pty=True)
