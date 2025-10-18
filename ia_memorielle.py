# ia_memorielle.py
# IA qui utilise un fichier JSON comme mémoire,
# apprend des phrases/faits simples et répond aux questions sur les mots-clés.
import json
import os
import random
import re
import unicodedata

FICHIER_MEMOIRE = "memoire.json"

# ---------- Utilitaires ----------
def normalize(text: str) -> str:
    """Normalise le texte pour recherche : minuscules, sans signes diacritiques, sans ponctuation superflue."""
    text = text.lower()
    # enlever accent
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    # remplacer apostrophes et ponctuations par espaces
    text = re.sub(r"[’'`]", " ", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def mots_de_phrase(text: str):
    return [m for m in normalize(text).split() if m]

# ---------- Chargement / sauvegarde ----------
def charger_memoire():
    if os.path.exists(FICHIER_MEMOIRE):
        with open(FICHIER_MEMOIRE, "r", encoding="utf-8") as f:
            memoire = json.load(f)
    else:
        memoire = {"conversation": [], "connaissances": {}, "facts": {}}
    # assurer les clés
    memoire.setdefault("conversation", [])
    memoire.setdefault("connaissances", {})
    memoire.setdefault("facts", {})
    return memoire

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w", encoding="utf-8") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=4)

# ---------- Recherche de mot-clé ----------
def trouver_mot_cle(user_input: str, memoire):
    """Retourne le mot-clé (clé exacte de memoire['connaissances']) trouvé dans la phrase, ou None."""
    texte = normalize(user_input)
    # Cherche d'abord correspondance exacte de mots (préférable)
    mots = mots_de_phrase(texte)
    # test mots simples
    for mot in mots:
        if mot in memoire["connaissances"] or mot in memoire["facts"]:
            return mot
    # ensuite test si une clé (plus longue) est contenue dans la phrase
    for mot_cle in memoire["connaissances"].keys():
        if mot_cle in texte:
            return mot_cle
    for mot_cle in memoire["facts"].keys():
        if mot_cle in texte:
            return mot_cle
    return None

# ---------- Enregistrement de faits simples ----------
VERBES_SIMPLE = ["mange", "mangent", "manger", "aime", "aiment", "habite", "vit", "a", "est", "sont", "possède", "posseder", "aimer"]

def extraire_fait(user_input: str, memoire):
    """
    Tente d'extraire un fait simple de type <mot_clé> VERBE <objet>.
    Si un mot-clé connu apparaît et qu'on détecte un verbe utile, on stocke l'objet.
    """
    texte = normalize(user_input)
    mots = mots_de_phrase(texte)
    found = None
    # trouver mot_clé présent dans la phrase (priorité aux clés existantes)
    for mot in memoire["connaissances"].keys():
        if mot in texte:
            found = mot
            break
    if not found:
        for mot in memoire["facts"].keys():
            if mot in texte:
                found = mot
                break
    # si on ne connaît aucun mot, on essaie de deviner un mot substantif simple (premier mot)
    if not found and mots:
        # pas idéal, on évite inventer pour mots courts comme "je","tu"
        if len(mots[0]) > 2:
            found = mots[0]

    if not found:
        return None  # rien à apprendre

    # tenter d'extraire verbe+objet via regex simple :
    # ex: "le chat mange des croquettes", "chat aime jouer", "le chat est noir"
    # on va chercher un des verbes simples et prendre ce qui suit comme objet
    for v in VERBES_SIMPLE:
        pattern = r"\b" + re.escape(v) + r"\b\s*(.*)"
        m = re.search(pattern, texte)
        if m:
            objet = m.group(1).strip()
            if objet:
                # nettoyer début si commence par des articles
                objet = re.sub(r"^(le |la |les |un |une |des |du |de la |d' )", "", objet).strip()
                # stocker
                memoire.setdefault("facts", {})
                memoire["facts"].setdefault(found, {})
                memoire["facts"][found].setdefault(v, [])
                if objet not in memoire["facts"][found][v]:
                    memoire["facts"][found][v].append(objet)
                # aussi sauvegarder la phrase dans connaissances pour réutilisation
                memoire.setdefault("connaissances", {})
                memoire["connaissances"].setdefault(found, [])
                if user_input not in memoire["connaissances"][found]:
                    memoire["connaissances"][found].append(user_input)
                return {"sujet": found, "verbe": v, "objet": objet}
    return None

# ---------- Réponses aux questions ----------
def repondre_question(user_input: str, memoire):
    texte = normalize(user_input)

    # 1) Questions formelles : "que/quoi/qu'est-ce que ... (mange) ... ?"
    # On essaie d'attraper "que mange (le )?chat"
    q_mange = re.search(r"que(?: |'|est-ce que)?\s*(?:mange|mangent)\s*(?:-|le |la |les |un |une )?([a-z0-9\s'-]+)\??", texte)
    if q_mange:
        sujet = q_mange.group(1).strip()
        mot = trouver_mot_cle(sujet, memoire) or normalize(sujet).split()[0]
        return reponse_sur_fait(mot, "mange", memoire)

    q_que = re.search(r"qu(?:e|oi|')\s*(sais[- ]tu|est[- ]ce que|est)\s*(?:de|sur)?\s*([a-z0-9\s'-]+)\??", texte)
    if q_que:
        sujet = q_que.group(2).strip()
        mot = trouver_mot_cle(sujet, memoire) or normalize(sujet).split()[0]
        return reponse_sur_connaissances(mot, memoire)

    # "tu te souviens de X" ou "tu te rappelles X"
    q_souviens = re.search(r"(tu te souviens de|tu te rappelles(?: -?tu)? )\s*([a-z0-9\s'-]+)\??", user_input.lower())
    if q_souviens:
        sujet = q_souviens.group(2).strip()
        mot = trouver_mot_cle(sujet, memoire) or normalize(sujet).split()[0]
        return reponse_sur_connaissances(mot, memoire)

    # 2) Forme générale : si la phrase contient un mot-clé connu, on renvoie info/fait pertinent
    mot = trouver_mot_cle(user_input, memoire)
    if mot:
        # prioriser faits (mange, a, est, aime) si question
        verbs_priority = ["mange", "aime", "est", "a", "habite"]
        for v in verbs_priority:
            if mot in memoire.get("facts", {}) and v in memoire["facts"][mot]:
                objs = memoire["facts"][mot][v]
                if objs:
                    return f"{mot.capitalize()} {v} {', '.join(objs)}."
        # sinon renvoyer une phrase connue
        if memoire.get("connaissances", {}).get(mot):
            return random.choice(memoire["connaissances"][mot])
    # fallback
    return None

def reponse_sur_fait(mot, verbe, memoire):
    mot = normalize(mot)
    if mot in memoire.get("facts", {}) and verbe in memoire["facts"][mot]:
        objs = memoire["facts"][mot][verbe]
        if objs:
            # formater objet(s)
            return f"{mot.capitalize()} {verbe} {', '.join(objs)}."
    # si pas de fait, essayer connaissances textuelles
    if mot in memoire.get("connaissances", {}) and memoire["connaissances"][mot]:
        return random.choice(memoire["connaissances"][mot])
    return None

def reponse_sur_connaissances(mot, memoire):
    mot = normalize(mot)
    if mot in memoire.get("connaissances", {}) and memoire["connaissances"][mot]:
        # construire une synthèse si facts existent
        lines = []
        # facts first
        facts = memoire.get("facts", {}).get(mot, {})
        for v, objs in facts.items():
            if objs:
                lines.append(f"{mot.capitalize()} {v} {', '.join(objs)}.")
        # compléter avec phrases connues
        if memoire["connaissances"].get(mot):
            lines.append(random.choice(memoire["connaissances"][mot]))
        if lines:
            return " ".join(lines)
    return None

# ---------- Interface principale ----------
def ia_memorielle():
    print("Salut ! Je suis ton IA mémorielle. Tape 'quit' pour arrêter.")
    print("Commandes utiles : 'efface memoire' pour réinitialiser, 'liste mots' pour afficher les mots connus.")
    memoire = charger_memoire()

    while True:
        user_input = input("Toi : ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("IA : À bientôt !")
            break

        # commandes directes
        if user_input.lower() == "efface memoire":
            confirm = input("Confirmer effacement de memoire.json ? (oui/non) : ").strip().lower()
            if confirm == "oui":
                memoire = {"conversation": [], "connaissances": {}, "facts": {}}
                sauvegarder_memoire(memoire)
                print("IA : Mémoire réinitialisée.")
            else:
                print("IA : Annulé.")
            continue
        if user_input.lower() == "liste mots":
            keys = sorted(set(list(memoire.get("connaissances", {}).keys()) + list(memoire.get("facts", {}).keys())))
            print("IA : Mots connus :", ", ".join(keys[:200]) + (", ..." if len(keys) > 200 else ""))
            continue

        # sauvegarder question dans conversation
        memoire.setdefault("conversation", []).append(f"Toi : {user_input}")

        # d'abord, vérifier si c'est une question ciblée -> essayer d'y répondre
        reponse = repondre_question(user_input, memoire)
        if reponse:
            print("IA :", reponse)
            memoire["conversation"].append(f"IA : {reponse}")
            sauvegarder_memoire(memoire)
            continue

        # sinon tenter d'extraire un fait si l'utilisateur déclare quelque chose
        fait = extraire_fait(user_input, memoire)
        if fait:
            # réponse de confirmation et synthèse
            sujet, verbe, objet = fait["sujet"], fait["verbe"], fait["objet"]
            reponse = f"Compris — j'ai appris que {sujet} {verbe} {objet}."
            print("IA :", reponse)
            memoire["conversation"].append(f"IA : {reponse}")
            sauvegarder_memoire(memoire)
            continue

        # sinon, si la phrase contient un mot connu, renvoyer une info connue
        mot = trouver_mot_cle(user_input, memoire)
        if mot:
            if memoire.get("facts", {}).get(mot):
                # prioriser facts simples
                facts = memoire["facts"][mot]
                for v in ["mange", "aime", "est", "habite", "a"]:
                    if v in facts and facts[v]:
                        reponse = f"{mot.capitalize()} {v} {', '.join(facts[v])}."
                        break
            if not reponse and memoire.get("connaissances", {}).get(mot):
                reponse = random.choice(memoire["connaissances"][mot])
            if reponse:
                print("IA :", reponse)
                memoire["conversation"].append(f"IA : {reponse}")
                sauvegarder_memoire(memoire)
                continue

        # Si on arrive là, on ne comprend pas précisément : poser une question ou apprendre la phrase brute
        # On propose de mémoriser la phrase comme info générale
        reponse = "Je n'ai pas d'info précise là-dessus. Tu veux que j'enregistre ça comme un fait ? (oui/non)"
        print("IA :", reponse)
        memoire["conversation"].append(f"IA : {reponse}")
        # attendre réponse oui/non
        rep = input("Toi : ").strip().lower()
        if rep in ("oui", "o"):
            # considérer la phrase comme info générale pour les mots qu'on détecte
            mots = mots_de_phrase(user_input)
            if not mots:
                print("IA : Je n'ai rien compris à mémoriser.")
            else:
                # utiliser premier mot détecté comme clé
                cle = mots[0]
                memoire.setdefault("connaissances", {})
                memoire["connaissances"].setdefault(cle, [])
                if user_input not in memoire["connaissances"][cle]:
                    memoire["connaissances"][cle].append(user_input)
                print(f"IA : D'accord, j'ai mémorisé ça sous '{cle}'.")
            memoire["conversation"].append(f"Toi : {rep}")
            sauvegarder_memoire(memoire)
        else:
            print("IA : OK, je n'enregistrerai rien.")
            memoire["conversation"].append(f"Toi : {rep}")
            sauvegarder_memoire(memoire)

if __name__ == "__main__":
    ia_memorielle()
