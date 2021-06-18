from causaleffect import *

'''Code in Figure 3.6 (a)'''

p1 = Probability(var={'X', 'Z'}, cond={'W'})
p2 = Probability(var={'Y'}, cond={'Z'})
p3 = Probability(var={'W'})
p = Probability(recursive=True, children={p1, p2, p3})
print(p.printLatex(simplify=False))
