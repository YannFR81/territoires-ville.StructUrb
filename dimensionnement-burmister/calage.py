"""Calage : pour chaque structure mécanique du catalogue, rapport sollicitation/admissible (sans kc, kd)."""
import numpy as np, math, catalogue as c, methode as M, sys
from burmister import Structure, Couche, sollicitations
e,S,MB=c.lire_str('/tmp/repos/territoires-ville.StructUrb/Certu.str')
P={m['abrege']:m for m in MB}
# paramètres de fatigue (1994, à confirmer) — inv_b, SN, Sh(m)
FAT={'GB3':(5,.3),'GB2':(5,.3),'EME':(5,.25),'GC3':(15,1.),'SC':(12,.8),'SL':(12.5,.8),'GLg':(12.5,1.),'GLg-T2':(12.5,1.),
     'GCV':(13.5,1.),'BC5':(16,1.),'BC5g':(16,1.),'BC3':(15,1.)}
def kr(r,ib,SN,Sh): b=-1/ib; return 10**(-M.u_risque(r)*b*math.sqrt(SN**2+(2/b)**2*Sh**2)) if r>0 else 1
def run(idx,pf='PF2',interf_hyd='collee',step=2):
    st=[s for s in S if s['index']==idx][0]; t=st['tables'][(pf,'Q1')]; NEs=c.suite_NE(st['NE_min'],len(t))
    out=[]
    for NE,row in list(zip(NEs,t))[::step]:
        hs=row['ep_surf']/100; hb=(row['ep_base1']+row['ep_base2'])/100; hf=(row['ep_fond1']+row['ep_fond2'])/100
        if hb==0: continue
        L=[]
        if hs>0 and st['surface'] not in('ES','Pavés','Dalles'): L.append(Couche(5400,.35,hs,'BBSG'))
        mb=P[st['base']]; L.append(Couche(mb['E'],mb['nu'],hb,st['base']))
        if hf>0:
            mf=P[st['fondation']]
            if st['base'].startswith('BC') or (mb['sigma6']>0 and mf['sigma6']>0): L[-1].interface=interf_hyd
            L.append(Couche(mf['E'],mf['nu'],hf,st['fondation']))
        L.append(Couche(M.PLATEFORMES[pf],.35,nom=pf))
        sol=sollicitations(Structure(L))
        r=st['taux_risque']; res={}
        for i,cc in enumerate(L[:-1]):
            if cc.nom in FAT:
                ib,SN=FAT[cc.nom]; m=P[cc.nom]
                if m['eps6']>0:
                    adm=1e-6*m['eps6']*math.sqrt({'GB3':12300/9000,'GB2':12300/9000,'EME':16900/14000}[cc.nom])*(NE/1e6)**(-1/ib)*kr(r,ib,SN,M.Sh_bitumineux(cc.h))*M.KS[pf]
                    res[cc.nom+'_εt']=sol[i]['eps_t']/adm
                else:
                    adm=m['sigma6']*(NE/1e6)**(-1/ib)*kr(r,ib,SN,0.03)*M.KS[pf]
                    res[cc.nom+f'_σt(c{i})']=sol[i]['sigma_t']/adm
        res['εz_PF']=sol[-1]['eps_z']/M.eps_z_adm(NE, NE>=2.5e5) if True else 0
        out.append(res)
    keys=out[0].keys()
    return st['abrege'].strip(), {k:(np.median([o[k] for o in out]),np.std([o[k] for o in out])) for k in keys}
if __name__=='__main__':
    for idx in map(int,sys.argv[1:]):
        for it in (['collee','glissante'] if idx in (17,23,22,55,52,4,49,5,6,60) else ['collee']):
            n,d=run(idx,interf_hyd=it); print(f"{idx:3} {n:20} {it:9}", '  '.join(f"{k}={v[0]:.2f}±{v[1]:.2f}" for k,v in d.items()))
