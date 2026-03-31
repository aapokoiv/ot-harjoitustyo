from invoke import task
import subprocess

### code that AI helped starting
@task
def start(ctx):
    subprocess.run(
        ["python3", "src/index.py"],
        stdin=None,
        stdout=None,
        stderr=None
    )@task
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
