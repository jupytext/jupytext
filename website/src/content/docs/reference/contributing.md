---
title: "Contributing"
description: "How to report issues and contribute to Jupytext."
sidebar:
  order: 4
---

Thanks for reading this! Contributions to this project are welcome, and there are many ways you can contribute

## Improve the documentation

You've spotted a typo, a paragraph that is not very clear, or an instruction that does not work? Please follow the _Fork me on Github_ link, edit the document, and submit a pull request.

## Report an issue

You have seen an issue with Jupytext, or you can't find your way in the documentation?
Please let us know, and provide enough information so that we can reproduce the problem.

## Propose enhancements

You want to submit an enhancement on Jupytext? Unless this is a small change, we usually prefer that you let us know beforehand: open an issue that describe the problem you want to solve.

## Changelog fragments (optional)

You do not need to update `CHANGELOG.md`, bump the version, or provide a
changelog fragment for an ordinary PR. Maintainers prepare release notes from
merged PRs and any available fragments when preparing a release.

If you would like to suggest a release note, add a Markdown file in
[`changelog.d/`](https://github.com/jupytext/jupytext/tree/main/changelog.d)
named `<PR-number>.<category>.md`. The categories are `added`, `changed`, `fixed`,
and `security`. Before a PR number is available, use a unique descriptive name,
then rename the file once the PR is open. Write a short bullet point describing
the effect of the change, with a PR link and contributor credit, without version
or category headings. Documentation-only and internal changes usually do not
need a release note.

Separate fragments reduce conflicts between PRs in the merge queue. They remain
optional: a PR will not be blocked because it has no fragment. Maintainers fill
in missing entries, choose their final wording and order by importance or topic,
and remove incorporated fragments when updating the changelog. Fragment filenames
do not determine the published order.

Development sections in `CHANGELOG.md` link to the fragment directory. When
starting a new development version, maintainers update both
`src/jupytext/version.py` and the changelog heading, use the canonical spelling
(for example `1.19.7.dev0`), and add that link below the heading. The link is
removed when finalizing the release notes. After version or changelog changes,
run `pixi run pytest tests/functional/docs/test_changelog.py`.

## Add support for another language

A pull request for which you do not need to contact us in advance is the addition of a new language to Jupytext. In principle that should be easy - you would only have to:
- document the language extension and comment by adding one line to `_SCRIPT_EXTENSIONS` in `jupytext/languages.py`.
- add the language to `website/src/content/docs/formats/languages.md`
- contribute a sample notebook in `tests/data/notebooks/inputs/ipynb_[language]`.
- run the tests suite (create a [development environment](/reference/developing/), then execute `pytest` locally). The tests will generate various text representations corresponding to your notebook under  `tests/data/notebooks/outputs/`. Please verify that these files are valid scripts, and include them in your PR.
