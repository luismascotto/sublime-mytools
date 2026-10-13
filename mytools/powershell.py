import base64
import os
import shutil
import tempfile
from typing import Callable, List, NamedTuple, Optional

TERMINAL_WINDOWS_TERMINAL = "windows_terminal"
TERMINAL_CONSOLE = "console"
TERMINALS = (TERMINAL_WINDOWS_TERMINAL, TERMINAL_CONSOLE)

WhichFn = Callable[[str], Optional[str]]


class LaunchError(Exception):
    pass


class LaunchSpec(NamedTuple):
    args: List[str]
    new_console: bool


def normalize_text(selections: List[str]) -> str:
    parts = [s.replace("\r\n", "\n").replace("\r", "\n") for s in selections if s]
    return "\n".join(parts)


def quote_ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_bootstrap_script(text_path: str) -> str:
    # Runs in a child scope so nothing leaks into the interactive session.
    # PSReadLine must be idle at the prompt for Insert() to work, hence OnIdle.
    # $Event.MessageData is $null for OnIdle (PSReadLine raises it without data),
    # so the text goes through a one-shot global variable. The [string] cast keeps
    # Insert() off its char overload, which would insert NUL for $null.
    return (
        "& {\n"
        "    $path = " + quote_ps_literal(text_path) + "\n"
        "    $text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)\n"
        "    Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue\n"
        "    try {\n"
        "        Import-Module PSReadLine -ErrorAction Stop\n"
        "        $global:MyToolsSendText = $text\n"
        "        $null = Register-EngineEvent -SourceIdentifier PowerShell.OnIdle"
        " -MaxTriggerCount 1 -Action {\n"
        "            [Microsoft.PowerShell.PSConsoleReadLine]::Insert([string]$global:MyToolsSendText)\n"
        "            Remove-Variable -Name MyToolsSendText -Scope Global -ErrorAction SilentlyContinue\n"
        "        }\n"
        "    } catch {\n"
        "        Set-Clipboard -Value $text\n"
        "        Write-Warning 'MyTools: PSReadLine unavailable; text copied to clipboard.'\n"
        "    }\n"
        "}\n"
    )


def encode_command(script: str) -> str:
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def build_launch_spec(
    executable: str,
    terminal: str,
    encoded_command: str,
    which: WhichFn = shutil.which,
) -> LaunchSpec:
    if terminal not in TERMINALS:
        raise LaunchError(
            "Invalid 'terminal' setting: {!r}. Expected one of {}.".format(terminal, TERMINALS)
        )

    exe_path = which(executable)
    if exe_path is None:
        raise LaunchError("PowerShell executable not found: {!r}".format(executable))

    ps_args = [exe_path, "-NoExit", "-EncodedCommand", encoded_command]

    if terminal == TERMINAL_WINDOWS_TERMINAL:
        wt_path = which("wt.exe")
        if wt_path is not None:
            return LaunchSpec(args=[wt_path, "-w", "new", "new-tab"] + ps_args, new_console=False)

    return LaunchSpec(args=ps_args, new_console=True)


def write_temp_text(text: str) -> str:
    fd, path = tempfile.mkstemp(prefix="mytools-", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(text)
    except BaseException:
        os.remove(path)
        raise
    return path
