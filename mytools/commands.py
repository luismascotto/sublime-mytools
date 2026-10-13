import os
import subprocess

import sublime
import sublime_plugin

from . import powershell

SETTINGS_FILE = "MyTools.sublime-settings"


class MytoolsSendToPowershellCommand(sublime_plugin.TextCommand):
    def is_enabled(self):
        return any(not region.empty() for region in self.view.sel())

    def run(self, edit):
        text = powershell.normalize_text([self.view.substr(r) for r in self.view.sel()])
        if not text:
            sublime.status_message("MyTools: nothing selected")
            return

        settings = sublime.load_settings(SETTINGS_FILE)
        executable = settings.get("powershell_executable", "pwsh.exe")
        terminal = settings.get("terminal", powershell.TERMINAL_WINDOWS_TERMINAL)

        text_path = powershell.write_temp_text(text)
        try:
            encoded = powershell.encode_command(powershell.build_bootstrap_script(text_path))
            spec = powershell.build_launch_spec(executable, terminal, encoded)
            subprocess.Popen(
                spec.args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if spec.new_console else 0,
            )
        except (powershell.LaunchError, OSError) as e:
            try:
                os.remove(text_path)
            except OSError:
                pass
            print("MyTools: Send to PowerShell failed: {!r}".format(e))
            sublime.error_message("MyTools: Send to PowerShell failed.\n\n{}".format(e))
            return

        print("MyTools: launched {}".format(spec.args[:-1] + ["<encoded>"]))
        sublime.status_message("MyTools: sent to PowerShell")
