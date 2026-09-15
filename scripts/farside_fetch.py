# -*- coding: utf-8 -*-
"""
Récupère l'historique complet des flux ETF spot chez Farside Investors.

Pourquoi ce script tourne dans GitHub Actions et pas sur le serveur
---------------------------------------------------------------------
Farside est derrière Cloudflare, qui refuse les IP de datacenter. Mesuré
le 15/09/2026 : HTTP 200 depuis une machine résidentielle, **HTTP 403
depuis le serveur Hetzner**, et cela avec quatre jeux d'en-têtes
différents — jusqu'au jeu navigateur complet avec `Referer` et
`Sec-Fetch-*`. Ce n'est donc pas une question d'en-tête : c'est l'IP.

Les exécuteurs GitHub Actions sortent par des adresses que Cloudflare
laisse passer. Ce script y télécharge la page une fois par jour et publie
un JSON dans le dépôt ; ApexView lit ensuite ce fichier via
raw.githubusercontent.com, joignable depuis le serveur en 0,22 s.

Sortie : data/farside_btc.json et data/farside_eth.json
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SOURCES = {
    "btc": "https://farside.co.uk/bitcoin-etf-flow-all-data/",
    "eth": "https://farside.co.uk/ethereum-etf-flow-all-data/",
}

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Noms complets des émetteurs — Farside ne donne que le ticker.
EMETTEURS = {
    "IBIT": "BlackRock",        "FBTC": "Fidelity",
    "BITB": "Bitwise",          "ARKB": "ARK/21Shares",
    "BTCO": "Invesco/Galaxy",   "EZBC": "Franklin",
    "BRRR": "Valkyrie",         "HODL": "VanEck",
    "BTCW": "WisdomTree",       "GBTC": "Grayscale",
    "BTC":  "Grayscale Mini",   "DEFI": "Hashdex",
    "ETHA": "BlackRock",        "FETH": "Fidelity",
    "ETHW": "Bitwise",          "CETH": "21Shares",
    "ETHV": "VanEck",           "QETH": "Invesco/Galaxy",
    "EZET": "Franklin",         "ETHE": "Grayscale",
    "ETH":  "Grayscale Mini",
}

RE_BALISE = re.compile(r"<[^>]+>")
RE_LIGNE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
RE_CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S | re.I)
RE_DATE = re.compile(r"^\d{1,2}\s+\w{3}\s+20\d{2}$")


def _texte(html: str) -> str:
    """Contenu d'une cellule, balises et entités retirées."""
    t = RE_BALISE.sub("", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&#8211;", "-"), ("&ndash;", "-")):
        t = t.replace(a, b)
    return t.strip()


def _nombre(cellule: str):
    """
    Convertit une cellule Farside en millions de dollars.

    ⚠️ LES NÉGATIFS SONT ENTRE PARENTHÈSES, pas précédés d'un moins :
    « (123.4) » vaut −123,4. Les lire comme positifs inverserait le sens
    de chaque sortie de capitaux — le contraire de ce que le bloc doit
    montrer.

    ⚠️ « - » ET LA CELLULE VIDE NE VALENT PAS ZÉRO : ils signifient que
    le fonds n'existait pas encore ou n'a pas publié. Les compter comme 0
    ferait démarrer chaque fonds au 11/01/2024, y compris ceux lancés des
    mois plus tard.
    """
    t = cellule.replace(",", "").replace("$", "").strip()
    if t in ("", "-", "–", "—", "n/a"):
        return None
    negatif = t.startswith("(") and t.endswith(")")
    if negatif:
        t = t[1:-1]
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if negatif else v


def recuperer(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def analyser(html: str) -> dict:
    """Extrait {dates, tickers, flux par jour et par fonds} du tableau."""
    lignes = RE_LIGNE.findall(html)
    tickers, jours = [], []

    for brut in lignes:
        cells = [_texte(c) for c in RE_CELL.findall(brut)]
        if len(cells) < 4:
            continue

        # La ligne d'en-tête est celle qui contient les tickers.
        if not tickers:
            candidats = [c for c in cells[1:] if re.fullmatch(r"[A-Z]{3,5}", c)]
            if len(candidats) >= 5:
                tickers = candidats
                continue

        # ⚠️ ON N'ACCEPTE QUE LES LIGNES DATÉES. Le tableau se termine par
        # des lignes « Total », « Average », « Maximum », « Minimum » : les
        # avaler comme des jours créerait quatre journées fantômes aux
        # montants aberrants, en tête du classement.
        if not RE_DATE.match(cells[0]):
            continue

        valeurs = [_nombre(c) for c in cells[1:]]
        par_fonds = {}
        for i, tk in enumerate(tickers):
            if i < len(valeurs) and valeurs[i] is not None:
                par_fonds[tk] = valeurs[i]

        # La dernière colonne est le total du jour ; à défaut, on somme.
        total = valeurs[len(tickers)] if len(valeurs) > len(tickers) else None
        if total is None:
            total = sum(par_fonds.values()) if par_fonds else None
        if total is None:
            continue

        try:
            d = datetime.strptime(cells[0], "%d %b %Y").date().isoformat()
        except ValueError:
            continue
        jours.append({"date": d, "flux": round(total, 2), "fonds": par_fonds})

    jours.sort(key=lambda x: x["date"])
    return {"tickers": tickers, "jours": jours}


def construire(actif: str) -> dict:
    html = recuperer(SOURCES[actif])
    d = analyser(html)
    jours = d["jours"]
    if not jours:
        raise SystemExit(f"[farside] {actif}: aucune ligne datée extraite — "
                         f"le format de la page a probablement changé")

    # Cumul par émetteur, calculé sur tout l'historique.
    cumul = {}
    for j in jours:
        for tk, v in j["fonds"].items():
            cumul[tk] = cumul.get(tk, 0.0) + v

    dernier = jours[-1]
    emetteurs = []
    for tk in d["tickers"]:
        emetteurs.append({
            "ticker": tk,
            "nom": EMETTEURS.get(tk, tk),
            "jour": round(dernier["fonds"].get(tk, 0.0), 2),
            "cumul": round(cumul.get(tk, 0.0), 2),
        })
    emetteurs.sort(key=lambda e: e["cumul"], reverse=True)

    return {
        "actif": actif,
        "source": SOURCES[actif],
        "maj_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "depuis": jours[0]["date"],
        "jusqu_a": dernier["date"],
        "nb_jours": len(jours),
        "flux_dernier_jour": dernier["flux"],
        "flux_cumule": round(sum(j["flux"] for j in jours), 2),
        # Série allégée pour le graphique : date + flux, sans le détail.
        "serie": [{"d": j["date"], "f": j["flux"]} for j in jours],
        "emetteurs": emetteurs,
    }


def main():
    racine = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(racine, exist_ok=True)
    code = 0
    for actif in ("btc", "eth"):
        try:
            d = construire(actif)
            chemin = os.path.join(racine, f"farside_{actif}.json")
            # Écriture atomique : un fichier tronqué serait pire que pas
            # de mise à jour du tout.
            tmp = chemin + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, chemin)
            print(f"[farside] {actif}: {d['nb_jours']} jours "
                  f"({d['depuis']} -> {d['jusqu_a']}), "
                  f"{len(d['emetteurs'])} emetteurs, "
                  f"cumule {d['flux_cumule']:,.0f} M$")
        except Exception as e:
            print(f"[farside] {actif}: ECHEC {type(e).__name__} {e}")
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
