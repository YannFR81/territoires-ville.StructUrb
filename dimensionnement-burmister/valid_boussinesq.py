import numpy as np
from burmister import Structure, Couche
q,a,E,nu=0.662,0.125,1000.,0.35
# massif homogène découpé en 4 couches collées identiques + demi-espace
S=Structure([Couche(E,nu,0.06),Couche(E,nu,0.10),Couche(E,nu,0.15),Couche(E,nu,0.2),Couche(E,nu)])
print(f"{'z':>6} {'sz num':>10} {'sz exact':>10} {'w num':>11} {'w exact':>11} {'er num':>11} {'er exact':>11} {'ez num':>11} {'ez exact':>11}")
err=[]
for z in [0.03,0.06,0.10,0.16,0.25,0.31,0.45,0.51,0.8,1.2]:
    R=S.reponse(z,[0.0],q,a)
    Rz=np.sqrt(a*a+z*z)
    sz=-q*(1-z**3/Rz**3)
    w=(1+nu)*q*a/E*(a/Rz+(1-2*nu)/a*(Rz-z))
    sr=-q/2*((1+2*nu)-2*(1+nu)*z/Rz+z**3/Rz**3)
    er=(sr-nu*(sr+sz))/E
    ez=(sz-2*nu*sr)/E
    vals=[(R['sz'][0],sz),(R['w'][0],w),(R['er'][0],er),(R['ez'][0],ez)]
    err+= [abs(n-e)/abs(e) for n,e in vals]
    print(f"{z:6.2f}"+''.join(f" {n:10.4e} {e:10.4e}" for n,e in vals))
print("erreur relative max :", max(err))
