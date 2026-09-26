Welcome to the Contributors section, thank you for your time!

# Important resources:

- [Examples](examples/)
- [Documentation](documentation/)

# Development

Use Python 3.11 or newer. From the repository root, install the package and development tools in a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest --cov=causaleffect --cov-report=term-missing
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe -m twine check dist/*.whl dist/*.tar.gz
.\.venv\Scripts\python.exe -m pdoc causaleffect -o site
.\.venv\Scripts\python.exe benchmarks/benchmark.py
```

On macOS or Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.
For the example notebook, install `ipykernel` in this environment and select it as the kernel.

# Code of conduct:

This project is governed by the [Contributor Covenant](CODE_OF_CONDUCT.md) code of conduct. By participating, you are expected to uphold this code. In case of any unacceptable behaviour, please report to pedemonte96@gmail.com
