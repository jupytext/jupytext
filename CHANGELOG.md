Jupytext ChangeLog
==================

1.19.5.dev0 (2026-mm-dd)
-------------------

**Changed**
- Harden the github action ([#1569](https://github.com/jupytext/jupytext/pull/1569)). Thanks to [Peyton Murray](https://github.com/peytondmurray) for this PR!

**Security**
- Paired paths can no longer be written outside the notebook's directory tree. A `formats` entry read from notebook metadata, e.g. `../../../../etc///py` or an absolute path, is now rejected instead of driving a file write above the working tree ([#1588](https://github.com/jupytext/jupytext/pull/1588)).

1.19.4 (2026-06-21)
-------------------

**Changed**
- Jupytext's documentation is now at https://jupytext.org! ([#1538](https://github.com/jupytext/jupytext/pull/1538))
- We have moved Jupytext to its own Jupytext organization ([#1546](https://github.com/jupytext/jupytext/issues/1546))
- Updated the JupyterLab extension production dependencies (12 patch updates) ([#1541](https://github.com/jupytext/jupytext/pull/1541))
- We require `pandoc<3.10` on the CI as pandoc converts the "3.10" string to a float, which then causes issues in Jupytext ([#1545](https://github.com/jupytext/jupytext/issues/1545))
- Fixed the CI so that tests also run on scheduled runs, and so that `jupyterfs` tests are skipped when their initialization fails ([#1539](https://github.com/jupytext/jupytext/pull/1539))
- In the CI, the extension is build using a dedicated `build` pixi environment.

**Fixed**
- We now support unicode characters while dumping YAML ([#1542](https://github.com/jupytext/jupytext/pull/1542))

**Added**
- A new `custom_language_magics` option is available ([#1491](https://github.com/jupytext/jupytext/issues/1491)). Thanks to [steovd](https://github.com/steovd) for making the PR!

**Security**
- Fixed [GHSA-m22c-4q2m-m5wr](https://github.com/jupytext/jupytext/security/advisories/GHSA-m22c-4q2m-m5wr): the `update-playwright-snapshots` workflow was
  triggerable by any user via an `issue_comment` event. It now checks that the
  comment author is an OWNER, MEMBER, or COLLABORATOR before running
  ([#1535](https://github.com/jupytext/jupytext/pull/1535))
- Set `persist-credentials: false` on all workflow checkout steps as
  defense-in-depth, preventing a live `GITHUB_TOKEN` from being left in
  `.git/config` where attacker-controlled build hooks could read it. This is
  strictly required only for `update-playwright-snapshots` (fixed above), but
  applies to all workflows so they remain safe if their scope is later extended.

1.19.3 (2026-05-17)
-------------------

**Fixed**
- The Jupytext CLI issues a warning when a notebook is not trusted. Also, trust is preserved when empty outputs are added (follow-up on [#1505](https://github.com/mwouts/jupytext/issues/1505))

**Changed**
- The dependabot config has been updated to correctly bump extension packages, now allowing only production updates and ignoring dev dependencies ([#1532](https://github.com/mwouts/jupytext/pull/1532)). Thanks to [Mahendra Paipuri](https://github.com/mahendrapaipuri) for this PR!
- Removed deprecated stylelint packages (`stylelint-config-prettier` and `stylelint-prettier`) from the JupyterLab extension dependencies ([#1530](https://github.com/mwouts/jupytext/pull/1530))
- We have removed Python 3.9 testing from the CI (Python 3.9 reached EOL in October 2025)


1.19.2 (2026-05-10)
-------------------

**Fixed**
- Trusted notebooks remain trusted after `jupytext --sync` ([#1505](https://github.com/mwouts/jupytext/issues/1505))
- We have fixed the homepage link in `package.json`. Thanks to [Michał Krassowski](https://github.com/krassowski) for making this PR ([#1494](https://github.com/mwouts/jupytext/pull/1494))
- Thanks to [Brigitta Sipőcz](https://github.com/bsipocz) for fixing a broken link in our CLI ([#1428](https://github.com/mwouts/jupytext/pull/1428))
- The `--quiet` flag now suppresses the `creating missing directory` warning when writing to a path that includes a prefix ([#1533](https://github.com/mwouts/jupytext/pull/1533))


**Changed**
- The CI workflow has been restructured to maximize parallelization. All test suites (pip, conda, UI) and the build step now run concurrently after pre-commit checks, instead of sequentially, reducing CI times ([#1527](https://github.com/mwouts/jupytext/pull/1527))
- We have skipped the tests that involve `jupyterfs` on Python 3.12+ as they started failing on the CI with no obvious way to fix them ([#1509](https://github.com/mwouts/jupytext/issues/1509))
- We have changed the configuration of Dependabot to get grouped dependency updates for our JupyterLab extension.
- We have merged a series of Dependabot security updates: [#1516](https://github.com/mwouts/jupytext/pull/1516), [#1517](https://github.com/mwouts/jupytext/pull/1517), [#1519](https://github.com/mwouts/jupytext/pull/1519), [#1520](https://github.com/mwouts/jupytext/pull/1520), [#1522](https://github.com/mwouts/jupytext/pull/1522), [#1524](https://github.com/mwouts/jupytext/pull/1524)


1.19.1 (2026-01-25)
-------------------

**Changed**
- Jupytext does not change the file icons anymore! Thanks to [Michał Krassowski](https://github.com/krassowski) for finally solving this long standing issue! ([#398](https://github.com/mwouts/jupytext/issues/398))
- We have bumped lodash from 4.17.21 to 4.17.23 in JupyterLab extension ([#1483](https://github.com/mwouts/jupytext/pull/1483))
- We require `marimo<=0.19.4` in tests following a change in the location of the `marimo` import ([#1485](https://github.com/mwouts/jupytext/issues/1485))


1.19.0 (2026-01-18)
-------------------

**Changed**
- The environment used to develop Jupytext is now maintained using Pixi ([#1459](https://github.com/mwouts/jupytext/pull/1459))

**Fixed**
- We have restored the support for `.qmd` documents in Jupyter ([#1435](https://github.com/mwouts/jupytext/issues/1435))
- We have fixed warnings about the cell ids like either `Cell is missing an id field` or `Additional properties are not allowed ('id' was unexpected)` when converting to some formats, including Pandoc ([#1464](https://github.com/mwouts/jupytext/pull/1464))
- We have updated the dependencies of the Jupytext extension for JupyterLab. Many thanks to [Mahendra Paipuri](https://github.com/mahendrapaipuri) for his PR ([#1477](https://github.com/mwouts/jupytext/pull/1477))!

**Added**
- We have added a new `py:marimo` format, which uses the `marimo` command line interface to convert notebooks to and from the Marimo format ([#1431](https://github.com/mwouts/jupytext/pull/1431))


1.18.1 (2025-10-19)
-------------------

**Fixed**
- Fixed test `test_check_source_is_newer_when_using_jupytext_sync` to work reliably on systems with low filesystem timestamp resolution ([#1460](https://github.com/mwouts/jupytext/issues/1460))

**Changed**
- We now use `pixi` to maintain the local Python environments used for developing and testing Jupytext.


1.18.0 (2025-10-18)
-------------------

**Added**
- The documentation has a chapter on the [Jupytext Sync](https://jupytext.readthedocs.io/en/latest/vs-code.html) extension for VS Code ([#1395](https://github.com/mwouts/jupytext/issues/1395))
- We have added a new option `--check-source-is-newer` to the Jupytext CLI. Use this option if you want to make sure that the file passed as argument to Jupytext is the newest of all paired files, and/or newer than the destination file.
- We have added a section on [Jupyter Collaboration](https://jupytext.readthedocs.io/en/latest/jupyter-collaboration.html) which also provides a very useful autoreload functionality ([#406](https://github.com/mwouts/jupytext/issues/406), [#1401](https://github.com/mwouts/jupytext/issues/1401))
- Pairing groups allow you to define different pairing configurations for specific subsets of notebooks. The `formats` configuration option now supports a list of format dictionaries for first-match pairing. Use `[[formats]]` sections in your TOML configuration to define multiple format specifications, where the first matching format is used. This allows applying different pairing rules to notebooks in different locations, such as generating documentation markdown files only for tutorial notebooks ([#1383](https://github.com/mwouts/jupytext/issues/1383))
- We have added more tests to document the complex pairing formats, which also work on Windows ([#1028](https://github.com/mwouts/jupytext/issues/1028))
- Pairing into nested folders was fixed on Windows ([#1028](https://github.com/mwouts/jupytext/issues/1028))
- Jupytext is now tested with Python 3.14 ([#1456](https://github.com/mwouts/jupytext/issues/1456))

**Fixed**
- The Jupytext CLI now detects if a file it has read or consulted has been modified while it was processing it. That can happen in the context of the [Jupytext Sync](https://marketplace.visualstudio.com/items?itemName=caenrigen.jupytext-sync) extension for VS Code ([#1411](https://github.com/mwouts/jupytext/issues/1411), [vscode-jupytext-sync-#12](https://github.com/caenrigen/vscode-jupytext-sync/issues/12)). When such a synchronous modification is detected, Jupytext now raises an error. Many thanks to [Anne Archibald](https://github.com/aarchiba) for reporting the issue and preparing an inspiring PR ([#1417](https://github.com/mwouts/jupytext/pull/1417)).
- We don't import `notebook` when `jupyter_server` is available ([#1436](https://github.com/mwouts/jupytext/issues/1436))
- Jupytext now supports more characters in the cell metadata keys, to improve compatibility with `jupyterlab-slideshow` ([#1441](https://github.com/mwouts/jupytext/issues/1441)). Thanks to [Nicolas Thierry](https://github.com/nthiery) for this fix.
- The function `find_jupytext_configuration_file` now works with relative directories ([#1440](https://github.com/mwouts/jupytext/issues/1440)). This fix was contributed by [Thierry Parmentelat](https://github.com/parmentelat).
- We have fixed a parsing error for R Markdown files ([#1429](https://github.com/mwouts/jupytext/issues/1429))
- We have fixed a parsing error when the first cell of the notebook contains a YAML header that is not a dict ([#1444](https://github.com/mwouts/jupytext/issues/1444))

**Changed**
- We have updated the pre-commit hooks. The code is now formatted using `ruff format`, and updated for Python 3.9+ using https://github.com/asottile/pyupgrade ([#1423](https://github.com/mwouts/jupytext/issues/1423))


1.17.3 (2025-08-28)
-------------------

**Added**
- All the extensions supported by Jupytext now appear in the `--to` paragraph
of `jupytext --help` ([#433](https://github.com/mwouts/jupytext/issues/433))
- We have added a new function `get_formats_from_notebook_path` that returns the list of paired
formats for a given notebook ([#1419](https://github.com/mwouts/jupytext/issues/1419))

**Fixed**
- We have fixed `jupytext --sync`, and the contents manager, to make sure that a simple `.py` file (not in the percent format) will not be treated as a paired file when the Jupytext configuration file has `formats="ipynb,py:percent"` ([#1418](https://github.com/mwouts/jupytext/issues/1418))
- A notebook can be moved in Jupyter even if that makes it unpaired ([#1414](https://github.com/mwouts/jupytext/issues/1414))
- The test against `jupyter-fs` now installs its `fs` extra dependency ([#1398](https://github.com/mwouts/jupytext/issues/1398))
- The `jupytext --sync` command now works correctly with symbolic links. Thanks to [mccullerlp](https://github.com/mccullerlp) for reporting ([#1407](https://github.com/mwouts/jupytext/issues/1407)) and addressing ([#1408](https://github.com/mwouts/jupytext/pull/1408)) the problem!
- Jupytext will look for `quarto.cmd` on Windows. Thanks to [mccullerlp](https://github.com/mccullerlp) for documenting the issue ([#1406](https://github.com/mwouts/jupytext/issues/1406), [#1409](https://github.com/mwouts/jupytext/pull/1409)).
- We have corrected the `jupytext --paired-paths` command: it will now take the Jupytext configuration file, if any, into account ([#1419](https://github.com/mwouts/jupytext/issues/1419))


1.17.2 (2025-06-01)
-------------------

**Fixed**
- The `--set-formats` argument takes precedence over pre-existing pairing information in the notebook ([#1386](https://github.com/mwouts/jupytext/issues/1386))

**Changed**
- We have removed Python 3.8 from the list of supported Python version, and from the CI, as it has reached its EOL

**Added**
- ROOT-flavored C++ notebooks can be paired to `.cpp` files - thanks to [Steven Gardiner](https://github.com/sjgardiner) for this contribution ([#1384](https://github.com/mwouts/jupytext/pull/1384))


1.17.1 (2025-04-26)
-------------------

**Fixed**
- Renaming files other than notebooks will not load their content ([#1376](https://github.com/mwouts/jupytext/issues/1376))


1.17.0 (2025-04-05)
-------------------

**Added**
- The MyST frontmatter found in MyST Markdown notebooks can be mapped to a YAML header at the top of the Jupyter notebook. This way MyST notebooks in either the `md:myst` or `ipynb` format can be used with MyST. Thanks to [Ian Carroll](https://github.com/itcarroll) for proposing and implementing this change ([#1314](https://github.com/mwouts/jupytext/issues/1314))
- The context menu has a "New Text Notebook" entry. Thanks to [Mahendra Paipuri](https://github.com/mahendrapaipuri) for this PR ([#1365](https://github.com/mwouts/jupytext/pull/1365))!


**Changed**
- Jupytext's default contents manager is now derived from the asynchronous AsyncLargeFileManager. Thanks to [Darshan Poudel](https://github.com/Darshan808) for making this finally happen ([#1328](https://github.com/mwouts/jupytext/pull/1328))!
- The [percent format](https://jupytext.readthedocs.io/en/latest/formats-scripts.html#the-percent-format) is now the default format for scripts. If you run `jupytext --to py notebook.ipynb` you now get a `py:percent` script (use `--to py:light` for the light format) [#1201](https://github.com/mwouts/jupytext/pull/1201)
- The `rst2md` conversion now works with `sphinx-gallery>=0.8`. Thanks to [Thomas J. Fan](https://github.com/thomasjpfan) for fixing this! ([#1334](https://github.com/mwouts/jupytext/pull/1334))
- We have updated the JupyterLab extension dependencies ([#1300](https://github.com/mwouts/jupytext/pull/1300), [#1355](https://github.com/mwouts/jupytext/pull/1355), [#1360](https://github.com/mwouts/jupytext/pull/1360)). Thanks to [Mahendra Paipuri](https://github.com/mahendrapaipuri) for these PRs!

**Fixed**
- We have added and fixed round trip tests on MyST Markdown notebooks ([#759](https://github.com/mwouts/jupytext/issues/759), [#789](https://github.com/mwouts/jupytext/issues/789), [#1267](https://github.com/mwouts/jupytext/issues/1267), [#1317](https://github.com/mwouts/jupytext/issues/1317))
- The `--quiet` option now works with the `--pipe` mode of Jupytext CLI ([#1305](https://github.com/mwouts/jupytext/issues/1305))
- Jupytext is now compatible with the cell toolbar extension - thanks to [Nicolas Brichet](https://github.com/brichet) for the fix! ([#1358](https://github.com/mwouts/jupytext/pull/1358))
- The project description on PyPI now uses absolute links ([#1287](https://github.com/mwouts/jupytext/issues/1287))


1.16.7 (2025-02-09)
-------------------

**Added**
- Logtalk notebooks are now supported ([#1308](https://github.com/mwouts/jupytext/pull/1308)) - thanks to [Paulo Moura](https://github.com/pmoura) for this contribution

**Fixed**
We have updated the dependencies of the JupyterLab extension to address [security issues](https://github.com/mwouts/jupytext/security/dependabot).


1.16.6 (2024-12-16)
-------------------

**Fixed**
- We fixed a "File Changed" warning when saving notebooks ([#1301](https://github.com/mwouts/jupytext/issues/1301))

**Changed**
- The original file name is easier to infer from the tmp file name in pre-commit hooks ([#1289](https://github.com/mwouts/jupytext/issues/1289)) - thanks to [Lunin Leonid](https://github.com/lrlunin) for making this change.


1.16.5 (2024-12-15)
-------------------

**Fixed**
- We have fixed a notebook corruption issue when using Jupytext with Jupyter-Collaboration ([#1124](https://github.com/mwouts/jupytext/issues/1124), [jupyter-collaboration 214](https://github.com/jupyterlab/jupyter-collaboration/issues/214)).
- We have added the `require_hash` argument on the Jupytext contents manager. The hash of a paired file is the concatenation of the hash of the text file and the hash for the `.ipynb` file ([#1165](https://github.com/mwouts/jupytext/issues/1165))
- The `rst2md` tests have been fixed by requiring `sphinx<8` ([#1266](https://github.com/mwouts/jupytext/issues/1266))
- Some dependencies of the JupyterLab extensions were updated ([#1272](https://github.com/mwouts/jupytext/issues/1272), [#1273](https://github.com/mwouts/jupytext/issues/1273), [#1280](https://github.com/mwouts/jupytext/issues/1280), [#1285](https://github.com/mwouts/jupytext/issues/1285), [#1290](https://github.com/mwouts/jupytext/issues/1290))
- The pre-commit hook is now compatible with log.showsignature=True ([#1281](https://github.com/mwouts/jupytext/issues/1281)). Thanks to [Justin Lecher](https://github.com/jlec) for this fix.

**Added**
- Jupytext is now tested with Python 3.13 ([#1242](https://github.com/mwouts/jupytext/issues/1242)). Thanks to [Jerry James](https://github.com/jamesjer) for the suggested fixes!
- The extension of a notebook piped into stdin will be taken in the notebook metadata ([#1282](https://github.com/mwouts/jupytext/issues/1282))


1.16.4 (2024-07-12)
-------------------

**Fixed**
- We use `asyncio.iscoroutinefunction` to determine whether the current contents manager is sync or async ([#1260](https://github.com/mwouts/jupytext/issues/1260))


1.16.3 (2024-07-09)
-------------------

**Fixed**
- We use `inspect` to determine whether the current contents manager derives from `AsyncContentsManager` (which is not
supported by Jupytext at the moment). This fixes a compatibility issue with `jupyter-fs==1.0.0` ([#1239](https://github.com/mwouts/jupytext/issues/1239)). Thanks to [Mahendra Paipuri](https://github.com/mahendrapaipuri) for this PR!
- We have fixed a typo when `build_jupytext_contents_manager_class` can't be imported ([#1162](https://github.com/mwouts/jupytext/issues/1162))
- A Python 3.13 deprecation warning was fixed [#1241](https://github.com/mwouts/jupytext/pull/1241) - thanks to [Jerry James](https://github.com/jamesjer)
- We have fixed a typo when `build_jupytext_contents_manager_class` can't be imported ([#1162](https://github.com/mwouts/jupytext/issues/1162))
- Some dependencies of the JupyterLab extensions were updated ([#1243](https://github.com/mwouts/jupytext/issues/1243), [#1245](https://github.com/mwouts/jupytext/issues/1245))

**Added**
- Lua notebooks are now supported ([#1252](https://github.com/mwouts/jupytext/pull/1252)) - thanks to [erentar](https://github.com/erentar) for this contribution
- Go notebooks are supported too ([#1244](https://github.com/mwouts/jupytext/issues/1244))! Many thanks to [Jan Pfeifer](https://github.com/janpfeifer), author of [GoNB](https://github.com/janpfeifer/gonb), and to [HaveF](https://github.com/HaveF) for their help on this topic.
- Empty prefixes are now allowed in Jupytext format when specified as a dictionary ([#1144](https://github.com/mwouts/jupytext/issues/1144))

**Changed**
- We've had to deactivate the tests on the Quarto format in the CI as the Quarto round trip
might now add a Markdown cell to the notebook ([#1255](https://github.com/mwouts/jupytext/issues/1255))


1.16.2 (2024-05-05)
-------------------

**Added**
- Added support for Xonsh notebooks ([#1213](https://github.com/mwouts/jupytext/pull/1213)) - thanks to [Jeffrey Odongo](https://github.com/jsquaredosquared) for this contribution

**Changed**
- By default, the JupyterLab extension for Jupytext is not included in the build (set `HATCH_BUILD_HOOKS_ENABLE=true` to include it). This simplifies the installation of Jupytext in pre-commit hooks ([#1210](https://github.com/mwouts/jupytext/issues/1210))
- Temporary text notebooks for the `--pipe` or `--check` commands are now created in the notebook directory ([#1206](https://github.com/mwouts/jupytext/issues/1206))
- Jupytext uses the standard library `tomllib` in Python 3.11, or `tomli` in Python 3.10 or older, to match JupyterLab's dependencies ([#1195](https://github.com/mwouts/jupytext/issues/1195))
- The dependencies of the JupyterLab extension were updated ([#1216](https://github.com/mwouts/jupytext/issues/1216), [#1218](https://github.com/mwouts/jupytext/issues/1218), [#1231](https://github.com/mwouts/jupytext/issues/1231))
- `jupytext --sync` will not update the timestamp of text notebooks if their content is unchanged ([#1215](https://github.com/mwouts/jupytext/issues/1215))


**Fixed**
- Jupytext is now tested with `pandoc>=3.0`. Please note that switching to `pandoc>=3.0` will add cell ids to your `pandoc:md` notebooks ([#1006](https://github.com/mwouts/jupytext/issues/1006))


1.16.1 (2024-01-13)
-------------------

**Changed**
- The CI has been updated. Thanks to [Christian Le](https://github.com/LecrisUT) for taking care of this! ([#1190](https://github.com/mwouts/jupytext/issues/1190), [#1204](https://github.com/mwouts/jupytext/issues/1204))

**Fixed**
- Fixed an issue about unpairing notebooks from the Jupytext Menu ([#1197](https://github.com/mwouts/jupytext/issues/1197))
- JupyterLab's dependency `follow-redirects` was updated from 1.15.3 to 1.15.4 ([#1203](https://github.com/mwouts/jupytext/issues/1203))


1.16.0 (2023-12-03)
-------------------

**Added**
- The Jupytext Menu is back! And text notebooks can be created directly from the launcher. This is an outstanding contribution by [Mahendra Paipuri](https://github.com/mahendrapaipuri) ([#1154](https://github.com/mwouts/jupytext/issues/1154), [#1163](https://github.com/mwouts/jupytext/issues/1163)). This requires JupyterLab 4.x or Jupyter Notebook 7.x.

**Changed**
- Jupytext is now configured with `pyproject.toml` and built with `hatch`. The layout has been reorganised to follow `src-layout` ([#1140](https://github.com/mwouts/jupytext/issues/1140)). This is another outstanding contribution by [Mahendra Paipuri](https://github.com/mahendrapaipuri).
- The tests are now part of the `sdist`. They have been reorganized into unit/functional/integration/external ([#1167](https://github.com/mwouts/jupytext/issues/1167), [#1173](https://github.com/mwouts/jupytext/issues/1173)).
- The legacy extension for Jupyter Notebook <=6 (the Jupytext Menu) has been removed.

**Fixed**
- The bibliography section in Rmd files does not become a code cell anymore ([#1161](https://github.com/mwouts/jupytext/issues/1161))
- Commented code in `active-py` cells is not uncommented anymore ([#1131](https://github.com/mwouts/jupytext/issues/1131))
- The test coverage has been restored ([#1167](https://github.com/mwouts/jupytext/issues/1167), [#1173](https://github.com/mwouts/jupytext/issues/1173))
- We test Jupytext against the pre-release version of JupyterLab, and other dependencies ([#1168](https://github.com/mwouts/jupytext/issues/1168))


1.15.2 (2023-09-16)
-------------------

**Added**
- The JupyterLab extension is now compatible with the [JupyterLab RISE](https://github.com/jupyterlab-contrib/rise) extension. Many thanks to [Frédéric Collonval](https://github.com/fcollonval) for his PR ([#1126](https://github.com/mwouts/jupytext/pull/1126))!


1.15.1 (2023-08-26)
-------------------

**Added**
- We have added a new command line interface `jupytext-config` that you can use to set Jupytext as the default viewer for text notebooks in JupyterLab and Jupyter Notebook 7. Thanks to [Thierry Parmentelat](https://github.com/parmentelat) for this contribution! ([#1094](https://github.com/mwouts/jupytext/pull/1094))


1.15.0 (2023-07-30)
-------------------

**Changed**
- This version comes with a version of the JupyterLab extension that is compatible with JupyterLab 4.x. Many thanks to [Thierry Parmentelat](https://github.com/parmentelat) for his PRs! ([#1092](https://github.com/mwouts/jupytext/pull/1092), [#1109](https://github.com/mwouts/jupytext/pull/1109))
- Pandoc 3.0 is now supported, thanks to [Raniere Silva](https://github.com/rgaiacs) for his PR ([#1099](https://github.com/mwouts/jupytext/pull/1099))
- We have reorganized the documentation and the README.md ([#1031](https://github.com/mwouts/jupytext/issues/1031), [#1073](https://github.com/mwouts/jupytext/issues/1073))
- Invalid `pyproject.toml` files will be ignored by Jupytext in Jupyter ([#1103](https://github.com/mwouts/jupytext/issues/1103))
- We have updated the pre-commit tools


1.14.7 (2023-06-29)
-------------------

**Changed**
- We have updated the GitHub workflows - thanks to Matthew Feickert and to Cristian Le for their help on this subject ([#1037](https://github.com/mwouts/jupytext/issues/1037))
- We have removed the upper bound on `markdown-it-py<3`. Now we test Jupytext with `markdown-it-py` in versions `2.x` and `3.x` on the CI ([#1075](https://github.com/mwouts/jupytext/issues/1075))

**Fixed**
- Notebooks with an empty YAML header work ([#1070](https://github.com/mwouts/jupytext/issues/1070))
- Double quote strings in R Markdown options can contain single quotes ([#1079](https://github.com/mwouts/jupytext/issues/1079))
- The necessary directories are created when paired notebooks are moved to a sub-folder ([#1059](https://github.com/mwouts/jupytext/issues/1059))
- Commented quotes are recognized as such ([#1060](https://github.com/mwouts/jupytext/issues/1060))
- Jupytext can use either `pkg_resources` or `packaging` to parse version numbers ([#1085](https://github.com/mwouts/jupytext/issues/1085))


1.14.6 (2023-06-04)
-------------------

**Changed**
- This version comes with a build requirement `jupyterlab>=3,<4`, as the Jupyterlab
extension for Jupytext is not compatible with JupyterLab 4 yet ([#1054](https://github.com/mwouts/jupytext/issues/1054))
- The JupyterLab extension was released to `npm` in version 1.3.9.


1.14.5 (2023-02-25)
-------------------

**Added**
- Added Stata as a supported language ([#1027](https://github.com/mwouts/jupytext/pull/1027)) - thanks to [Raffaele Mancuso](https://github.com/raffaem) for this contribution
- Added SAS as a supported language ([#1047](https://github.com/mwouts/jupytext/pull/1047)) - thanks to [lawrencet149](https://github.com/lawrencet149) for this contribution
- We have added a series of test to make sure that the main formats support cell tags ([#1024](https://github.com/mwouts/jupytext/issues/1024))

**Fixed**
- When a metadata key is not a valid identifier, a warning is emitted and the metadata is not saved to the text representation ([#1042](https://github.com/mwouts/jupytext/issues/1042))
- The CI was fixed by [Matthew Feickert](https://github.com/matthewfeickert) ([#1035](https://github.com/mwouts/jupytext/pull/1035))
- We now use `concurrency` to cancel previous runs on the same branch/PR ([#1037](https://github.com/mwouts/jupytext/issues/1037))
- We use both `codecov.notify.after_n_builds` and `comment.after_n_builds` to get only the final codecov comment

**Changed**
- Empty tags are not exported to the text notebook anymore ([#960](https://github.com/mwouts/jupytext/issues/960))
- We updated the `yarn.lock` file for the jupyter lab extension to address security vulnerabilities ([#1030](https://github.com/mwouts/jupytext/issues/1030), [#1036](https://github.com/mwouts/jupytext/issues/1036))
- In the pre-commit tests we now use `main` for the main branch


1.14.4 (2022-12-11)
-------------------

**Added**
- Added Wolfram Language as a supported language ([#1014](https://github.com/mwouts/jupytext/issues/1014)) - thanks to [Etienne Dechamps](https://github.com/dechamps) for this contribution


1.14.3 (2022-12-11)
-------------------

**Fixed**
- When the default contents manager is _async_ (i.e. `jupyter_server>=2.0.0`), the Jupyter server extension for Jupytext derives a contents manager from `LargeFileManager` instead, as async contents managers are not supported by Jupytext at the moment ([#1020](https://github.com/mwouts/jupytext/issues/1020))
- We have made adjustments on the CI as flake8 was moved to GitHub, and Python 3.6 is not available anymore on `ubuntu-latest`


1.14.2 (2022-11-12)
-------------------

**Fixed**
- The sample notebooks have been normalized with `nbformat.validator.normalize` ([#1002](https://github.com/mwouts/jupytext/issues/1002)).
- The warnings in the test suite that we cannot fix are filtered using a new `pytest.ini` file
- We updated the `yarn.lock` file for the jupyter lab extension to address security vulnerabilities ([#984](https://github.com/mwouts/jupytext/issues/984), [#1005](https://github.com/mwouts/jupytext/issues/1005), [#1011](https://github.com/mwouts/jupytext/issues/1011))

**Changed**
- The CI uses Python 3.9 rather than 3.7 when testing conda environments

**Added**
- Gnuplot is now supported ([#998](https://github.com/mwouts/jupytext/issues/998)) - thanks to [razimantv](https://github.com/razimantv) for this contribution
- We now test Jupytext against Python 3.6 to 3.11 on the CI
- We have added a test to document how to use the folder and prefix matching when pairing notebooks ([#974](https://github.com/mwouts/jupytext/issues/974))


1.14.1 (2022-07-29)
-------------------

**Fixed**
- The timestamp of a paired notebook is the timestamp of the most recent paired file. This fixes the warning "File Changed"
after reloading the notebook in Jupyter ([#978](https://github.com/mwouts/jupytext/issues/978)).


1.14.0 (2022-07-03)
-------------------

**Changed**
- The Jupytext configuration file has a new option `cm_config_log_level` that defaults to `info_if_changed`.
With that value, the contents manager will log a line regarding the configuration file used only when the
config file is not the same as the one previously used ([#959](https://github.com/mwouts/jupytext/issues/959)) -
many thanks to R.C. Thomas for suggesting this and thoughtfully testing the patch.
- Hidden configuration files like `.jupytext.toml` or `.jupytext.py` are now ignored by Jupytext's contents manager
when `allow_hidden=False` (that option was introduced in `jupyter_server==2.0.0a1`) ([#964](https://github.com/mwouts/jupytext/issues/964)).
- We have changed `jupytext --set-formats` to make it more similar to `jupytext --sync`. Now `--set-formats` will not
override existing paired files anymore ([#969](https://github.com/mwouts/jupytext/issues/969)).

**Added**
- We have added a test `test_pre_commit_hook_sync_with_no_config` that documents how to use the pre-commit hook without
a configuration file ([#967](https://github.com/mwouts/jupytext/issues/967))

1.13.8 (2022-04-04)
-------------------

**Fixed**
- Text-only notebooks are always trusted (as they don't include any output cells) ([#941](https://github.com/mwouts/jupytext/issues/941))
- We made sure that our tests also work in absence of a Python kernel ([#906](https://github.com/mwouts/jupytext/issues/906))
- The coverage of the `tests` folder has been restored at 100%
- Bash commands like `!{cmd}` are now correctly escaped in the `py:percent` format ([#938](https://github.com/mwouts/jupytext/issues/938))

**Added**
- Added Tcl as a supported language ([#930](https://github.com/mwouts/jupytext/issues/930)) - thanks to [shishitao](https://github.com/shishitao) for this contribution
- Added Maxima as a supported language ([#927](https://github.com/mwouts/jupytext/issues/927)) - thanks to [Alberto Lusiani](https://github.com/alusiani) for contributing a sample Maxima notebook.

**Changed**
- The Jupytext contents manager is derived from the `LargeFileManager` imported from `jupyter_server` rather than `notebook` ([#933](https://github.com/mwouts/jupytext/issues/933))
- Allow for markdown-it-py v2 ([#924](https://github.com/mwouts/jupytext/issues/924))
- We have updated the hooks used in the test pre-commits, to fix an issue on the CI ([#940](https://github.com/mwouts/jupytext/issues/940), [#942](https://github.com/mwouts/jupytext/issues/942))
- We updated the `yarn.lock` file for the jupyter lab extension to address security vulnerabilities ([#904](https://github.com/mwouts/jupytext/issues/904), [#925](https://github.com/mwouts/jupytext/issues/925), [#935](https://github.com/mwouts/jupytext/issues/935), [#939](https://github.com/mwouts/jupytext/issues/939))


1.13.7 (2022-02-09)
-------------------

**Fixed**
- The Jupytext CLI only suggest `--update` when the target is an .ipynb file ([#905](https://github.com/mwouts/jupytext/issues/905)) - thanks to [st--](https://github.com/st--) for this contribution
- We made sure that commands like `cat notebook.md | jupytext --execute` work ([#908](https://github.com/mwouts/jupytext/issues/908))

**Added**
- Added Haskell as supported language ([#909](https://github.com/mwouts/jupytext/issues/909)) - thanks to [codeweber](https://github.com/codeweber) for this contribution

**Changed**
- We have updated the pre-commit hooks and in particular we switched to the first stable version of `black==22.1.0`.
- We require `pandoc==2.16.2` for testing. The representation for code cells changed from ` ``` {.python}` to ` ``` python` in that version of Pandoc ([#906](https://github.com/mwouts/jupytext/issues/906)). We don't use `pandoc>=2.17` in tests at the moment because of the introduction of cell ids that cannot be filtered.
- Jupytext will not add anymore a UTF-8 encoding on Python scripts when the notebook contains non-ascii characters ([#907](https://github.com/mwouts/jupytext/issues/907))
- We have added `pyupgrade` to the pre-commit hooks used for developing Jupytext ([#907](https://github.com/mwouts/jupytext/issues/907))


1.13.6 (2022-01-11)
-------------------

**Fixed**
- The `text_representation` metadata of text notebooks is filtered from `.ipynb` files both in `jupytext.write` and in the contents manager for Jupyter ([#900](https://github.com/mwouts/jupytext/issues/900))

**Changed**
- Jupytext will not issue a warning when a format suffix starting with '.', '-' or '_' is passed to the `--to` option ([#901](https://github.com/mwouts/jupytext/issues/901))


1.13.5 (2021-12-27)
-------------------

**Fixed**
- Jupytext will not open a text notebook that is not UTF-8 ([#896](https://github.com/mwouts/jupytext/issues/896))


1.13.4 (2021-12-12)
-------------------

**Changed**
- The test suite filters the warnings that don't belong to Jupytext ([#823](https://github.com/mwouts/jupytext/issues/823))

**Fixed**
- The parsing of notebooks that don't have a YAML header (like `docs/formats.md`) was improved.
- The test suite works with `pytest-randomly` ([#838](https://github.com/mwouts/jupytext/issues/838))


1.13.3 (2021-12-04)
-------------------

**Changed**
- The "Jupytext Notebook" factory that lets the user configure the Notebook viewer as the default for text notebooks accepts more filetypes: "myst", "r-markdown" and "quarto" ([#803](https://github.com/mwouts/jupytext/issues/803))
- Empty MyST Markdown files are valid notebooks ([#883](https://github.com/mwouts/jupytext/issues/883))
- Jupytext also works with `markdown-it-py` v2.0 ([#885](https://github.com/mwouts/jupytext/issues/885))


1.13.2 (2021-11-30)
-------------------

**Changed**
- The extension for JupyterLab benefited from a series of improvements contributed by [Frédéric Collonval](https://github.com/fcollonval):
  - A new "Jupytext Notebook" factory offers the option to open text notebooks directly with the notebook view ([#803](https://github.com/mwouts/jupytext/issues/803)). To use it, follow the instructions in the [documentation](https://github.com/mwouts/jupytext/blob/main/docs/index.md#Install).
  - The ICommandPalette is optional, for compatibility with RISE within JupyterLab [RISE[#605](https://github.com/mwouts/jupytext/issues/605)](https://github.com/damianavila/RISE/pull/605)
  - Added support for translation
- Branch `master` was renamed to `main` (links in the documentation were updated)


1.13.1 (2021-10-07)
-------------------

**Fixed**
- The magic commands in `py:percent` scripts with no explicit format information remain commented over a round trip ([#848](https://github.com/mwouts/jupytext/issues/848))


1.13.0 (2021-09-25)
-------------------

**Added**
- The Jupytext CLI has a new `--diff` command to show the differences between two notebooks (and if you want to see the changes in a file being updated by Jupytext, use `--show-changes`) ([#799](https://github.com/mwouts/jupytext/issues/799))
- Jupyter will show the diff between text and `ipynb` paired notebooks when it cannot open a paired notebook because the `ipynb` version is more recent. Also, if the inputs in the two files are identical then the notebook will open with no error ([#799](https://github.com/mwouts/jupytext/issues/799))
- The `py:percent` format will use raw strings when encoding Markdown cells as string, if they contain backslash characters ([#836](https://github.com/mwouts/jupytext/issues/836))

**Fixed**
- We have upgraded the jupyterlab extension dependencies and especially `ansi-regex` to fix a security vulnerability ([#857](https://github.com/mwouts/jupytext/issues/857))

**Changed**
- The Jupytext configuration file is reloaded only when a notebook is opened, saved, or when a different folder is explored ([#797](https://github.com/mwouts/jupytext/issues/797))


1.12.0 (2021-09-09)
-------------------

**Added**
- Jupytext supports Quarto notebooks (with `.qmd` extension) ([#837](https://github.com/mwouts/jupytext/issues/837))
- Jupytext can be configured through the `pyproject.toml` file. Thanks to Robin Brown for this contribution! ([#828](https://github.com/mwouts/jupytext/issues/828))
- Jupytext now supports OCaml files with `.ml` extension. Thanks to Quentin Fortier for getting this started ([#832](https://github.com/mwouts/jupytext/issues/832))

**Fixed**
- Added more test to make sure that notebooks can be trusted. In practice, notebooks could not be trusted in JupyterLab<3.0.13 because of the absence of cell ids ([#826](https://github.com/mwouts/jupytext/issues/826))


1.11.5 (2021-08-31)
-------------------

**Fixed**
- Fixed typos revealed by `codespell` - thanks to @hectormz for this contribution ([#829](https://github.com/mwouts/jupytext/issues/829))
- We updated the dependencies of the `jupyterlab-jupytext` extension to address several security issues ([#842](https://github.com/mwouts/jupytext/issues/842)) ([#843](https://github.com/mwouts/jupytext/issues/843))
- The Jupytext dev environment (`requirements-dev.txt`) now uses `jupyterlab==3.0.17` rather than `3.0.0` because of another security issue ([#839](https://github.com/mwouts/jupytext/issues/839))


1.11.4 (2021-07-14)
-------------------

**Changed**
- The documentation illustrates how the `cell_markers` option (and the other ones) can be set directly in the `jupytext.toml` config file ([#809](https://github.com/mwouts/jupytext/issues/809)).
- The dependency on `mdit-py-plugins` through `markdown-it-py[plugins]` was made explicit ([#814](https://github.com/mwouts/jupytext/issues/814))

**Fixed**
- System assigns of the form `var = !cmd` are commented out ([#816](https://github.com/mwouts/jupytext/issues/816))
- Fixed an `InconsistentPath` issue with notebooks paired with scripts in a folder. The prefix in the Jupytext formats always use /, while paths might use either / or \ ([#806](https://github.com/mwouts/jupytext/issues/806))
- Tests that cannot succeed are skipped when either the Jupytext folder is not a git repository, when `sphinx-gallery` is too recent, or when `pandoc` is not up-to-date ([#814](https://github.com/mwouts/jupytext/issues/814))
- Removed the mention of '--update' in 'jupytext --pipe' since outputs are preserved already


1.11.3 (2021-06-10)
-------------------

**Changed**
- Jupytext CLI has a new option `--use-source-timestamp` that sets the last modification time of the output file equal to that of the source file (this avoids having to change the timestamp of the source file) ([#784](https://github.com/mwouts/jupytext/issues/784))
- In the pre-commit mode, Jupytext now uses the commit timestamp to determine which file in the pair is the most recent ([#780](https://github.com/mwouts/jupytext/issues/780))


**Fixed**
- Dependencies of the JupyterLab extension have been upgraded to fix a security vulnerability ([#798](https://github.com/mwouts/jupytext/pull/798))
- The `--warn-only` option also applies to pipes. Use this if the pipe may fail, e.g. if you apply `black` on a possibly invalid script ([#781](https://github.com/mwouts/jupytext/issues/781))
- Variables assigned from a magic command are commented out in `py` scripts ([#781](https://github.com/mwouts/jupytext/issues/781))
- Fixed a round-trip issue on notebooks that have None/null in their metadata ([#792](https://github.com/mwouts/jupytext/issues/792))


1.11.2 (2021-05-02)
-------------------

**Changed**
- Jupytext's dependency markdown-it-py is now in v1 ([#769](https://github.com/mwouts/jupytext/issues/769))
- The optional argument `fmt` in `jupytext.reads` now has the default value `None` - thanks to Yuvi Panda ([#763](https://github.com/mwouts/jupytext/issues/763))

**Fixed**
- All text files are opened with an explicit `utf-8` encoding ([#770](https://github.com/mwouts/jupytext/issues/770))
- Previously `--pipe black` was not always putting two blank lines between functions. To fix that we load the internal Jupytext
  cell metadata like `lines_to_next_cell` from the text file rather than ipynb ([#761](https://github.com/mwouts/jupytext/issues/761))
- The timestamp of the source file is not updated any more when the destination file is not in the pair ([#765](https://github.com/mwouts/jupytext/issues/765), [#767](https://github.com/mwouts/jupytext/issues/767))

**Added**
- A new test documents when the `ipython3` pygment lexer appears in MyST Markdown files ([#759](https://github.com/mwouts/jupytext/issues/759))


1.11.1 (2021-03-26)
-------------------

**Fixed**
- Format options stored in the notebook itself are now taken into account (Fixes [#757](https://github.com/mwouts/jupytext/issues/757))


1.11.0 (2021-03-18)
-------------------

**Fixed**
- The `jupytext.toml` config file can now be used together with the `jupytext` pre-commit hook ([#752](https://github.com/mwouts/jupytext/issues/752))
- The `notebook_extensions` option of the `jupytext.toml` file now works ([#746](https://github.com/mwouts/jupytext/issues/746))

**Changed**
- The options in `jupytext.toml` where renamed to match the `jupytext` metadata in the text notebooks. One should now use `formats` rather than `default_jupytext_formats` and `notebook_metadata_filter` rather than `default_notebook_metadata_filter` ([#753](https://github.com/mwouts/jupytext/issues/753))


1.10.3 (2021-03-07)
-------------------

**Fixed**
- We have updated `marked`, an indirect dependency of the `jupyterlab-jupytext` extension, to fix a moderate vulnerability ([#750](https://github.com/mwouts/jupytext/issues/750)).
- We use non-random cell ids in the tests to avoid test failures due to duplicate cell ids ([#747](https://github.com/mwouts/jupytext/issues/747))


1.10.2 (2021-02-17)
-------------------

**Fixed**
- We have adjusted the `MANIFEST.in` file to exclude the `node_modules` but still include the JupyterLab extension that was missing in the `.tar.gz` (and conda) package in v1.10.1. Many thanks to Martin Renou for providing the fix at ([#741](https://github.com/mwouts/jupytext/issues/741))


1.10.1 (2021-02-11)
-------------------

**Added**
- The recursive glob pattern `**/*.ipynb` is now supported by Jupytext - Thanks to Banst for this contribution ([#731](https://github.com/mwouts/jupytext/issues/731))
- Sage notebooks are supported. They can be converted to `.sage` and `.md` files and back. Thanks to Lars Franke for suggesting this! ([#727](https://github.com/mwouts/jupytext/issues/727))
- Jupytext is also accessible with `python -m jupytext`. Thanks to Matthew Brett for his PR! ([#739](https://github.com/mwouts/jupytext/issues/739))

**Changed**
- We have tested Jupytext with the new cell ids introduced in `nbformat>=5.1.0`. Cell ids are preserved by the `--sync` and `--update` command. So we removed the constraint on the version of `nbformat` ([#735](https://github.com/mwouts/jupytext/issues/735)).

**Fixed**
- We filtered out the `node_modules` folder from the `.tar.gz` package for Jupytext ([#730](https://github.com/mwouts/jupytext/issues/730))


1.10.0 (2021-02-04)
-------------------

**Added**
- Jupytext has a pre-commit hook! Many thanks to John Paton and Aaron Gokaslan for making this happen ([#698](https://github.com/mwouts/jupytext/issues/698))
- Jupytext CLI will not rewrite files that don't change ([#698](https://github.com/mwouts/jupytext/issues/698)).
- If you want to see the diff for changed files, use the new `--diff` option ([#722](https://github.com/mwouts/jupytext/issues/722))
- We have added `isort` and `autoflake8` to the `pre-commit` configuration file used for developing the Jupytext project ([#709](https://github.com/mwouts/jupytext/issues/709))
- We made sure that `py:percent` scripts end with exactly one blank line ([#682](https://github.com/mwouts/jupytext/issues/682))
- We checked that Jupytext works well with symbolic links to folders (not files!) ([#696](https://github.com/mwouts/jupytext/issues/696))

**Changed**
- Jupytext does not work properly with the new cell ids of the version 4.5 of `nbformat>=5.1.0` yet, so we added the requirement `nbformat<=5.0.8` ([#715](https://github.com/mwouts/jupytext/issues/715))
- Jupytext will issue an informative error or warning on notebooks in a version of nbformat that is not known to be supported ([#681](https://github.com/mwouts/jupytext/issues/681), [#715](https://github.com/mwouts/jupytext/issues/715))

**Fixed**
- Code cells that contain triple backticks (or more) are now encapsulated with four backticks (or more) in the Markdown and MyST Markdown formats. The version number for the Markdown format was increased to 1.3, and the version number for the MyST Markdown format was increased to 0.13 ([#712](https://github.com/mwouts/jupytext/issues/712))
- Indented magic commands are supported ([#694](https://github.com/mwouts/jupytext/issues/694))


1.9.1 (2021-01-06)
------------------

**Fixed**
- Include the lab extension that was missing in the conda package ([#703](https://github.com/mwouts/jupytext/pull/703)).


1.9.0 (2021-01-05)
------------------

**Changed**
- The Jupytext extension for JupyterLab is compatible with JupyterLab 3.0, thanks to Martin Renou's awesome contribution ([#683](https://github.com/mwouts/jupytext/pull/683)).


1.8.2 (2021-01-04)
------------------

**Changed**
- Jupytext 1.8.2 depends on `python>=3.6`. The last version of Jupytext explicitly tested with Python 2.7 and 3.5 was Jupytext 1.7.1 ([#697](https://github.com/mwouts/jupytext/issues/697)).


1.8.1 (2021-01-03)
------------------

**Changed**
- The dependency on `markdown-it-py` is conditional on `python>=3.6` ([#697](https://github.com/mwouts/jupytext/issues/697))


1.8.0 (2020-12-22)
------------------

**Changed**
- Removed support for Python 2.7 and 3.5, a preliminary step towards a JupyterLab 3.0-compatible extension ([#683](https://github.com/mwouts/jupytext/issues/683))
- The MyST Markdown format uses `markdown-it-py~=0.6.0` ([#692](https://github.com/mwouts/jupytext/issues/692))


1.7.1 (2020-11-16)
------------------

**Fixed**
- Text notebooks have the same format and mimetype as ipynb notebooks. This fixes the _File Load Error - content.indexOf is not a function_ error on text notebooks ([#659](https://github.com/mwouts/jupytext/issues/659))


1.7.0 (2020-11-14)
------------------

**Changed**
- Jupytext's contents manager uses the parent CM's `get` and `save` methods to read and save text files, and explicitly calls `jupytext.reads` and `jupytext.writes` to do the conversion. We don't use `mock` nor internal parent methods any more. Thanks to Max Klein for helping making this work! ([#634](https://github.com/mwouts/jupytext/issues/634), [#635](https://github.com/mwouts/jupytext/issues/635))
- Thanks to the above, Jupytext can work on top of contents manager that don't derive from `FileContentsManager`, and in particular it works with `jupyterfs` ([#618](https://github.com/mwouts/jupytext/issues/618))
- The documentation was reorganized. `README.md` was simplified and now includes many links to the documentation.
- The documentation now uses `myst_parser` rather than `recommonmark`. And we use `conda` on RTD ([#650](https://github.com/mwouts/jupytext/issues/650), [#652](https://github.com/mwouts/jupytext/issues/652))
- The `readf` and `writef` functions were dropped (they had been deprecated in favor of `read` and `write` in June 2019, v1.2.0)
- The description & dependencies of the JupyterLab extension were updated ([#654](https://github.com/mwouts/jupytext/issues/654))
- The `--set-kernel -` command, on a Python notebook, gives an explicit error when no kernel is not found that matches the current Python executable.
- All the GitHub workflow files were concatenated into a unique file, and we have added an `pypi-publish` step to automatically publish the package on PyPi when new releases are created.
- The `CHANGELOG.md` file was moved under `docs` to better expose the history of changes.

**Added**
- Configuration errors are reported in the console and/or in Jupyter ([#613](https://github.com/mwouts/jupytext/issues/613))
- Jupytext's Contents Manager internal errors are logged on the console, and trigger an HTTP Error 500 ([#638](https://github.com/mwouts/jupytext/issues/638))
- The GitHub actions run on both push events and pull requests, and duplicate jobs are skipped ([#605](https://github.com/mwouts/jupytext/issues/605))
- Jupytext has a `tox.ini` file, thanks to Chris Sewell ([#605](https://github.com/mwouts/jupytext/issues/605))
- Jupytext is tested against Python 3.9
- The `execution` cell metadata is now filtered by default ([#656](https://github.com/mwouts/jupytext/issues/656))

**Fixed**
- Optional dependency on `sphinx-gallery` frozen to version `~=0.7.0` ([#614](https://github.com/mwouts/jupytext/issues/614))
- Codecov/patch reports should be OK now ([#639](https://github.com/mwouts/jupytext/issues/639))
- Jupytext tests work on non-English locales ([#636](https://github.com/mwouts/jupytext/issues/636))
- Cell metadata that are already present in text notebook can be filtered out using a config file ([#656](https://github.com/mwouts/jupytext/issues/656))
- Optional cell attributes like attachments are preserved ([#671](https://github.com/mwouts/jupytext/issues/671))


1.6.0 (2020-09-01)
------------------

**Added**
- New option `hide_notebook_metadata` to encapsulate the notebook metadata in an HTML comment ([#527](https://github.com/mwouts/jupytext/issues/527))
- New option `root_level_metadata_as_raw_cell`. Set it to `False` if you don't want to see root level metadata
of R Markdown notebooks as a raw cell in Jupyter ([#415](https://github.com/mwouts/jupytext/issues/415))
- New option `doxygen_equation_markers` to translate Markdown equations into Doxygen equations ([#517](https://github.com/mwouts/jupytext/issues/517))
- New option `custom_cell_magics` to comment out cells starting with user-specific cell magics ([#513](https://github.com/mwouts/jupytext/issues/513))
- Documented how to use `isort` on notebooks ([#553](https://github.com/mwouts/jupytext/issues/553))
- `jupytext notebook.ipynb --to filename.py` will warn that `--to` is used in place of `--output`.
- `jupytext --set-formats filename.py` will suggest to use `--sync` instead of `--set-formats` ([#544](https://github.com/mwouts/jupytext/issues/544))
- Warn if 'Include Metadata' is off when saving text files in Jupyter ([#561](https://github.com/mwouts/jupytext/issues/561))
- Test that notebooks paired through a configuration file are left unmodified ([#598](https://github.com/mwouts/jupytext/issues/598))
- Test that metadata filters in the configuration files are taken into account when using `jupytext --to` ([#543](https://github.com/mwouts/jupytext/issues/543))
- New argument `--run-path` to execute the notebooks at the desired location ([#595](https://github.com/mwouts/jupytext/issues/595))
- Activated GitHub code scanning alerts

**Changed**
- Jupytext now depends on `markdown-it-py` (Python 3.6 and above) and always features the MyST-Markdown format,
thanks to Chris Sewell ([#591](https://github.com/mwouts/jupytext/issues/591))
- The `md:myst` and `md:pandoc` are always included in the Jupytext formats, and an informative runtime
error will occur if the required dependencies, resp. `markdown-it-py` and `pandoc`, are not installed. ([#556](https://github.com/mwouts/jupytext/issues/556))
- The `# %%` cell marker has the same indentation as the first line in the cell ([#562](https://github.com/mwouts/jupytext/issues/562))
- Jupytext is now installed from source on MyBinder to avoid cache issues ([#567](https://github.com/mwouts/jupytext/issues/567))
- The tests that execute a notebook are now skipped on Windows to avoid timeout issues ([#489](https://github.com/mwouts/jupytext/issues/489))

**Fixed**
- Only scripts can have an encoding comment, not Markdown or R Markdown files ([#576](https://github.com/mwouts/jupytext/issues/576))
- Spaces in `--pipe` commands are supported ([#562](https://github.com/mwouts/jupytext/issues/562))
- Bash commands starting with special characters are now correctly detected, thanks to Aaron Gokaslan ([#587](https://github.com/mwouts/jupytext/issues/587))
- MyST Markdown files are recognized as such even if MyST-Markdown is not available ([#556](https://github.com/mwouts/jupytext/issues/556))
- Build JupyterLab with `dev-build=False` and `minimize=False` on mybinder to avoid build errors
- Configured coverage targets in `codecov.yml`


1.5.2 (2020-07-21)
------------------

**Changed**
- The documentation uses the Alabaster theme

**Fixed**
- Preserve indentation when commenting out magic commands ([#437](https://github.com/mwouts/jupytext/issues/437))
- Fixed MyBinder - `jupytext.py` is not a configuration file ([#559](https://github.com/mwouts/jupytext/issues/559), [#567](https://github.com/mwouts/jupytext/issues/567))


1.5.1 (2020-07-05)
------------------

**Fixed**
- Added `toml` as a dependency ([#552](https://github.com/mwouts/jupytext/issues/552)).
- Filtered out `__pycache__` and `.pyc` files from the pip package.
- Fixed coverage upload by adding `coverage` as a dependency to the conda CI workflow.
- Fixed the conda CI / Python 2.7 job by explicitly installing `backports.functools_lru_cache` ([#554](https://github.com/mwouts/jupytext/issues/554)).


1.5.0 (2020-06-07)
------------------

**Added**
- Jupytext can use a local or global [configuration file](https://github.com/mwouts/jupytext/blob/main/docs/config.md) ([#508](https://github.com/mwouts/jupytext/issues/508))
- Jupytext can pair notebooks in trees. Use e.g. `notebooks///ipynb,scripts///py:percent` if you want to replicate the tree of notebooks under `notebooks` in a folder named `scripts` ([#424](https://github.com/mwouts/jupytext/issues/424))
- The extension for Jupyter Notebook has a _New Text Notebook_ menu that creates text-only notebooks ([#443](https://github.com/mwouts/jupytext/issues/443))
- Groovy and Java are now supported, thanks to Przemek Wesołek ([#500](https://github.com/mwouts/jupytext/issues/500))
- The Coconut language is also supported, thanks to Thurston Sexton ([#532](https://github.com/mwouts/jupytext/issues/532))
- Resource files with `.resource` extension from the Robot Framework are supported, thanks to Hiski Valli ([#535](https://github.com/mwouts/jupytext/issues/535))
- Jupytext is tested in `pip` and `conda` environments, on Linux, Mac OS and Windows, using Github actions ([#487](https://github.com/mwouts/jupytext/issues/487))
- Jupytext uses pre-commit checks and automatic reformatting with `pre-commit`, `black` and `flake8` ([#483](https://github.com/mwouts/jupytext/issues/483))
- Documentation improvements:
  - Mention that the YAML header can be created with either `--set-kernel`, `--set-formats`, or both ([#485](https://github.com/mwouts/jupytext/issues/485))
  - Mention that one should use double quotes, not single quotes, around `jupytext --check` commands like `"pytest {}"` on Windows ([#475](https://github.com/mwouts/jupytext/issues/475))
  - Improved error message when a file is in a version that can't be read by Jupytext ([#531](https://github.com/mwouts/jupytext/issues/531))

**Fixed**
- Skip the `jupytext --execute` tests when the warning _Timeout waiting for IOPub output_ occurs, which is the case intermittently on Windows ([#489](https://github.com/mwouts/jupytext/issues/489))
- Fixed wrong paired paths when syncing with the --pre-commit flag ([#506](https://github.com/mwouts/jupytext/issues/506))


1.4.2 (2020-04-05)
------------------

**Added**
- Added an example with custom notebook metadata ([#469](https://github.com/mwouts/jupytext/issues/469))
- Added an example with custom cell tags ([#478](https://github.com/mwouts/jupytext/issues/478))

**Changed**
- The outputs from the `.ipynb` file are matched with the input cells from the text file with less strict rules. In this version, a search and replace on the text file will not remove the outputs any more ([#464](https://github.com/mwouts/jupytext/issues/464)).
- Update parsing of myst notebooks to new (markdown-it based) parser (please upgrade to `myst-parser` to version `~0.8`) ([#473](https://github.com/mwouts/jupytext/issues/473))
- Use `os.path.samefile` when searching for the kernel that corresponds to the current environment (`--set-kernel -`)

**Fixed**
- Fixed the CLI example for not commenting out magic commands: `--opt comment_magics=false`. In addition, most of the `jupytext` commands in `using-cli.md` are now tested! ([#465](https://github.com/mwouts/jupytext/issues/465))
- `jupytext.read` and `jupytext.write` now give more meaningful errors when the format information is incorrect ([#462](https://github.com/mwouts/jupytext/issues/462))
- Multiline comments starting or ending with quadruple quotes should not cause issues anymore ([#460](https://github.com/mwouts/jupytext/issues/460))
- Fixed active cells in the py:percent format ([#477](https://github.com/mwouts/jupytext/issues/477))

1.4.1 (2020-03-19)
------------------

**Added**
- Script of script (SoS) notebooks are now supported. Thanks to Thomas Pernet-coudrier for contributing the sample notebook ([#453](https://github.com/mwouts/jupytext/issues/453)).
- New MyST Markdown format (`md:myst`), developed by the [ExecutableBookProject](https://github.com/ExecutableBookProject) team. Read more about the MyST Markdown format in the [documentation](https://jupytext.readthedocs.io/en/latest/formats.html#myst-markdown). And many thanks to Chris Sewell for contributing the actual implementation! ([#447](https://github.com/mwouts/jupytext/issues/447) [#456](https://github.com/mwouts/jupytext/issues/456) [#458](https://github.com/mwouts/jupytext/issues/458))

**Fixed**
- When using `jupytext --pipe cmd`, the output of `cmd` should not appear in the terminal ([#432](https://github.com/mwouts/jupytext/issues/432))


1.4.0 (2020-03-09)
------------------

**Changed**
- The new jupyterlab extension (in version 1.2.0) is compatible with JupyterLab 2.0. Many thanks to Jean Helie! ([#449](https://github.com/mwouts/jupytext/issues/449))
- It is not compatible with JupyterLab 1.x anymore. If you wish, you can install manually the previous version of the extension with `jupyter labextension install jupyterlab-jupytext@1.1.1`.

**Fixed**
- Display the output/errors of command executed with `jupytext --pipe` or `jupytext --check` ([#432](https://github.com/mwouts/jupytext/issues/432))

1.3.5 (2020-03-08)
------------------

**Fixed**
- Removed leading slash in notebook paths ([#444](https://github.com/mwouts/jupytext/issues/444))
- Fixed `jupytext --set-formats` when using formats with prefix and/or suffix ([#450](https://github.com/mwouts/jupytext/issues/450))


1.3.4 (2020-02-18)
------------------

**Added**
- C# and F# Jupyter notebooks are now supported ([#427](https://github.com/mwouts/jupytext/issues/427), [#429](https://github.com/mwouts/jupytext/issues/429))

**Fixed**
- `jupytext --to script *.ipynb` now computes the script extension for each notebook ([#428](https://github.com/mwouts/jupytext/issues/428))
- Fix shebang handling for languages with non-# comments, by Jonas Bushart ([#434](https://github.com/mwouts/jupytext/issues/434))
- Indented bash commands are now commented out ([#437](https://github.com/mwouts/jupytext/issues/437))
- The main formats are documented in `jupytext --help` ([#426](https://github.com/mwouts/jupytext/issues/426), [#433](https://github.com/mwouts/jupytext/issues/433))


1.3.3 (2020-01-27)
------------------

**Added**
- Jupytext has a logo! Many thanks to Kyle Kelley for contributing the actual logo ([#423](https://github.com/mwouts/jupytext/issues/423)), and to Chris Holdgraf for suggesting this ([#260](https://github.com/mwouts/jupytext/issues/260)).
- Nested metadata filtering is now supported! You can use this to rid of `jupytext_version` if you wish ([#416](https://github.com/mwouts/jupytext/issues/416)).

**Fixed**
- Code cells in the Markdown format can contain triple backticks inside multiline strings ([#419](https://github.com/mwouts/jupytext/issues/419)).
- Changes in the YAML header when running `jupytext --test` on text files are ignored ([#414](https://github.com/mwouts/jupytext/issues/414)).

1.3.2 (2020-01-08)
------------------

**Fixed**
- The `--pre-commit` mode now ignores non-notebook files in the index ([#338](https://github.com/mwouts/jupytext/issues/338)).
- `nbformat_minor` is taken from the notebook with outputs When inputs and outputs are merged.

1.3.1 (2019-12-26)
------------------

**Added**
- New `nomarker` format in the Jupyter Notebook and JupyterLab extensions ([#397](https://github.com/mwouts/jupytext/issues/397))

**Changed**
- The `normarker` format replaces the one previously named `bare`.

**Fixed**
- Multiline strings are now accepted in the YAML header ([#404](https://github.com/mwouts/jupytext/issues/404)). Fix contributed by ZHUO Qiang ([#405](https://github.com/mwouts/jupytext/issues/405)).
- Fixed the instructions on how to use multiline comments for all Markdown cells in the py:percent format, by ZHUO Qiang  ([#403](https://github.com/mwouts/jupytext/issues/403)).
- Added `cd` to the list of magic commands.
- Do not read paired files when `--set-formats` is being used (fixes [#399](https://github.com/mwouts/jupytext/issues/399)).

1.3.0 (2019-11-23)
------------------

See also [What's new in Jupytext 1.3?](https://gist.github.com/mwouts/724efe5e00654fc2145a4c916796e071)

**Added**

- Pairing a notebook to both `.md` and `.py` is now supported. Input cells are loaded from the most recent text representation ([#290](https://github.com/mwouts/jupytext/issues/290))
- Both the Jupyter Notebook and the JupyterLab extension for Jupytext were updated ([#290](https://github.com/mwouts/jupytext/issues/290))
- Raw cells are now encoded using HTML comments (`<!-- #raw -->` and `<!-- #endraw -->`) in Markdown files ([#321](https://github.com/mwouts/jupytext/issues/321))
- Markdown cells can be delimited with any of `<!-- #region -->`,  `<!-- #markdown -->` or `<!-- #md -->` ([#344](https://github.com/mwouts/jupytext/issues/344))
- Code blocks from Markdown files, when they don't have an explicit language, appear in Markdown cells in Jupyter ([#321](https://github.com/mwouts/jupytext/issues/321))
- Code blocks with an explicit language and a `.noeval` attribute are inactive in Jupyter ([#347](https://github.com/mwouts/jupytext/issues/347))
- Markdown and raw cells can be quoted with triple quotes in the `py:percent` format. And Markdown cells can start with just `# %% [md]` ([#305](https://github.com/mwouts/jupytext/issues/305))
- The light format uses `# + [markdown]` rather than the previous `cell_type` metadata to identify markdown cells with metadata ([#356](https://github.com/mwouts/jupytext/issues/356))
- Explicit Markdown cells in the light format `# + [markdown]` can use triple quotes ([#356](https://github.com/mwouts/jupytext/issues/356))
- IPython magic help commands like `float?` are classified as magics, and thus commented in Python scripts ([#297](https://github.com/mwouts/jupytext/issues/297))
- Cell metadata can be encoded as either `key=value` (the new default) or in JSON. An automatic option `cell_metadata_json` should help minimize the impact on existing files ([#344](https://github.com/mwouts/jupytext/issues/344))
- R Markdown hidden inputs, outputs, or cells are now mapped to the corresponding Jupyter Book tags by default ([#337](https://github.com/mwouts/jupytext/issues/337))
- The notebook metadata filter is automatically updated when extra keys are added to the YAML header ([#376](https://github.com/mwouts/jupytext/issues/376))
- The Jupyter Notebook extension for Jupytext is compatible with Jupyter Notebook 6.0 ([#346](https://github.com/mwouts/jupytext/issues/346))
- `jupytext notebook.py --to ipynb` updates the timestamp of `notebook.py` so that the paired notebook still works in Jupyter ([#335](https://github.com/mwouts/jupytext/issues/335), [#254](https://github.com/mwouts/jupytext/issues/254))
- `jupytext --check pytest notebook.ipynb` can be used to run test functions in a notebook ([#286](https://github.com/mwouts/jupytext/issues/286))
- `jupytext --check` and `jupytext --pipe` can run commands that only operate on files: when `{}` is found in the text of the command, `jupytext` saves the text representation of the notebook in a temp file, and replaces `{}` with the name of that file before executing the command. ([#286](https://github.com/mwouts/jupytext/issues/286))
- Documented how to sync notebooks in a pre-commit hook ([#338](https://github.com/mwouts/jupytext/issues/338))
- Added support for Rust/Evxcr, by Jonas Bushart ([#351](https://github.com/mwouts/jupytext/issues/351))
- Added support for [Robot Framework](https://robots-from-jupyter.github.io/), by Asko Soukka ([#378](https://github.com/mwouts/jupytext/issues/378))
- Added support for PowerShell ([#349](https://github.com/mwouts/jupytext/issues/349))

**Changed**

- Use `CHANGELOG.md` rather than `HISTORY.rst`

**Fixed**

- Commands like `cat = x` are not magic commands, so they are not commented any more ([#339](https://github.com/mwouts/jupytext/issues/339))
- Fixed an inconsistent round trip (code cell with `"cat"` being converted to a markdown cell) in the `py:light` format ([#339](https://github.com/mwouts/jupytext/issues/339))
- `jupytext --test textfile.ext` now really compares the text file to its round trip (rather than the corresponding notebook) ([#339](https://github.com/mwouts/jupytext/issues/339))
- Markdown cells that contain code are now preserved in a round trip through the Markdown and R Markdown formats ([#361](https://github.com/mwouts/jupytext/issues/361))
- Code cells with a `%%python3` cell magic are now preserved in a round trip through the Markdown format ([#365](https://github.com/mwouts/jupytext/issues/365))
- `jupytext --execute` runs the notebook in its folder ([#382](https://github.com/mwouts/jupytext/issues/382))
- Strings in the metadata of code cells are quoted in the Rmd representation. And we escape R code in chunk options with `#R_CODE#` ([#383](https://github.com/mwouts/jupytext/issues/383))

1.2.4 (2019-09-19)
------------------

**Added**

- The documentation includes a mention on how to set metadata filters at the command line ([#330](https://github.com/mwouts/jupytext/issues/330))
- Jupytext will not catch any error when the flag `--warn-only` is not set ([#327](https://github.com/mwouts/jupytext/issues/327))

**Fixed**

- Now the flag `--warn-only` catches every possible error ([#263](https://github.com/mwouts/jupytext/issues/263))
- `.md` and `.markdown` files are treated identically ([#325](https://github.com/mwouts/jupytext/issues/325))
- Fixed `--set-kernel` when using pipes ([#326](https://github.com/mwouts/jupytext/issues/326))
- Fixed utf-8 encoding on stdout on Python 2 ([#331](https://github.com/mwouts/jupytext/issues/331))


1.2.3 (2019-09-02)
------------------

**Fixed**

- Dependency on `setuptools` in `pandoc.py` made optional to fix the build of the conda package ([#310](https://github.com/mwouts/jupytext/issues/310), [#323](https://github.com/mwouts/jupytext/issues/323))


1.2.2 (2019-09-01)
------------------

**Added**

- Documentation includes a section on how to use Jupytext as a Python library ([#317](https://github.com/mwouts/jupytext/issues/317))
- Mention of the server extension in the documentation ([#304](https://github.com/mwouts/jupytext/issues/304))
- Text notebooks can be tested with `jupytext --execute notebook.md` ([#303](https://github.com/mwouts/jupytext/issues/303))
- The default value of `as_version` in `jupytext.read` is `nbformat.NO_CONVERT`, as for `nbformat.read`
- Jupytext tests are now included in sdist ([#310](https://github.com/mwouts/jupytext/issues/310))

**Fixed**

- Fixed the usability of the `fmt` argument in `jupytext.read` ([#312](https://github.com/mwouts/jupytext/issues/312))
- Fixed the download notebook error when `c.notebook_extensions` has a custom value ([#318](https://github.com/mwouts/jupytext/issues/318))
- String delimiters in commented text are now ignored ([#307](https://github.com/mwouts/jupytext/issues/307))


1.2.1 (2019-07-20)
------------------

**Added**

- Added documentation on how to use Jupytext with JupyterLab 0.35 ([#299](https://github.com/mwouts/jupytext/issues/299))
- and on using Jupytext with the pre-commit package manager ([#292](https://github.com/mwouts/jupytext/issues/292))
- The `read` and `write` functions are easier to use ([#292](https://github.com/mwouts/jupytext/issues/292))

**Fixed**

- Jupytext now ships the `jupyterlab-jupytext` extension in version 1.0.2. The version 1.0.1 erroneously introduces a `target_formats` metadata in the jupytext section, instead of `formats`, and works only after two clicks.


1.2.0 (2019-07-18)
------------------

**Added**

- New `--execute` option in Jupytext CLI ([#231](https://github.com/mwouts/jupytext/issues/231))
- The `--set-formats` option in Jupytext CLI also triggers `--sync`, allowing shorter commands.
- `jupytext`'s `read` and `write` functions can be used as drop-in replacements for `nbformat`'s ones ([#262](https://github.com/mwouts/jupytext/issues/262)).
- `jupytext --sync` will now skip unpaired notebooks ([#281](https://github.com/mwouts/jupytext/issues/281)).
- The JupyterLab extension was updated. It now works on text files ([#213](https://github.com/mwouts/jupytext/issues/213)) and has a new option to include
(or not) the metadata in the text representation of the notebook.
- Jupytext's contents manager class is derived dynamically from the default CM class for compatibility with
`jupyter_server` ([#270](https://github.com/mwouts/jupytext/issues/270))
- Removed dependency on `mock` and `testfixtures`, thanks to Jean-Sebastien Dieu ([#279](https://github.com/mwouts/jupytext/issues/279))
- Added support for `.markdown` extension ([#288](https://github.com/mwouts/jupytext/issues/288))

**Fixed**

- The `jupyterlab-jupytext` extension shipped with the python package is in version 1.0.1, and is compatible only
with JupyterLab >= 1.0. If you use an earlier version of JupyterLab, please install the version 0.19 of the extension
with `jupyter labextension install jupyterlab-jupytext@0.19` ([#276](https://github.com/mwouts/jupytext/issues/276), [#278](https://github.com/mwouts/jupytext/issues/278))
- Text files can be unpaired ([#289](https://github.com/mwouts/jupytext/issues/289))


1.1.7 (2019-06-23)
------------------

**Added**

- Added support for Scala notebook, by Tobias Frischholz ([#253](https://github.com/mwouts/jupytext/issues/253))
- Added a getting started notebook for jupytext (and Binder), by Chris Holdgraf ([#257](https://github.com/mwouts/jupytext/issues/257))
- The Markdown and R Markdown representations are now tested for all the languages
- The Jupytext notebook extension also works when the notebook is a text file ([#213](https://github.com/mwouts/jupytext/issues/213))


**Fixed**

- The Jupytext Menu in Jupyter Notebook is now compatible with `jupyter_nbextensions_configurator` ([#178](https://github.com/mwouts/jupytext/issues/178))
- Entries in the Jupytext menu are updated when the menu is hovered on ([#248](https://github.com/mwouts/jupytext/issues/248))
- Fixed link to `.md` files in the documentation ([#255](https://github.com/mwouts/jupytext/issues/255))


1.1.6 (2019-06-11)
------------------

**Added**

- Jupytext now supports Javascript and Typescript, thanks to Hatem Hosny ([#250](https://github.com/mwouts/jupytext/issues/250))
- Jupytext works with Python 3.8 as well

**Fixed**

- Fix global `auto` pairing ([#249](https://github.com/mwouts/jupytext/issues/249))


1.1.5 (2019-06-06)
------------------

**Fixed**

- Fixed implicit dependency on `jupyter_client` ([#245](https://github.com/mwouts/jupytext/issues/245))


1.1.4 (2019-06-05)
------------------

**Added**

- New argument `--set-kernel` in Jupytext command line ([#230](https://github.com/mwouts/jupytext/issues/230))
- Jupytext now accepts `--to script` or `--to auto` ([#240](https://github.com/mwouts/jupytext/issues/240))
- Jupytext now has a real Sphinx documentation on [readthedocs](https://jupytext.readthedocs.io/en/latest), thanks to Chris Holdgraf ([#237](https://github.com/mwouts/jupytext/issues/237))

**Fixed**

- Invalid notebooks may cause a warning, but not a fatal error ([#234](https://github.com/mwouts/jupytext/issues/234))
- Jupyter server extension leaves the contents manager unchanged if it is a sub-class of Jupytext's CM ([#236](https://github.com/mwouts/jupytext/issues/236))
- Fixed format inference when metadata is present but not format information ([#239](https://github.com/mwouts/jupytext/issues/239))
- Preserve executable and encoding information in scripts with metadata ([#241](https://github.com/mwouts/jupytext/issues/241))

1.1.3 (2019-05-22)
------------------

**Added**

- Support for IDL notebooks and .pro scripts ([#232](https://github.com/mwouts/jupytext/issues/232))


1.1.2 (2019-05-16)
------------------

**Added**

- Jupytext's content manager has a new `notebook_extensions` option ([#224](https://github.com/mwouts/jupytext/issues/224), [#183](https://github.com/mwouts/jupytext/issues/183))
- Cells can be made inactive in scripts with the `active-ipynb` cell tag ([#226](https://github.com/mwouts/jupytext/issues/226))

**Fixed**

- Directories ending in .jl (or .ipynb) are not notebooks ([#228](https://github.com/mwouts/jupytext/issues/228))
- Empty notebooks have no language ([#227](https://github.com/mwouts/jupytext/issues/227))


1.1.1 (2019-04-16)
------------------

**Added**

- Jupytext server extension leaves the contents manager unchanged when it is already a subclass of TextFileContentsManager ([#218](https://github.com/mwouts/jupytext/issues/218))
- The base class for TextFileContentsManager defaults to FileContentsManager when LargeFileManager is not available ([#217](https://github.com/mwouts/jupytext/issues/217))


1.1.0 (2019-04-14)
------------------

**Added**

- Markdown and R Markdown formats now support metadata ([#66](https://github.com/mwouts/jupytext/issues/66), [#111](https://github.com/mwouts/jupytext/issues/111), [#188](https://github.com/mwouts/jupytext/issues/188))
- The `light` format for Scripts can use custom cell markers, e.g. Vim or VScode/PyCharm folding markers ([#199](https://github.com/mwouts/jupytext/issues/199))
- Pandoc's Markdown format for Jupyter notebooks is available in Jupytext as `md:pandoc` ([#208](https://github.com/mwouts/jupytext/issues/208))

**Fixed**

- Jupytext's contents manager is now based on `LargeFileManager` to allow large file uploads ([#210](https://github.com/mwouts/jupytext/issues/210))
- YAML header parsed with yaml.safe_load rather than yaml.load ([#215](https://github.com/mwouts/jupytext/issues/215))
- IPython line magic can be split across lines ([#209](https://github.com/mwouts/jupytext/issues/209))
- `jupytext --to py` rather than `--to python` in the README ([#216](https://github.com/mwouts/jupytext/issues/216))


1.0.5 (2019-03-26)
------------------

**Fixed**

- Fix the error 'notebook file has changed on disk' when saving large notebooks ([#207](https://github.com/mwouts/jupytext/issues/207))


1.0.4 (2019-03-20)
------------------

**Added**

- Wildcard are now supported on Windows ([#202](https://github.com/mwouts/jupytext/issues/202))
- Trusted notebooks remain trusted when inputs cells are modified ([#203](https://github.com/mwouts/jupytext/issues/203))

**Fixed**

- Pre-commit mode adds the result of conversion to the commit ([#200](https://github.com/mwouts/jupytext/issues/200))


1.0.3 (2019-03-13)
------------------

**Added**

- Matlab and Octave notebooks and scripts are now supported ([#197](https://github.com/mwouts/jupytext/issues/197))

**Fixed**

- `notebook_metadata_filter = "all"` now works ([#196](https://github.com/mwouts/jupytext/issues/196))
- Default pairing in subfolders fixed in JupyterLab ([#180](https://github.com/mwouts/jupytext/issues/180))


1.0.2 (2019-02-27)
------------------

**Added**

- Rename notebooks in pairs in the tree view ([#190](https://github.com/mwouts/jupytext/issues/190))
- Associate `.scm` file extension with Scheme scripts ([#192](https://github.com/mwouts/jupytext/issues/192))
- Added support for Clojure, by bzinberg ([#193](https://github.com/mwouts/jupytext/issues/193))

**Fixed**

- Allow spaces between `?` or `!` and python or bash command ([#189](https://github.com/mwouts/jupytext/issues/189))


1.0.1 (2019-02-23)
------------------

**Fixed**

- Exclude tests in package deployment ([#184](https://github.com/mwouts/jupytext/issues/184))
- Jupytext's serverextension only runs selected init steps ([#185](https://github.com/mwouts/jupytext/issues/185))
- Added an additional test for magic arguments ([#111](https://github.com/mwouts/jupytext/issues/111))

1.0.0 (2019-02-19)
------------------

**Added**

- Jupytext now includes a Jupyter Notebook extension and a JupyterLab extension ([#86](https://github.com/mwouts/jupytext/issues/86)).
- Jupytext command line has more arguments: `--paired-paths` to list the paths for the paired representations of the notebook, and `--sync` to synchronise the content of all paired paths based on the most recent file ([#146](https://github.com/mwouts/jupytext/issues/146)). In addition, the `--from` argument is optional even when the notebook is read from stdin ([#148](https://github.com/mwouts/jupytext/issues/148)).
- The pairing information, and more generally the notebook metadata can be edited with the CLL, see the `--set-formats` and the `--update-metadata` arguments ([#141](https://github.com/mwouts/jupytext/issues/141)).
- Jupytext can `--pipe` the text representation of a notebook to external programs like `black` or `flake8` ([#154](https://github.com/mwouts/jupytext/issues/154), [#142](https://github.com/mwouts/jupytext/issues/142))
- The Python representation of notebooks containing PEP8 cells is now expected to be PEP8 compliant ([#154](https://github.com/mwouts/jupytext/issues/154)).
- Format specification allow prefix and suffix for path and file name ([#138](https://github.com/mwouts/jupytext/issues/138), [#142](https://github.com/mwouts/jupytext/issues/142)). Use `ipynb,prefix/suffix.py:percent` to pair the current notebook named `notebook.ipynb` to a script named `prefixnotebooksuffix.py`. Suffix and prefix can also be configured on the `ipynb` file, with the same syntax.
- Introducing a new `hydrogen` format for scripts, which derives from `percent`. In that format Jupyter magic commands are not commented ([#59](https://github.com/mwouts/jupytext/issues/59), [#126](https://github.com/mwouts/jupytext/issues/126), [#132](https://github.com/mwouts/jupytext/issues/132)).
- Introducing a new `bare` format for scripts, which derives from `light`. That format has no cell marker. Use a notebook metadata filter `{"jupytext": {"notebook_metadata_filter":"-all"}}` if you want no YAML header ([#152](https://github.com/mwouts/jupytext/issues/152)).
- The default format for R script is now `light`, as for the other languages.
- Added support for q/kdb+ notebooks ([#161](https://github.com/mwouts/jupytext/issues/161)).
- Python scripts or Markdown documents that have no Jupyter metadata receive a metadata filter that ensures that metadata is not exported back to the text representation ([#124](https://github.com/mwouts/jupytext/issues/124)).
- Metadata filters are represented as strings rather than dictionaries to make YAML headers shorter. Previous syntax from [#105](https://github.com/mwouts/jupytext/issues/105) is still supported. They were also renamed to `notebook_metadata_filter` and `cell_metadata_filter`.
- Markdown and RMarkdown formats have a new option `split_at_heading` to split Markdown cells at heading ([#130](https://github.com/mwouts/jupytext/issues/130))

**Fixed**

- Main language of scripts is inferred from script extension. Fixes a round trip conversion issue for Python notebooks with a Javascript cell.
- Non-Python scripts opened as notebooks in Jupyter are now correctly saved even when no matching kernel is found.
- Jupyter magic commands like `ls` are commented in the light and R markdown format ([#149](https://github.com/mwouts/jupytext/issues/149)).
- Cell starting with `%%html`, `%%latex` are now commented out in the `light`, `percent` and `Rmd` formats ([#179](https://github.com/mwouts/jupytext/issues/179)).

0.8.6 (2018-11-29)
------------------

**Added**

- The `language_info` section is not part of the default header any more. Language information is now taken from metadata `kernelspec.language`. ([#105](https://github.com/mwouts/jupytext/issues/105)).
- When opening a paired notebook, the active file is now the file that was originally opened ([#118](https://github.com/mwouts/jupytext/issues/118)). When saving a notebook, timestamps of all the alternative representations are tested to ensure that Jupyter's autosave does not override manual modifications.
- Jupyter magic commands are now commented per default in the `percent` format ([#126](https://github.com/mwouts/jupytext/issues/126), [#132](https://github.com/mwouts/jupytext/issues/132)). Version for the `percent` format increases from '1.1' to '1.2'. Set an option `comment_magics` to `false` either per notebook, or globally on Jupytext's contents manager, or on `jupytext`'s command line, if you prefer not to comment Jupyter magics.
- Jupytext command line has a pre-commit mode ([#121](https://github.com/mwouts/jupytext/issues/121)).


0.8.5 (2018-11-13)
------------------

**Added**

- `bash` scripts as notebooks ([#127](https://github.com/mwouts/jupytext/issues/127))
- R scripts with `.r` extension are supported ([#122](https://github.com/mwouts/jupytext/issues/122))
- Jupytext selects the first kernel that matches the language ([#120](https://github.com/mwouts/jupytext/issues/120))

0.8.4 (2018-10-29)
------------------

**Added**

- Notebook metadata is filtered - only the most common metadata are stored in the text representation ([#105](https://github.com/mwouts/jupytext/issues/105))
- New config option `freeze_metadata` on the content manager and on the command line interface (defaults to `False`). Use this option to avoid creating a YAML header or cell metadata if there was none initially. ([#110](https://github.com/mwouts/jupytext/issues/110))
- Language magic arguments are preserved in R Markdown, and also supported in `light` and `percent` scripts ([#111](https://github.com/mwouts/jupytext/issues/111), [#114](https://github.com/mwouts/jupytext/issues/114), [#115](https://github.com/mwouts/jupytext/issues/115))
- First markdown cell exported as a docstring when using the Sphinx format ([#107](https://github.com/mwouts/jupytext/issues/107))

0.8.3 (2018-10-19)
------------------

**Added**

- Frozen cells are supported in R Markdown, light and percent scripts ([#101](https://github.com/mwouts/jupytext/issues/101))
- Inactive cells extended to percent scripts ([#108](https://github.com/mwouts/jupytext/issues/108))
- `jupytext` gains a `--version` argument ([#103](https://github.com/mwouts/jupytext/issues/103))
- "ExecuteTime" cell metadata is not included in the text representation anymore ([#106](https://github.com/mwouts/jupytext/issues/106))


0.8.2 (2018-10-15)
------------------

**Added**

- Round trip conversion testing with `jupytext --test` was improved ([#99](https://github.com/mwouts/jupytext/issues/99))
- Round trip conversion tested on Jake Vanderplas' Python for Data Science Handbook.

**Fixed**

- Nested lists and dictionaries are now supported in notebook metadata
- Final empty code cell supported in Sphinx representation

0.8.1 (2018-10-11)
------------------

**Fixed**

- Sphinx format tested on `World population` notebook ([#97](https://github.com/mwouts/jupytext/issues/97))
- Mirror test made stronger on this occasion!
- Markdown representation recognize Julia, Scheme and C++ code cells as such
- Light representation of Scheme and C++ notebooks fixed ([#61](https://github.com/mwouts/jupytext/issues/61))

0.8.0 (2018-10-10)
------------------

**Added**

- All `jupytext` related metadata goes to a `jupytext` section ([#91](https://github.com/mwouts/jupytext/issues/91)). Please make sure your collaborators use the same version of Jupytext, as the new version can read previous metadata, but not the opposite.
- Notebooks extensions can be prefixed with any prefix of at most three chars ([#87](https://github.com/mwouts/jupytext/issues/87)).
- Export of the same notebook to multiple formats is now supported. To export to all python formats, plus `.ipynb` and `.md`, use `"jupytext": {"formats": "ipynb,pct.py:percent,lgt.py:light,spx.py:sphinx,md"},`.
- README includes a short section on how to extend `light` and `percent` formats to more languages ([#61](https://github.com/mwouts/jupytext/issues/61)).
- Jupytext's contents manager accepts the `auto` extension in `default_jupytext_formats` ([#93](https://github.com/mwouts/jupytext/issues/93)).
- All Jupyter magics are escaped in `light` scripts and R markdown documents. Escape magics in other formats with a `comment_magics` metadata (true or false), or with the contents manager `comment_magics` global flag ([#94](https://github.com/mwouts/jupytext/issues/94)).

**Fixed**

- Trusting notebooks made functional again.
- Command line `jupytext` returns a meaningful error when no argument is given.
- Fixed global pairing configuration ([#95](https://github.com/mwouts/jupytext/issues/95)).

0.7.2 (2018-10-01)
------------------

**Added**

- `light` and `percent` formats made available for scheme and cpp notebooks. Adding more formats is straightforward - just add a new entry to _SCRIPT_EXTENSIONS in languages.py, a sample notebook and a mirror test ([#61](https://github.com/mwouts/jupytext/issues/61))
- Format name is automatically appended to extension in `jupytext_formats` when notebook is loaded/saved.

**Fixed**

- Notebooks extensions can only be prefixed with `.nb` ([#87](https://github.com/mwouts/jupytext/issues/87))


0.7.1 (2018-09-24)
------------------

**Fixed**

- Markdown cells header in sphinx gallery format may have a space between first # and following.

0.7.0 (2018-09-23)
------------------

**Added**

- Header for cells in `percent` format is more robust: use `[markdown]` and `[raw]` to identify cell types. Cell type comes after the cell title. ([#59](https://github.com/mwouts/jupytext/issues/59))
- Jupytext can read and write notebooks as Hydrogen/VScode/Spyder/PyCharm compatible scripts (cells starting with `# %%`) ([#59](https://github.com/mwouts/jupytext/issues/59))
- Jupytext can read and write notebooks as Sphinx-gallery compatible scripts ([#80](https://github.com/mwouts/jupytext/issues/80))
- Metadata are supported for all cell types in light python and percent formats ([#66](https://github.com/mwouts/jupytext/issues/66)). Due to this, light python format version is now 1.3. Light python notebooks in versions 1.1 and 1.2 are still readable.
- Command line `jupytext` has a `from` argument, and now accepts notebook from the standard input.

**Fixed**

- Fix merging of input and output notebooks ([#83](https://github.com/mwouts/jupytext/issues/83))
- Removed extra new line on stdout in command line `jupytext` ([#84](https://github.com/mwouts/jupytext/issues/84))

0.6.5 (2018-09-13)
------------------

**Added**

- Code lines that start with a quotation mark in Jupyter are commented in the corresponding Python and Julia scripts ([#73](https://github.com/mwouts/jupytext/issues/73))
- Update pypy, add flake8 tests on Travis CI ([#74](https://github.com/mwouts/jupytext/issues/74))

**Fixed**

- Import notebook.transutils before notebook.services.contents.filemanager ([#75](https://github.com/mwouts/jupytext/issues/75))

0.6.4 (2018-09-12)
------------------

**Added**

- Jupytext will not load paired notebook when text representation is out of date ([#63](https://github.com/mwouts/jupytext/issues/63))
- Package tested against Python 3.7 ([#68](https://github.com/mwouts/jupytext/issues/68))

**Fixed**

- Allow unicode characters in notebook path ([#70](https://github.com/mwouts/jupytext/issues/70))
- Read README.md as unicode in `setup.py` ([#71](https://github.com/mwouts/jupytext/issues/71))

0.6.3 (2018-09-07)
------------------

**Added**

- Lighter cell markers for Python and Julia scripts ([#57](https://github.com/mwouts/jupytext/issues/57)). Corresponding file format version at 1.2. Scripts in previous version 1.1 can still be opened.
- New screenshots for the README.

**Fixed**

- Command line conversion tool `jupytext` fixed on Python 2.7 ([#46](https://github.com/mwouts/jupytext/issues/46))

0.6.2 (2018-09-05)
------------------

**Added**

- Initial support for Jupyter notebooks as Julia scripts ([#56](https://github.com/mwouts/jupytext/issues/56))
- Command line conversion tool `jupytext` has explicit `to` and `output` options ([#46](https://github.com/mwouts/jupytext/issues/46))
- Round trip test with `jupytext --test` improved ([#54](https://github.com/mwouts/jupytext/issues/54))
- Improved README ([#51](https://github.com/mwouts/jupytext/issues/51))


**Fixed**

- testfixtures now in requirements ([#55](https://github.com/mwouts/jupytext/issues/55))
- Empty code cells are now preserved ([#53](https://github.com/mwouts/jupytext/issues/53))

0.6.1 (2018-08-31)
------------------

**Added**

- Package and conversion script renamed from `nbrmd` to `jupytext`.

0.6.0 (2018-08-31)
------------------

**Added**

- Cell parsing and exporting done in two specialized classes. This is way easier to read. Pylint score at 9.9 !
- Python file format updated to 1.1: default end of cell for python scripts is one blank space. Two blank spaces are allowed as well. Now you can reformat code in Python IDE without breaking notebook cells ([#38](https://github.com/mwouts/jupytext/issues/38)).
- Added support for plain markdown files ([#40](https://github.com/mwouts/jupytext/issues/40), [#44](https://github.com/mwouts/jupytext/issues/44)).
- Demonstration notebooks more user friendly ([#45](https://github.com/mwouts/jupytext/issues/45)).
- Command line tool simpler to use ([#46](https://github.com/mwouts/jupytext/issues/46)).
- Start code patterns present in Jupyter cells are escaped.
- Default `nbrmd_format` is empty (mwouts/nbsrc/[#5](https://github.com/mwouts/jupytext/issues/5)): no Jupyter notebook is created on disk when the user opens a Python or R file and saves it from Jupyter, unless the users asks for it by setting `nbrmd_format`.

**Fixed**

- Fixed message in the `nbsrc` script ([#43](https://github.com/mwouts/jupytext/issues/43))
- Technical metadata don't appear any more in scripts unless required ([#42](https://github.com/mwouts/jupytext/issues/42))
- Code cells that are fully commented remain code cells after round trip ([#41](https://github.com/mwouts/jupytext/issues/41))

0.5.4 (2018-08-24)
------------------

**Added**

- R to Rmd conversion compares well to knitr::spin ([#26](https://github.com/mwouts/jupytext/issues/26))
- Increased coverage to 98%


0.5.3 (2018-08-22)
------------------

**Fixed**

- Read and write version to the same metadata ([#36](https://github.com/mwouts/jupytext/issues/36))


0.5.2 (2018-08-22)
------------------

**Added**

- Classical jupyter extensions (autoreload, rmagics) are also escaped ([#35](https://github.com/mwouts/jupytext/issues/35))
- Explicit file format version, set at 1.0, to avoid overriding ipynb files by accident ([#36](https://github.com/mwouts/jupytext/issues/36))


0.5.1 (2018-08-21)
------------------

**Fixed**

- Source only notebooks can be trusted.

0.5.0 (2018-08-21)
------------------

**Added**

- Jupyter magic commands escaped when exported ([#29](https://github.com/mwouts/jupytext/issues/29))
- 'endofcell' option for explicit (optional) end-of-cell marker ([#31](https://github.com/mwouts/jupytext/issues/31))
- 'active' cell option now supported for .py and .R export ([#30](https://github.com/mwouts/jupytext/issues/30))
- Raw cells now preserved when exported to .py or .R ([#32](https://github.com/mwouts/jupytext/issues/32))
- Extensions can be prefixed, like `.nb.py`, (mwouts/nbsrc[#5](https://github.com/mwouts/jupytext/issues/5))
- When a file with an extension not associated to 'ipynb' is opened and saved, no 'ipynb' file is created (mwouts/nbsrc[#5](https://github.com/mwouts/jupytext/issues/5))
- Extensions can now be a sequence of groups. For instance, `nbrmd_formats="ipynb,nb.py;script.ipynb,py"` will create an `ipynb` file when a `nb.py` is opened (and conversely), and a `script.ipynb` file when a `py` file is opened (mwouts/nbsrc[#5](https://github.com/mwouts/jupytext/issues/5))
- `nbsrc` script was moved to the `nbrmd` package. The `nbsrc` package now only contains the documentation (mwouts/nbsrc[#3](https://github.com/mwouts/jupytext/issues/3))


0.4.6 (2018-07-26)
------------------

- Ping pypi - previous version still not available


0.4.5 (2018-07-26)
------------------

**Fixed**

- Removed dependency of `setup.py` on `yaml`

0.4.4 (2018-07-26)
-------------------

**Fixed**

- Package republished with `python setup.py sdist bdist_wheel` to fix missing dependencies

0.4.3 (2018-07-26)
------------------

**Added**

- Multiline comments now supported [#25](https://github.com/mwouts/jupytext/issues/25)
- Readme refactored, notebook demos available on binder [#23](https://github.com/mwouts/jupytext/issues/23)

**Fixed**

- ContentsManager can be imported even if `notebook.transutils` is not available, for compatibility with older python distributions.
- Fixed missing cell metadata [#27](https://github.com/mwouts/jupytext/issues/27)
- Documentation tells how to avoid creating `.ipynb` files [#16](https://github.com/mwouts/jupytext/issues/16)

0.4.2 (2018-07-23)
------------------

**Added**

- Added test for R notebooks
- Added pylint badge, imports now in correct order
- New `active` cell metadata that allows cell activation only for desired extensions (currently available for Rmd and ipynb extensions only)

0.4.1 (2018-07-20)
------------------

**Fixed**

- Indented python code will not start a new cell [#20](https://github.com/mwouts/jupytext/issues/20)
- Fixed parsing of Rmd cell metadata [#21](https://github.com/mwouts/jupytext/issues/21)

0.4.0 (2018-07-18)
------------------

**Added**

- `.py` format for notebooks is lighter and pep8 compliant

**Fixed**

- Default nbrmd config not added to notebooks ([#17](https://github.com/mwouts/jupytext/issues/17))
- `nbrmd_formats` becomes a configurable traits ([#16](https://github.com/mwouts/jupytext/issues/16))
- Removed `nbrmd_sourceonly_format` metadata. Source notebook is current notebook when not `.ipynb`, otherwise the first notebook format in `nbrmd_formats` (not `.ipynb`) that is found on disk

0.3.0 (2018-07-17)
------------------

**Added**

- Introducing support for notebooks as python `.py` or R scripts `.R`

0.2.6 (2018-07-13)
------------------

**Added**

- Introduced `nbrmd_sourceonly_format` metadata
- Inputs are loaded from `.Rmd` file when a matching `.ipynb` file is opened.

**Fixed**

- Trusted notebooks remain trusted ([#12](https://github.com/mwouts/jupytext/issues/12))

0.2.5 (2018-07-11)
------------------

**Added**

- Outputs of existing `.ipynb` versions are combined with matching inputs of R markdown version, as suggested by @grst ([#12](https://github.com/mwouts/jupytext/issues/12))

**Fixed**

- Support for unicode text in python 2.7 ([#11](https://github.com/mwouts/jupytext/issues/11))


0.2.4 (2018-07-05)
------------------

**Added**

- nbrmd will always open notebooks, even if header of code cells are not terminated. Merge conflicts can thus be solved in Jupyter directly.
- New metadata 'main language' that preserves the notebook language.

**Fixed**

- dependencies included in `setup.py`
- pre_save_hook work with non-empty `notebook_dir` ([#9](https://github.com/mwouts/jupytext/issues/9))

0.2.3 (2018-06-28)
------------------

**Added**

- Screenshots in README

**Fixed**

- RMarkdown exporter for nbconvert fixed on non-recent python
- Tests compatible with other revisions of nbformat >= 4.0
- Tests compatible with older pytest versions


0.2.2 (2018-06-28)
-------------------

**Added**

- RMarkdown exporter for nbconvert
- Parsing of R options robust to parenthesis
- Jupyter cell tags are preserved

**Fixed**

- requirements.txt now included in pypi packages

0.2.1 (2018-06-24)
------------------

**Added**

- Support for editing markdown files in Jupyter
- New pre-save hook `update_selected_formats` that saves to formats in metadata 'nbrmd_formats'
- Rmd cell options directly mapped to cell metadata

**Fixed**

- ContentManager compatible with Python 2.7

0.2.0 (2018-06-21)
------------------

**Added**

- The package provides a `RmdFileContentsManager` for direct edit of R markdown files in Jupyter
- Notebook metadata and cell options are preserved


0.1.1 (2018-06-19)
------------------

**Added**

- `nbrmd` prints the result of conversion to stdout, unless flag `-i` is provided
- Notebooks with R code chunks are supported

0.1 (2018-06-18)
----------------

- Initial version with the `nbrmd` converter and Jupyter `pre_save_hook`
