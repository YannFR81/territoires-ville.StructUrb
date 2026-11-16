import sys, numpy as np, catalogue as c, methode as M
from burmister import Structure, Couche, sollicitations
e,S,_=c.lire_str('/tmp/repos/territoires-ville.StructUrb/Certu.str')
idx=int(sys.argv[1]); pf=sys.argv[2]; Esurf=float(sys.argv[3]) if len(sys.argv)>3 else 5400
st=[s for s in S if s['index']==idx][0]
mat=st['base']; r=st['taux_risque']
t=st['tables'][(pf,'Q1')]; NEs=c.suite_NE(st['NE_min'],len(t))
print(f"Structure {st['abrege']} | {pf} | risque {r}% | Esurf={Esurf}")
print(f"{'NE':>9} {'surf':>4} {'assise':>6} | {'εt calc':>8} {'εt adm':>8} {'ratio':>6} | {'εz calc':>8} {'εz adm':>8} {'ratio':>6}")
for NE,row in zip(NEs,t):
    hs=row['ep_surf']/100; hb=(row['ep_base1']+row['ep_base2']+row['ep_fond1']+row['ep_fond2'])/100
    if hb==0: continue
    E=M.MATERIAUX[mat]['E15']
    couches=([Couche(Esurf,.35,hs,"surf")] if hs>0 else [])+[Couche(E,.35,hb,mat),Couche(M.PLATEFORMES[pf],.35,nom=pf)]
    sol=sollicitations(Structure(couches))
    et=sol[-2]['eps_t']; ez=sol[-1]['eps_z']
    Sh=M.Sh_bitumineux(hb)
    eta=M.eps_t_adm(mat,NE,r,Sh,pf); eza=M.eps_z_adm(NE)
    print(f"{NE:9d} {row['ep_surf']:4d} {int(hb*100):6d} | {et*1e6:8.1f} {eta*1e6:8.1f} {et/eta:6.2f} | {ez*1e6:8.0f} {eza*1e6:8.0f} {ez/eza:6.2f}")
