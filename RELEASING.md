# Releasing

`pyproject.toml` defines the package version. Release tags use `v<version>` (for example, `v0.1.0`). The [Release workflow](.github/workflows/release.yml) accepts published, stable releases whose tag matches that version and whose commit is on `main`. It runs Ruff, mypy, tests, and artifact checks before publishing the wheel and source distribution to PyPI.

## Each release

1. Set the new version in `pyproject.toml` and `CITATION.cff`, and prepare its `CHANGELOG.md` section. Confirm that the version is unused on PyPI.
2. Merge the release changes into `dev`, then `main`, with passing CI on both pull requests. Confirm the version and changelog on `main`.
3. In GitHub **Releases > Draft a new release**, create `v<version>` at the release commit on `main`. Use the changelog section as release notes, leave **pre-release** off, and publish the release. A draft does not trigger the upload.
4. Confirm that both `build` and `publish` passed in **Actions > Release**. Check that PyPI has the wheel and source distribution, then install the pinned version and import `causaleffect` in a clean supported Python environment outside this checkout. Confirm the [API site](https://pedemonte96.github.io/causaleffect/causaleffect.html) deployed from `main`.

PyPI does not replace uploaded files. Use a new version for a correction. The existing [0.0.2 release](https://pypi.org/project/causaleffect/0.0.2/) remains the option for Python 3.7-3.10.
