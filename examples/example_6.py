"""Code in Figure 3.13."""

from causaleffect import ID, createGraph

G = createGraph(["W->X", "X->Y_1", "Z->Y_2", "W<->Y_1", "W<->Z", "W<->Y_2", "X<->Z", "W->Z"])
P = ID({"Y_1", "Y_2"}, {"X"}, G)
