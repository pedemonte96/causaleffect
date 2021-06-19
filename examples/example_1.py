from causaleffect import createGraph, plotGraph, graph

'''Code in Figure 3.5 (a)'''

edges = ['X<->Z', 'X<->W', 'X->Z', 'Z->W', 'W->Y', 'X->Y']
G = createGraph(edges)
print(graph.to_R_notation(edges))

plotGraph(G)
