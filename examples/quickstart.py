"""Show identifiable, conditional, and confounded causal queries."""

from causaleffect import ID, createGraph, printGraph

graph = createGraph(["Z->X", "Z->Y", "X->Y"])
print(ID({"Y"}, {"X"}, graph).printLatex())
print(ID({"Y"}, {"X"}, graph, cond={"Z"}).printLatex())

confounded = createGraph(["X->Y", "X<->Y"])
effect = ID({"Y"}, {"X"}, confounded)
print("Identifiable:", effect.identifiable)
if effect.hedge is not None:
    for forest in effect.hedge:
        print("Hedge:", printGraph(forest))
