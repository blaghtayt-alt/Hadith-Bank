"""Regression guards for the owner-authorized Global Hadith Library URL migration.

The operational links may be switched ONLY during the repository/Pages cutover.
This file belongs to the gated migration branch; it must not be merged before
the repository has actually been renamed and its Pages domain validated.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
OLD_GITHUB = "https://github.com/blaghtayt-alt/Hadith-Bank"
OLD_PAGES = "https://blaghtayt-alt.github.io/Hadith-Bank/"
NEW_GITHUB = "https://github.com/blaghtayt-alt/Global-Hadith-Library"
NEW_PAGES = "https://blaghtayt-alt.github.io/Global-Hadith-Library/"

ACTIVE_PATHS = (
    "README.md",
    ".github/workflows/reader-pages.yml",
    "reader/template.html",
    "scripts/build_reader.py",
    "scripts/import_filipino_hisn.py",
    "docs/WEBSITE.md",
    "docs/READING-AND-SEARCH.md",
    "docs/SEARCH-ENGINE-DISCOVERY.md",
    "docs/ADDING-MATERIAL.md",
    "docs/CHINESE-HISN.md",
    "docs/SOURCE-EDITION-STATUS.md",
    "docs/DOCUMENTATION-EVIDENCE-2026-11-15.md",
    "docs/JAPANESE-RESEARCH-V3.md",
    "docs/SEARCHABLE-BANK-IMPLEMENTATION.md",
    "docs/WEB-SOURCE-RESOLUTION-20261113.md",
)


class RepositoryURLCutoverTests(unittest.TestCase):
    def test_no_old_operational_urls(self):
        for name in ACTIVE_PATHS:
            with self.subTest(path=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertNotIn(OLD_GITHUB, content)
                self.assertNotIn(OLD_PAGES, content)

    def test_current_site_and_repository_bindings(self):
        reader = (ROOT / "scripts/build_reader.py").read_text(encoding="utf-8")
        shell = (ROOT / "reader/template.html").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/reader-pages.yml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name, content in (("reader", reader), ("template", shell), ("readme", readme)):
            with self.subTest(file=name):
                self.assertIn(NEW_GITHUB, content)
                self.assertIn(NEW_PAGES, content)
        self.assertIn("--production-url " + NEW_PAGES, workflow)
        self.assertIn("--candidate-url " + NEW_PAGES, workflow)
        self.assertNotIn(OLD_PAGES, workflow)


if __name__ == "__main__":
    unittest.main()
