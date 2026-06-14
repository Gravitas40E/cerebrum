from __future__ import annotations

import unittest

from utils.markdown import strip_markdown


class MarkdownTestCase(unittest.TestCase):
    def test_strip_markdown(self) -> None:
        source = "# Heading\n\n- **Bold** and [link](https://example.com)\n> quote"
        self.assertEqual(strip_markdown(source), "Heading\n\nBold and link\nquote")


if __name__ == "__main__":
    unittest.main()
