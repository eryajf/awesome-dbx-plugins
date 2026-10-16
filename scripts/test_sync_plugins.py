import unittest

from sync_plugins import add_release_badge, render


class PreservedPluginRowsTest(unittest.TestCase):
    repository = "example/dbx-plugin"
    link = "[example/dbx-plugin](https://github.com/example/dbx-plugin)"
    badge = "[![release](https://img.shields.io/github/v/release/example/dbx-plugin)](https://github.com/example/dbx-plugin/releases)"

    def test_current_row_keeps_one_release_column(self):
        row = f"| {self.link} | stars | {self.badge} | description |"
        self.assertEqual(add_release_badge(row, self.repository), row)
        self.assertEqual(render([], {}, [row]).splitlines()[-1], row)

    def test_legacy_row_gets_a_release_column_once(self):
        legacy = f"| {self.link} | stars | description |"
        expected = f"| {self.link} | stars | {self.badge} | description |"
        updated = add_release_badge(legacy, self.repository)
        self.assertEqual(updated, expected)
        self.assertEqual(add_release_badge(updated, self.repository), expected)


if __name__ == "__main__":
    unittest.main()
