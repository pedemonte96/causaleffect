# Changelog

## [0.1.0](https://github.com/pedemonte96/causaleffect/releases/tag/v0.1.0)

### Changed

- Require Python 3.11 or newer; PyPI 0.0.2 supported Python 3.7 or newer.
- Move all package metadata and dependencies to `pyproject.toml`, with an optional plotting extra.
- Depend on `igraph` directly without requiring NumPy.

### Added

- Type annotations, a `py.typed` marker, citation metadata, regression coverage, Ruff and mypy checks.
- CI on Python 3.11–3.14, coverage reports, trusted PyPI publishing, and generated API docs.
- An API guide, runnable examples, and a repeatable benchmark.

### Fixed

- Reject malformed graph edge strings.
- Handle arbitrary node names and return a hedge for non-identifiable effects.
- Preserve causal edge types, attributes, and multiplicity when splitting graphs and building C-components; correct parent and subgraph helpers.
- Validate identification inputs and avoid latent-name collisions.
- Preserve conditional ratios, nested fractions, and summed factors during probability simplification, with deterministic factor ordering.

## [0.0.2](https://github.com/pedemonte96/causaleffect/tree/0.0.2) (2021-06-19)

- [Published on PyPI](https://pypi.org/project/causaleffect/0.0.2/) for Python 3.7 or newer, with graph creation, plotting, and causal effect identification.
