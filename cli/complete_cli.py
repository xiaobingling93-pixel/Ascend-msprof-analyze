import click

from profiler.advisor.utils.tools import CONTEXT_SETTINGS


@click.command(context_settings=CONTEXT_SETTINGS,
               short_help='Auto complete ma-advisor command in terminal, support "bash(default)/zsh/fish".')
@click.argument('shell_type', nargs=1, default="Bash", type=click.Choice(["Bash", "Zsh", "Fish"], case_sensitive=False))
def auto_complete_cli(shell_type):
    """
    Auto complete ma-advisor command in terminal.

    Example:

    \b
    # print bash auto complete command to terminal
    msprof-analyze auto-completion Bash
    """
    click.echo("Tips: please paste following shell command to your terminal to activate auto completion.\n")
    if shell_type.lower() == "bash":
        bash_str = 'eval "$(_MSPROF_ANALYZE_COMPLETE=bash_source msprof-analyze)"'
    elif shell_type.lower() == "zsh":
        bash_str = 'eval "$(_MSPROF_ANALYZE_COMPLETE=zsh_source msprof-analyze)"'
    elif shell_type.lower() == "fish":
        bash_str = 'eval (env _MSPROF_ANALYZE_COMPLETE=fish_source msprof-analyze)'
    else:
        click.echo(f'Unsupported shell type {shell_type}.')
        return
    click.echo(f'{bash_str}\n')
