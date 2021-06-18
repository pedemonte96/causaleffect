from causaleffect import *

'''Code in Figure 3.16'''

G = createGraph(['Z->X', 'Z->Y', 'X->Y'])
P = ID({'Y'}, {'X'}, G)
print(P.printLatex())
