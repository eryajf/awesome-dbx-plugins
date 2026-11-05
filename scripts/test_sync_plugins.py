import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from sync_plugins import RepositoryNotFound, add_release_badge, get_json, render


class UnavailableRepositoryTest(unittest.TestCase):
    def test_get_json_maps_github_404_to_repository_not_found(self):
        error = HTTPError(
            "https://api.github.com/repos/example/missing",
            404,
            "Not Found",
            hdrs=None,
            fp=None,
        )
        with patch("sync_plugins.urlopen", side_effect=error):
            with self.assertRaises(RepositoryNotFound):
                get_json("https://api.github.com/repos/example/missing")

    def test_render_skips_missing_repository(self):
        def get_json(url):
            if url.endswith("/missing/dbx-plugin"):
                raise RepositoryNotFound("repository not found")
            return {
                "html_url": "https://github.com/example/dbx-plugin",
                "stargazers_count": 3,
            }

        with patch("sync_plugins.get_json", side_effect=get_json):
            table = render(["missing/dbx-plugin", "example/dbx-plugin"], {}, [])

        self.assertNotIn("missing/dbx-plugin", table)
        self.assertIn("example/dbx-plugin", table)


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
