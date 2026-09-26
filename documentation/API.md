# API guide

The public API is available from `import causaleffect`. Install NumPy alongside `causaleffect` for graph processing. The [generated API reference](https://pedemonte96.github.io/causaleffect/causaleffect.html) has the full signatures and type annotations.

## Graphs

`createGraph(edges, verbose=False)` accepts edge strings such as `"X->Y"`, `"Y<-Z"`, and `"X<->Z"`. Node names come from the edge endpoints. It returns a directed `igraph.Graph`; bidirected edges represent unobserved confounding. Malformed edges raise `ValueError`.

`printGraph(graph)` returns `(nodes, edges)`, where `nodes` is a list of names and `edges` contains `->` and `<->` strings.

`plotGraph(graph, name=None)` plots the graph. Install `causaleffect[plot]` first. Passing `name="diagram"` writes `diagram.png`; omitting it returns an in-memory plot.

`to_R_notation(edges)` returns `(edge_text, directed_end, all_end)` for the R `causaleffect` package. It modifies the supplied list of edge strings, so pass `edges.copy()` if you need to keep it.

## Identification

`ID(Y, X, graph, cond=None, verbose=False)` computes the effect on outcome nodes `Y` of intervening on nodes `X`. Pass optional conditioning nodes in `cond`; all three sets must be disjoint, or `ID` raises `ValueError`. Pass an acyclic directed graph; directed cycles are unsupported.

```python
from causaleffect import ID, createGraph

graph = createGraph(["X->Y", "Z->X", "Z->Y"])
effect = ID({"Y"}, {"X"}, graph)
print(effect.printLatex())
```

`ID` returns a `Probability`. When `effect.identifiable` is `True`, `effect.printLatex()` returns a LaTeX expression. When it is `False`, `effect.hedge` is a pair of C-forest graphs; inspect them with `printGraph`. `printLatex()` simplifies the expression in place by default. Call `effect.copy().printLatex()` to keep the original expression.

## Probability expressions

`Probability(var=..., cond=...)` represents `P(var | cond)`. For products, pass `recursive=True` and a set of `Probability` objects as `children`. `sumset` adds variables to sum over; `fraction=True` and `divisor` represent a ratio. `hedge` stores the two graphs for an unidentifiable effect.

`attributes()` returns the expression structure as a dictionary. `getFreeVariables()` returns variables not summed out. `copy()` makes a deep copy, and `simplify()` simplifies in place. See [examples 2 and 3](https://github.com/pedemonte96/causaleffect/tree/main/examples) for expression construction.
