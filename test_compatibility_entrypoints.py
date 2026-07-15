import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _planner_entrypoint as entrypoint


ROOT = Path(__file__).resolve().parent


class CompatibilityEntrypointTest(unittest.TestCase):
    def test_root_scripts_delegate_to_the_canonical_planner_commands(self):
        expectations = {
            "download_node_csv.py": "--passes",
            "get_data_for_new_city.py": "--query-type",
        }
        for script_name, expected_option in expectations.items():
            with self.subTest(script=script_name):
                result = subprocess.run(
                    [sys.executable, str(ROOT / script_name), "--help"],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected_option, result.stdout)
                self.assertIn("--data-root", result.stdout)

    def test_missing_private_submodule_has_an_actionable_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(entrypoint, "PLANNER_ROOT", Path(directory)):
                with self.assertRaisesRegex(SystemExit, "submodule update --init"):
                    entrypoint.run_planner_script("download_node_csv.py")


if __name__ == "__main__":
    unittest.main()
