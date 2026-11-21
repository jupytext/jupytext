import re
import sys
from pathlib import Path

import pytest
from jupytext.version import __version__


def replace_issue_number_with_links(text):
    def link_issue(match):
        prefix, issue = match.groups()
        if issue is None:
            return match[0]
        return f"{prefix}[#{issue}](https://github.com/mwouts/jupytext/issues/{issue})"

    return re.sub(r"\[[^\]\n]*\]\([^\n)]*\)|([^\[-])#([0-9]+)", link_issue, text)


@pytest.mark.parametrize(
    "input,output",
    [
        (
            "Issue #535",
            "Issue [#535](https://github.com/mwouts/jupytext/issues/535)",
        ),
        (
            "Multiline\ntext (#123)",
            "Multiline\ntext ([#123](https://github.com/mwouts/jupytext/issues/123))",
        ),
        (
            "(#123) and [Another-project-#535](https://custom_url)",
            "([#123](https://github.com/mwouts/jupytext/issues/123)) and [Another-project-#535](https://custom_url)",
        ),
        (
            "[Jupytext Sync #42](https://github.com/caenrigen/vscode-jupytext-sync/issues/42) and #123",
            "[Jupytext Sync #42](https://github.com/caenrigen/vscode-jupytext-sync/issues/42) and "
            "[#123](https://github.com/mwouts/jupytext/issues/123)",
        ),
    ],
)
def test_replace_issue_numbers_with_links(input, output):
    assert replace_issue_number_with_links(input) == output


@pytest.mark.skipif(sys.version_info < (3, 5), reason="'PosixPath' object has no attribute 'read_text'")
def test_update_changelog():
    changelog_file = Path(__file__).parent.parent.parent.parent / "CHANGELOG.md"
    cur_text = changelog_file.read_text()
    new_text = replace_issue_number_with_links(cur_text)
    if cur_text != new_text:
        changelog_file.write_text(new_text)  # pragma: no cover


def test_version_matches_changelog():
    root_path = Path(__file__).parent.parent.parent.parent
    changelog_file = root_path / "CHANGELOG.md"

    # Read version from version.py
    current_version = __version__

    # Read first version from CHANGELOG.md
    changelog_text = changelog_file.read_text()
    prev_line = ""
    for line in changelog_text.splitlines():
        if not line.startswith("--------"):
            prev_line = line
            continue

        changelog_version = prev_line.split("(")[0].strip()
        assert current_version == changelog_version, (
            f"Version mismatch: version.py has {current_version}, but CHANGELOG.md has {changelog_version}"
        )

        return

    raise ValueError("No version found in CHANGELOG.md")


def test_version_pep440_compliance():
    pep440_regex = r"^(?:(?:0|[1-9]\d*)\.){2}(?:0|[1-9]\d*)(?:[abc]|rc)?(?:\d+)?(?:\.post\d+)?(?:\.dev\d+)?$"
    assert re.match(pep440_regex, __version__), f"Version {__version__} is not PEP 440 compliant"
