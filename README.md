# MyTools (Sublime Text 4 package)

## Install

Requires Windows, Sublime Text 4 and Package Control.

1. Command Palette > `Package Control: Add Repository`, enter:
   `https://raw.githubusercontent.com/luismascotto/sublime-mytools/main/repository.json`
2. Command Palette > `Package Control: Install Package` > `MyTools`.

## Commands

| Command | Default key | Menus |
|---|---|---|
| `mytools_send_to_powershell` | `alt+shift+enter` (only with a non-empty selection) | Context menu, Tools > MyTools, Command Palette (`MyTools: Send to PowerShell`) |

Opens a new PowerShell instance and pre-fills the selected text at the prompt without executing it. Multiple selections are joined with newlines. If PSReadLine is unavailable, the text is copied to the clipboard instead.

Settings and key bindings are available under Preferences > Package Settings > MyTools. Override the key binding in your User keymap, for example:

```json
{ "keys": ["ctrl+alt+shift+enter"], "command": "mytools_send_to_powershell" }
```

## Layout

| Path | Purpose |
|---|---|
| `.python-version` | Selects the Python 3.8 plugin host |
| `plugin.py` | Only top-level `.py` files are loaded by Sublime; re-exports commands |
| `mytools/powershell.py` | Pure logic, no `sublime` import; unit-testable from the CLI |
| `mytools/commands.py` | Sublime `TextCommand` glue |
| `*.sublime-menu`, `*.sublime-commands`, `*.sublime-keymap`, `*.sublime-settings` | UI and configuration resources |
| `tests/unit/` | Standard-library `unittest` tests for `mytools/powershell.py` |

## Development setup

Link the repo into Sublime's `Packages` folder (once):

```powershell
New-Item -ItemType Junction -Path "$env:APPDATA\Sublime Text\Packages\MyTools" -Target "K:\Develop\SublimeSendToPwsh"
```

## Tests

```powershell
python -m unittest discover -s tests/unit -t . -v
```

## Debugging

- View > Show Console (`ctrl+``) shows `print` output and plugin tracebacks.
- In the console, `sublime.log_commands(True)` logs every command triggered (menus, keys, palette); `sublime.log_input(True)` logs key presses, which helps diagnose key binding conflicts.
- Run a command manually from the console: `view.run_command("mytools_send_to_powershell")`.

## Release

Package Control installs from semver git tags (checked about once per hour). Files listed in `.gitattributes` with `export-ignore` are excluded from the installed package.

```powershell
git tag 0.2.0
git push origin 0.2.0
```

Do not install MyTools via Package Control on a machine that uses the development junction: loose files in `Packages\MyTools` override the installed `.sublime-package`. Package Control's default `ignore_vcs_packages: true` keeps it from overwriting the junctioned source (it contains `.git`); keep that setting.

## Reloading footgun

Saving `plugin.py` reloads it, but Sublime does not reload modules under `mytools/`. After editing those, either:

- install `AutomaticPackageReloader` via Package Control (reloads the whole package on save), or
- restart Sublime Text.
