# causaleffect

`causaleffect` is a Python library for computing conditional and non-conditional causal effects.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install `causaleffect` (not yet uploaded).

```bash
pip install causaleffect
```

## Usage

```python
import causaleffect

G = causaleffect.createGraph (["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
P = causaleffect.ID ({'Y'}, {'X'}, G)
P.printLatex() # returns \sum_{w, z}P(w)P(z|w, x)\left(\sum_{x}P(x|w)P(y|w, x, z)\right)
```

## Examples

Some examples from the dissertation can be found in this repository:

| Figure number   | Example file                  |
|-----------------|-------------------------------|
| Figure 3.5 (a)  | `example_1.py`                |
| Figure 3.6 (a)  | `example_2.py`                |
| Figure 3.6 (b)  | `example_3.py`                |
| Figure 3.10     | `example_4.py`                |
| Figure 3.12     | `example_5.py`                |
| Figure 3.13     | `example_6.py`                |
| Figure 3.15 (a) | `example_7.py`                |
| Figure 3.15 (b) | `example_8.py`                |
| Figure 3.16     | `example_9.py`                |
