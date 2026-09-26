# Changelog

## 0.1.0

### Changed

- Require Python 3.11 or newer; PyPI 0.0.2 supported Python 3.7 or newer.
- Move all package metadata and dependencies to `pyproject.toml`, with an optional plotting extra.
- Depend on `igraph` directly without requiring NumPy.

### Added

- Type annotations, a `py.typed` marker, regression coverage, Ruff and mypy checks.
- CI on Python 3.11–3.14, coverage reports, trusted PyPI publishing, and generated API docs.
- An API guide, runnable examples, and a repeatable benchmark.

### Fixed

- Reject malformed graph edge strings.
- Handle arbitrary node names and return a hedge for non-identifiable effects.
- Preserve causal edge types and attributes, validate identification inputs, and avoid latent-name collisions.
- Keep probability simplification mathematically sound for conditional ratios, nested fractions, and summed factors.

## [0.0.2](https://github.com/pedemonte96/causaleffect/tree/0.0.2) (2021-06-19)

- [Published on PyPI](https://pypi.org/project/causaleffect/0.0.2/) for Python 3.7 or newer, with graph creation, plotting, and causal effect identification.
