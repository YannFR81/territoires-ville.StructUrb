import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import catalogue as c, methode as M
from burmister import Structure, Couche, sollicitations
e,S,_=c.lire_str('/tmp/repos/territoires-ville.StructUrb/Certu.str')
cas=[(7,'PF2','GB3'),(7,'PF3','GB3'),(2,'PF2','EME'),(10,'PF2','GB3'),(13,'PF2','GC3'),(13,'PF3','GC3')]
fig,ax=plt.subplots(figsize=(9,5.2),dpi=130)
for idx,pf,mat in cas:
    st=[s for s in S if s['index']==idx][0]; t=st['tables'][(pf,'Q1')]; NEs=c.suite_NE(st['NE_min'],len(t))
    xs,ys=[],[]
    for NE,row in zip(NEs,t):
        hs=row['ep_surf']/100; hb=sum(row[k] for k in('ep_base1','ep_base2','ep_fond1','ep_fond2'))/100
        p=M.MATERIAUX[mat]
        sol=sollicitations(Structure([Couche(5400,.35,hs),Couche(p['E15'],p['nu'],hb,mat),Couche(M.PLATEFORMES[pf],.35)]))
        if p['fam']=='bitumineux': y=sol[1]['eps_t']/M.eps_t_adm(mat,NE,st['taux_risque'],M.Sh_bitumineux(hb),pf)
        else: y=sol[1]['sigma_t']/M.sigma_t_adm(mat,NE,st['taux_risque'],0.03,pf)
        xs.append(NE); ys.append(y)
    ax.plot(xs,ys,'o-',ms=4,label=f"{st['abrege'].strip()} – {pf} (risque {st['taux_risque']} %)")
ax.axhline(1,color='k',lw=1); ax.axhspan(0.95,1.05,color='0.9',zorder=0)
ax.set_xscale('log'); ax.set_ylim(0.6,1.3); ax.set_xlabel("NE (essieux équivalents 13 t)")
ax.set_ylabel("sollicitation calculée / admissible")
ax.set_title("Épaisseurs du catalogue Struct-Urb recalculées par le solveur Burmister\n(1,0 = épaisseur juste suffisante selon la méthode rationnelle)")
ax.legend(fontsize=8,loc='lower right'); ax.grid(alpha=.3,which='both')
fig.tight_layout(); fig.savefig('validation_catalogue.png')
