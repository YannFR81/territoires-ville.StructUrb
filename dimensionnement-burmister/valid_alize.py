"""Comparaison du solveur à des résultats Alizé publiés (jumelage 65 kN : a=0,125 m, q=0,662 MPa, d=0,375 m).
Sources : NF P98-086 (2019) annexe I (extraits publics) ; Hornych, séminaire Univ. Gustave Eiffel."""
from burmister import Structure, Couche, jumelage
def ez(S,z,i): return -jumelage(S,z,.662,.125,.375,"dessous",nx=7)[0][i]['ezz']*1e6
def et(S,z,i): p=jumelage(S,z,.662,.125,.375,"dessus",nx=7)[0][i]; return max(p['exx'],p['eyy'])*1e6
cas=[]
S=Structure([Couche(5500,.35,.04),Couche(600,.35,.15),Couche(50,.35)])
cas+= [("NF P98-086 souple — εz tête GNT (axe roue)", ez(S,.04,0), 711.5, 4, "structure confirmée"),
       ("NF P98-086 souple — εz PF2 (axe roue)",      ez(S,.19,0), 1812.1, 4, "structure confirmée")]
S=Structure([Couche(5400,.35,.06),Couche(9000,.35,.13),Couche(9000,.35,.15),Couche(50,.35)])
cas+= [("NF P98-086 bitumineux — εt base GB3 (centre)", et(S,.34,-1), 59.7, .4, "surface 6 cm BBSG et 2e GB3 15 cm déduites"),
       ("NF P98-086 bitumineux — εz PF2 (centre)",       ez(S,.34,-1), 208.7, 2, "idem")]
S=Structure([Couche(5400,.35,.08),Couche(9300,.35,.16),Couche(120,.35)])
cas+= [("Hornych 8 BBSG/16 GB3/PF3, 15 °C — εt max", max(et(S,.24,i) for i in range(7)), 85, 1, "valeur publiée arrondie")]
for n,c,ref,tol,rem in cas:
    print(f"{'OK ' if abs(c-ref)<=tol else 'HORS'} {n:48} calcul {c:8.1f}  Alizé {ref:7.1f} ± {tol:<4} écart {100*(c-ref)/ref:+.2f} %  ({rem})")
