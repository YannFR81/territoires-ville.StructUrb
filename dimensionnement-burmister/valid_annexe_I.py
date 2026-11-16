# Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannFR81, agent territorial, et Claude, IA d'Anthropic, 2026.
# Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie.
"""Cas tests de l'annexe I de la NF P98-086 (mai 2019) — jumelage standard 65 kN.
Couches : (nom, h m, E MPa, nu, interface avec la couche inférieure). Semi-collée = moyenne collé/glissant."""
import numpy as np
from burmister import Structure, Couche, jumelage, contrainte_horizontale
INF=np.inf
CAS={
 "I.1 souple":[("BBM",.04,5500,.35,"collee"),("GNT",.15,600,.35,"collee"),("PF2",INF,50,.35,None)],
 "I.2 bitumineux 1":[("BBTM",.025,3000,.35,"collee"),("BBSG2",.06,7000,.35,"collee"),("GB3",.13,9000,.35,"collee"),("GB3",.13,9000,.35,"collee"),("PF2",INF,50,.35,None)],
 "I.3 bitumineux 2":[("BBTM",.025,3000,.35,"collee"),("EME2",.12,14000,.35,"collee"),("PF3",INF,120,.35,None)],
 "I.4 bitumineux 3":[("BBTM",.025,3000,.35,"collee"),("EME2",.11,14000,.35,"collee"),("EME2",.12,14000,.35,"collee"),("PF4",INF,200,.35,None)],
 "I.5 semi-rigide 1":[("BBSG",.06,7000,.35,"collee"),("GC-T3",.15,23000,.25,"semi"),("GC-T3",.15,23000,.25,"collee"),("PF3",INF,120,.35,None)],
 "I.6 semi-rigide 2":[("BBTM",.025,3000,.35,"collee"),("BBSG3",.06,7000,.35,"collee"),("GC-T3",.22,23000,.25,"semi"),("GC-T3",.20,23000,.25,"collee"),("PF2",INF,50,.35,None)],
 "I.7 rigide 1":[("BC5",.23,35000,.25,"glissante"),("BC2",.18,20000,.25,"collee"),("PF2",INF,50,.35,None)],
 "I.8 rigide 2":[("BC6",.20,40000,.25,"semi"),("GB3",.13,9000,.35,"collee"),("PF2qs",INF,80,.35,None)],
}
# (cas, indice couche, grandeur, position, valeur, tolérance)
REQ=[("I.1 souple",1,"ez","roue",711.5,4),("I.1 souple",2,"ez","roue",1812.1,4),
 ("I.2 bitumineux 1",3,"et","centre",59.7,.4),("I.2 bitumineux 1",4,"ez","centre",208.7,2),
 ("I.3 bitumineux 2",1,"et","centre",128.0,1),("I.3 bitumineux 2",2,"ez","roue",470.2,3),
 ("I.4 bitumineux 3",2,"et","centre",50.5,.4),("I.4 bitumineux 3",3,"ez","centre",154.1,1),
 ("I.5 semi-rigide 1",1,"st","centre",.612,.003),("I.5 semi-rigide 1",2,"st","centre",.815,.003),("I.5 semi-rigide 1",3,"ez","centre",121.0,1),
 ("I.6 semi-rigide 2",2,"st","centre",.450,.003),("I.6 semi-rigide 2",3,"st","centre",.552,.003),("I.6 semi-rigide 2",4,"ez","centre",92.4,1),
 ("I.7 rigide 1",0,"st","centre",1.265,.006),("I.7 rigide 1",1,"st","centre",.554,.003),("I.7 rigide 1",2,"ez","centre",125.2,1),
 ("I.8 rigide 2",0,"st","roue",1.277,.006),("I.8 rigide 2",1,"et","centre",28.3,.4),("I.8 rigide 2",2,"ez","centre",122.5,1)]
def une(layers,i,g,pos):
    S=Structure([Couche(E,nu,h,n,itf or "collee") for n,h,E,nu,itf in layers]); k=0 if pos=="roue" else -1
    if g=="ez": return -jumelage(S,S.zt[i],.662,.125,.375,"dessous",nx=3)[0][k]['ezz']*1e6
    p=jumelage(S,S.zb[i],.662,.125,.375,"dessus",nx=3)[0][k]
    if g=="et": return max(p['exx'],p['eyy'])*1e6
    return max(contrainte_horizontale(S.c[i],p['exx'],p['eyy'],p['ezz']))
def calc(layers,i,g,pos):
    semi=[j for j,l in enumerate(layers) if l[4]=="semi"]
    if not semi: return une(layers,i,g,pos)
    v=[]
    for mode in ("collee","glissante"):
        L=[(n,h,E,nu,mode if itf=="semi" else itf) for n,h,E,nu,itf in layers]; v.append(une(L,i,g,pos))
    return sum(v)/2
if __name__=="__main__":
    ok=0
    for cas,i,g,pos,ref,tol in REQ:
        v=calc(CAS[cas],i,g,pos); good=abs(v-ref)<=tol; ok+=good
        print(f"{'OK  ' if good else 'HORS'} {cas:18} {CAS[cas][i][0]:6} {g} {pos:6} calcul {v:9.3f}  norme {ref:8.3f} ± {tol:<5}  écart {100*(v-ref)/ref:+.2f} %")
    print(f"{ok}/{len(REQ)} dans la tolérance")
