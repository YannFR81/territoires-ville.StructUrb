import numpy as np
from burmister import Structure, Couche, _lignes
q,a=0.662,0.125
for mode in ["collee","glissante"]:
    S=Structure([Couche(7000,.35,.06,"BBSG"),Couche(9000,.35,.12,"GB3",interface=mode),Couche(600,.35,.25,"GNT"),Couche(50,.35,nom="PF2")])
    print("== interface BBSG/GB3 :",mode)
    # 1) équilibre : la transformée de sz tend vers la charge pour m->0 à toute profondeur
    m=np.array([1e-6]); 
    for z in [0.03,0.06,0.18,0.3,0.6]:
        i,U,W,Sz,Ez=S._noyaux(m,z,"dessus"); print(f"  équilibre z={z}: sz_hat(m→0)/m = {Sz[0]/m[0]:+.8f} (attendu -1)")
    # 2) continuité aux interfaces (r = 0 et r = 0.2)
    for z in S.zb[:-1]:
        h=S.reponse(z,[0,0.2],q,a,"dessus"); b=S.reponse(z,[0,0.2],q,a,"dessous")
        print(f"  z={z:.2f}: w {h['w']} | {b['w']}   sz {h['sz']} | {b['sz']}   u {h['u']} | {b['u']}")
    # 3) cisaillement nul à l'interface glissante
    if mode=="glissante":
        mm=np.linspace(0.1,200,5); coef=S.resoudre(mm)
        for i in (0,1):
            L=_lignes(mm,S.zb[0],S.zt[i],S.zb[i],S.c[i].E,S.c[i].nu)
            print("  trz couche",i,":",np.abs(np.einsum('mkj,mj->mk',L,coef[:,i])[:,3]).max())
    # 4) ez = dw/dz par différences finies dans la GB3
    z=0.12; dz=1e-5
    ez=S.reponse(z,[0.0],q,a)["ez"][0]
    fd=(S.reponse(z+dz,[0.0],q,a)["w"][0]-S.reponse(z-dz,[0.0],q,a)["w"][0])/(2*dz)
    print(f"  ez={ez:.6e}  -dw/dz (DF)={-fd:.6e}")
