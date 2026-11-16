# Dimensionnement de chaussées — Burmister + Struct-Urb. Développé par YannFR81, agent territorial, et Claude, IA d'Anthropic, 2026.
# Licence GNU GPL v3 (œuvre dérivée de Struct-Urb, CERTU/Cerema). Sans garantie.
"""Décodeur des fichiers binaires Struct-Urb (CERTU) : Certu.str et Certu.mts.
Format VB6 : Integer=int16, Long=int32, Boolean=int16, Byte=uint8, Single=float32,
String = Long (longueur) + octets cp1252."""
import struct, sys, json

FIN = "###Fin commentaire###"
PF_LABELS = [("PF1","Q1"),("PF1","Q2"),("PF2","Q1"),("PF2","Q2"),("PF2+","Q1"),("PF2+","Q2"),("PF3","Q1"),("PF3","Q2")]  # ordre DonnerColPF

class R:
    def __init__(s, data): s.d, s.p = data, 0
    def eof(s): return s.p >= len(s.d)
    def _u(s, fmt):
        n = struct.calcsize(fmt); v = struct.unpack_from("<"+fmt, s.d, s.p)[0]; s.p += n; return v
    def int(s): return s._u("h")
    def long(s): return s._u("i")
    def byte(s): return s._u("B")
    def single(s): return round(s._u("f"), 6)
    def bool(s): return s._u("h") != 0
    def str(s):
        n = s.long(); v = s.d[s.p:s.p+n].decode("cp1252"); s.p += n; return v
    def comment(s):
        c = s.str(); nxt = s.str()
        while nxt != FIN: c += nxt; nxt = s.str()
        return c

def lire_str(path):
    r = R(open(path, "rb").read())
    entete = r.str()
    structures, materiaux = [], []
    while not r.eof():
        t = r.str()
        if t == "Structure":
            st = dict(index=r.int(), abrege=r.str(), surface=r.str(), base=r.str(), fondation=r.str(),
                      surf_sans_ep=r.int(), saisie_complete=r.bool(),
                      util_desserte=r.int(), util_distribution=r.int(), util_PL=r.int(), util_bus=r.int(),
                      util_parking=r.int(), util_gir_dis=r.int(), util_gir_PL=r.int(),
                      type_chaussee=r.byte(), taux_risque=r.int(), type_CAM=r.int(), type_structure=r.byte(),
                      NE_min=r.long(), NE_max=r.long(), commentaire=r.comment())
            st["tables"] = {}
            for i in range(8):
                n = r.long(); rows = []
                for _ in range(n // 8):
                    rows.append(dict(ep_surf=r.int(), ep_base1=r.int(), ep_base2=r.int(),
                                     ep_fond1=r.int(), ep_fond2=r.int(), Qm=r.single(),
                                     min_techno=r.str(), max_pratique=r.str()))
                st["tables"][PF_LABELS[i]] = rows
            structures.append(st)
        elif t == "MatériauFondBase":
            materiaux.append(dict(nom=r.str(), abrege=r.str(), norme=r.str(), qualite_gel=r.str(),
                                  a_gel=r.single(), b_gel=r.single(), E=r.single(), nu=r.single(),
                                  eps6=r.single(), sigma6=r.single(), commentaire=r.comment()))
        else:
            raise ValueError(f"type inconnu {t!r} à {r.p}")
    return entete, structures, materiaux

def lire_mts(path):
    r = R(open(path, "rb").read())
    entete = r.str(); mats = []
    while not r.eof():
        t = r.str()
        if t in ("MatériauSimple", "Matériau"):
            m = dict(type=t, nom=r.str(), abrege=r.str(), norme=r.str(), qualite_gel=r.str(),
                     a_gel=r.single(), b_gel=r.single())
            if t == "Matériau":
                m.update(E=r.single(), nu=r.single(), eps6=r.single(), sigma6=r.single())
            m["commentaire"] = r.comment(); mats.append(m)
        elif t == "MatériauComposé":
            m = dict(type=t, nom=r.str(), abrege=r.str()); n = r.int()
            m.update(a_gel=r.single(), b_gel=r.single(), compositions=[])
            for _ in range(n):
                c = dict(ep_totale=r.int(), couches=[])
                for _ in range(3):
                    c["couches"].append((r.int(), r.str()))
                m["compositions"].append(c)
            mats.append(m)
        else:
            raise ValueError(f"type inconnu {t!r} à {r.p}")
    return entete, mats

def suite_NE(ne_min, n):
    """Reproduit TrouverNEthEtInd : pas = 10^(nb chiffres-1)."""
    out, ne = [], ne_min
    for _ in range(n):
        out.append(ne); ne += 10 ** (len(str(ne)) - 1)
    return out
