import re
from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


class AbsoluteLinksInReadme(MetadataHookInterface):
    """Hook that processes README.md to make relative links absolute."""

    def update(self, metadata):
        """Set the readme from README.md, with relative links made absolute."""
        readme_src_path = Path(self.root) / "README.md"
        base_url = "https://github.com/jupytext/jupytext/blob/main/"

        metadata["readme"] = {
            "content-type": "text/markdown",
            "text": self.convert_links(readme_src_path, base_url),
        }

    def convert_links(self, src_path, base_url):
        """Convert relative links in README.md to absolute links."""
        content = src_path.read_text(encoding="utf-8")

        # Find markdown links that don't start with http:// or https://
        pattern = re.compile(r"\[([^\]]+)\]\((?!http)([^)]+)\)")

        def replace_link(match):
            text, url = match.groups()
            if not url.startswith(("http://", "https://", "#")):
                url = base_url + url
            return f"[{text}]({url})"

        return pattern.sub(replace_link, content)
