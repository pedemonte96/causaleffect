"""Code in Figure 3.16."""

from causaleffect import ID, createGraph

G = createGraph(["Z->X", "Z->Y", "X->Y"])
P = ID({"Y"}, {"X"}, G)
print(P.printLatex())
