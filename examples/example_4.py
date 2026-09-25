"""Code in Figure 3.10."""

from causaleffect import ID, createGraph

G = createGraph(["X->Z", "Z->Y", "X<->Y"])
P = ID({"Y"}, {"X"}, G)
print(P.printLatex())
