# causaleffect

`causaleffect` is a Python library for computing conditional and non-conditional causal effects.

## Installation

For Python 3.11 or newer, install the current release from PyPI:

```bash
python -m pip install numpy causaleffect
```

For Python 3.7–3.10, install the [0.0.2 release](https://pypi.org/project/causaleffect/0.0.2/) instead:

```bash
python -m pip install "causaleffect==0.0.2"
```

Its source is preserved in the [0.0.2 Git tag](https://github.com/pedemonte96/causaleffect/tree/0.0.2). Python 3.11+ users can also pin that version. For `plotGraph` in 0.1.0, install the plotting extra:

```bash
python -m pip install numpy "causaleffect[plot]"
```

For plotting with 0.0.2, install `pycairo` or `cairocffi` separately.

For local development and checks, see [Contributing](https://github.com/pedemonte96/causaleffect/blob/main/CONTRIBUTING.md).

## Usage

If we want to compute the causal effect P(y|do(X=x)) from the causal diagram shown below,

![dag](https://raw.githubusercontent.com/pedemonte96/causaleffect/main/images/usage_s.png)

we first create and display the graph:

```python
import causaleffect

G = causaleffect.createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
causaleffect.plotGraph(G)
```

which renders the following image

![dag](https://raw.githubusercontent.com/pedemonte96/causaleffect/main/images/usage_plot.png)

Then we can compute the causal effect by executing:

```python
P = causaleffect.ID({"Y"}, {"X"}, G)
print(P.printLatex())
```

The code above computes the causal effect, and returns a string encoding the distribution in LaTeX notation:

```
\sum_{w, z}P(w)P(z|w, x)\left(\sum_{x}P(x|w)P(y|w, x, z)\right)
```

This string, in LaTeX, is

![effect](https://raw.githubusercontent.com/pedemonte96/causaleffect/main/images/causal_effect.png)

If the effect is not identifiable, `ID` returns a `Probability` with `identifiable == False`. Its `hedge` contains the two C-forest graphs; use `causaleffect.printGraph(P.hedge[0])` and `causaleffect.printGraph(P.hedge[1])` to inspect them.

## Examples

Start with the [quickstart script](https://github.com/pedemonte96/causaleffect/blob/main/examples/quickstart.py) for identifiable, conditional, and confounded effects.

Other examples from the dissertation:

| Figure number   | Example file                                                                                         |
| --------------- | ---------------------------------------------------------------------------------------------------- |
| Figure 3.5 (a)  | [`example_1.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_1.py) |
| Figure 3.6 (a)  | [`example_2.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_2.py) |
| Figure 3.6 (b)  | [`example_3.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_3.py) |
| Figure 3.10     | [`example_4.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_4.py) |
| Figure 3.12     | [`example_5.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_5.py) |
| Figure 3.13     | [`example_6.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_6.py) |
| Figure 3.15 (a) | [`example_7.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_7.py) |
| Figure 3.15 (b) | [`example_8.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_8.py) |
| Figure 3.16     | [`example_9.py`](https://github.com/pedemonte96/causaleffect/blob/main/examples/example_9.py) |

## Documentation

Read the [API guide](https://github.com/pedemonte96/causaleffect/blob/main/documentation/API.md) or the [generated API reference](https://pedemonte96.github.io/causaleffect/causaleffect.html). The [dissertation](https://arxiv.org/abs/2107.04632) explains the algorithms.

Run the [benchmark](https://github.com/pedemonte96/causaleffect/blob/main/benchmarks/benchmark.py) with `python benchmarks/benchmark.py`. Results are local timing measurements, not performance targets.

See the [changelog](https://github.com/pedemonte96/causaleffect/blob/main/CHANGELOG.md).

## Citation

If you use `causaleffect` in research, please cite:

Pedemonte, M., Vitrià, J., & Parafita, Á. (2021). _Algorithmic Causal Effect Identification with causaleffect_. arXiv. https://doi.org/10.48550/arXiv.2107.04632
