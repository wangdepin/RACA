from __future__ import annotations

import sys

import click

from .login_guard import check_login_command
from .ssh_session import SSHSessionManager


@click.command()
@click.argument("cluster")
@click.argument("command")
@click.option("--timeout", default=300, show_default=True, help="Command timeout in seconds.")
@click.option(
    "--allow-login",
    is_flag=True,
    default=False,
    help="Bypass the login-node guard for a command you know is trivial.",
)
def ssh(cluster: str, command: str, timeout: int, allow_login: bool) -> None:
    """Run COMMAND on CLUSTER via the active SSH session.

    Intended for Claude Code integration: always exits with the remote
    return code, and prints stdout/stderr verbatim.

    Compute-heavy commands (samtools, STAR, big sorts of BAM/FASTQ, …) are
    refused — they belong on a COMPUTE node via srun/sbatch, not the shared
    login node. Pass --allow-login (or set RACA_ALLOW_LOGIN=1) to override.
    """
    block = check_login_command(command, cluster=cluster, allow_login=allow_login)
    if block:
        click.echo(block, err=True)
        sys.exit(2)

    manager = SSHSessionManager()

    healthy, msg = manager.health_check(cluster)
    if not healthy:
        click.echo(
            click.style("ERROR:", fg="red", bold=True)
            + f" Not connected to {cluster}. Run: raca auth {cluster}",
            err=True,
        )
        sys.exit(1)

    result = manager.run(cluster, command, timeout=timeout)

    if result.stdout:
        click.echo(result.stdout, nl=False)
    if result.stderr:
        click.echo(result.stderr, nl=False, err=True)

    sys.exit(result.returncode)
