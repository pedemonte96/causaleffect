from causaleffect import *

'''Code in Figure 3.10'''

G = createGraph(['X->Z', 'Z->Y', 'X<->Y'])
P = ID({'Y'}, {'X'}, G)
print(P.printLatex())
