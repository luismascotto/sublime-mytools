import base64
import os
import unittest

from mytools import powershell


def fake_which(available):
    return lambda name: available.get(name)


class NormalizeTextTests(unittest.TestCase):
    def test_joins_selections_with_lf(self):
        self.assertEqual(powershell.normalize_text(["a", "b"]), "a\nb")

    def test_skips_empty_selections(self):
        self.assertEqual(powershell.normalize_text(["", "a", ""]), "a")

    def test_normalizes_crlf_and_cr(self):
        self.assertEqual(powershell.normalize_text(["a\r\nb\rc"]), "a\nb\nc")


class QuotePsLiteralTests(unittest.TestCase):
    def test_wraps_in_single_quotes(self):
        self.assertEqual(powershell.quote_ps_literal(r"C:\tmp\x.txt"), r"'C:\tmp\x.txt'")

    def test_doubles_embedded_single_quotes(self):
        self.assertEqual(powershell.quote_ps_literal("O'Brien"), "'O''Brien'")


class BootstrapScriptTests(unittest.TestCase):
    def test_embeds_quoted_path(self):
        script = powershell.build_bootstrap_script(r"C:\Users\O'Brien\t.txt")
        self.assertIn(r"$path = 'C:\Users\O''Brien\t.txt'", script)

    def test_registers_one_shot_idle_insert(self):
        script = powershell.build_bootstrap_script("x")
        self.assertIn("PowerShell.OnIdle -MaxTriggerCount 1", script)
        self.assertIn("[Microsoft.PowerShell.PSConsoleReadLine]::Insert", script)


class EncodeCommandTests(unittest.TestCase):
    def test_round_trips_as_utf16le_base64(self):
        script = "Write-Host 'olá ✓'"
        encoded = powershell.encode_command(script)
        self.assertEqual(base64.b64decode(encoded).decode("utf-16-le"), script)


class BuildLaunchSpecTests(unittest.TestCase):
    PWSH = r"C:\Program Files\PowerShell\7\pwsh.exe"
    WT = r"C:\WindowsApps\wt.exe"

    def test_windows_terminal(self):
        which = fake_which({"pwsh.exe": self.PWSH, "wt.exe": self.WT})
        spec = powershell.build_launch_spec("pwsh.exe", "windows_terminal", "ENC", which)
        self.assertEqual(
            spec.args,
            [self.WT, "-w", "new", "new-tab", self.PWSH, "-NoExit", "-EncodedCommand", "ENC"],
        )
        self.assertFalse(spec.new_console)

    def test_falls_back_to_console_when_wt_missing(self):
        which = fake_which({"pwsh.exe": self.PWSH})
        spec = powershell.build_launch_spec("pwsh.exe", "windows_terminal", "ENC", which)
        self.assertEqual(spec.args, [self.PWSH, "-NoExit", "-EncodedCommand", "ENC"])
        self.assertTrue(spec.new_console)

    def test_console(self):
        which = fake_which({"pwsh.exe": self.PWSH, "wt.exe": self.WT})
        spec = powershell.build_launch_spec("pwsh.exe", "console", "ENC", which)
        self.assertEqual(spec.args, [self.PWSH, "-NoExit", "-EncodedCommand", "ENC"])
        self.assertTrue(spec.new_console)

    def test_missing_executable_raises(self):
        with self.assertRaises(powershell.LaunchError):
            powershell.build_launch_spec("pwsh.exe", "console", "ENC", fake_which({}))

    def test_invalid_terminal_raises(self):
        which = fake_which({"pwsh.exe": self.PWSH})
        with self.assertRaises(powershell.LaunchError):
            powershell.build_launch_spec("pwsh.exe", "tmux", "ENC", which)


class WriteTempTextTests(unittest.TestCase):
    def test_writes_utf8_without_newline_translation(self):
        path = powershell.write_temp_text("a\nolá")
        try:
            with open(path, "rb") as f:
                self.assertEqual(f.read(), "a\nolá".encode("utf-8"))
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
