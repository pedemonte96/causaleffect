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