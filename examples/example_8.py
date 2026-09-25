"""Code in Figure 3.15 (b)."""

from causaleffect import ID, createGraph

G = createGraph(["X<->Y", "Z->Y", "X->Z", "W->X", "W->Z"])
P = ID({"Y"}, {"X"}, G)
print(P.printLatex())
