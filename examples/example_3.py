from causaleffect import *

'''Code in Figure 3.6 (b)'''

p1 = Probability(var={'X', 'Z'}, cond={'W'})
p2 = Probability(var={'Y'}, cond={'Z'})
p3 = Probability(var={'W'})
p4 = Probability(sumset={'X', 'Z', 'W'}, recursive=True, children={p1, p2, p3})
p = Probability(sumset={'Z', 'W'}, recursive=True, children={p1, p2, p3}, fraction=True, divisor=p4)
print(p.printLatex(simplify=False))
