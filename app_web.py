# app_web.py
from flask import Flask, request, render_template_string, session
import os, json, re, uuid

# =============== Config ===============
app = Flask(__name__)
app.secret_key = "change_this_secret_key_empereur"  # change la si tu veux
DATA_DIR = "data"
USER_MEM_DIR = os.path.join(DATA_DIR, "user_memories")
GLOBAL_KNOWLEDGE_FILE = os.path.join(DATA_DIR, "knowledge.json")
os.makedirs(USER_MEM_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# =============== Helpers (normalisation, I/O) ===============
def normalize(text: str) -> str:
    """Normalise la chaîne: minuscules, sans ponctuation excessive, espaces simples."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[’'`]", "'", text)
    text = re.sub(r"[^a-z0-9\u00C0-\u017Fa-z\s\-]", " ", text)  # garde lettres accentuées et chiffres
    text = re.sub(r"\s+", " ", text).strip()
    return text

def read_json_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def write_json_file(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# =============== Knowledge store ===============
def load_global_knowledge():
    return read_json_file(GLOBAL_KNOWLEDGE_FILE)

def save_global_knowledge(k):
    write_json_file(GLOBAL_KNOWLEDGE_FILE, k)

def add_global_fact(subject, predicate, obj, raw_text):
    """Ajoute un fait triple dans la connaissance globale (évite les doublons simples)."""
    k = load_global_knowledge()
    subj_n = normalize(subject)
    obj_n = normalize(obj)
    # simple duplicate check
    for t in k:
        if t.get("subject_norm")==subj_n and t.get("object_norm")==obj_n and t.get("predicate")==predicate:
            return
    triple = {
        "subject": subject.strip(),
        "predicate": predicate,
        "object": obj.strip(),
        "subject_norm": subj_n,
        "object_norm": obj_n,
        "raw": raw_text
    }
    k.append(triple)
    save_global_knowledge(k)

# =============== Per-user memory (privée) ===============
def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        session["chat"] = []  # historique par session
    return session["user_id"]

def user_memory_file(user_id):
    return os.path.join(USER_MEM_DIR, f"{user_id}.json")

def load_user_memory(user_id):
    return read_json_file(user_memory_file(user_id))

def save_user_memory(user_id, mem):
    write_json_file(user_memory_file(user_id), mem)

def add_user_fact(user_id, subject, predicate, obj, raw_text):
    mem = load_user_memory(user_id)
    subj_n = normalize(subject)
    obj_n = normalize(obj)
    # évite duplications simples
    for t in mem:
        if t.get("subject_norm")==subj_n and t.get("object_norm")==obj_n and t.get("predicate")==predicate:
            return
    triple = {
        "subject": subject.strip(),
        "predicate": predicate,
        "object": obj.strip(),
        "subject_norm": subj_n,
        "object_norm": obj_n,
        "raw": raw_text
    }
    mem.append(triple)
    save_user_memory(user_id, mem)

# =============== Détection et parsing de faits simples ===============
# Patterns français / anglais très basiques
FACT_PATTERNS = [
    # français: "X est Y", "Le soleil est une étoile"
    r"^\s*(?P<subj>.+?)\s+est\s+(?P<obj>.+?)\s*$",
    r"^\s*(?P<subj>.+?)\s+sont\s+(?P<obj>.+?)\s*$",
    # anglais:
    r"^\s*(?P<subj>.+?)\s+is\s+(?P<obj>.+?)\s*$",
    r"^\s*(?P<subj>.+?)\s+are\s+(?P<obj>.+?)\s*$",
    # française variante: "X : Y" (ex: "Une étoile : Tout ce qui brille...")
    r"^\s*(?P<subj>.+?)\s*[:\-—]\s*(?P<obj>.+?)\s*$"
]

def extract_fact(text):
    """
    Si text contient un fait simple, retourne (subject, predicate, object), sinon None.
    predicate is a string like 'est' or 'is' or ':' etc.
    """
    t = text.strip()
    for pat in FACT_PATTERNS:
        m = re.match(pat, t, flags=re.IGNORECASE)
        if m:
            subj = m.group("subj").strip()
            obj = m.group("obj").strip()
            # determine predicate from pattern
            if re.search(r"\b(est|sont)\b", m.group(0), flags=re.IGNORECASE):
                pred = "est"
            elif re.search(r"\b(is|are)\b", m.group(0), flags=re.IGNORECASE):
                pred = "is"
            else:
                pred = ":"  # fallback
            # Do not accept too short subjects or objects
            if len(normalize(subj)) >= 1 and len(normalize(obj)) >= 1:
                return subj, pred, obj
    return None

# =============== Petite heuristique pour détecter info "personnelle" ===============
PERSONAL_KEYWORDS = ["mon ", "ma ", "mes ", "je suis", "moi ", "monnom", "mon nom", "adresse", "né le", "née le", "mon âge", "je m'appelle"]

def looks_personal(text):
    lo = normalize(text)
    for kw in PERSONAL_KEYWORDS:
        if kw in lo:
            return True
    # "je suis <nom>" -> personnel
    if re.search(r"\bje suis\b", lo):
        return True
    return False

# =============== Recherche intelligente dans la connaissance ===============
def find_in_triples(query_norm, triples):
    """Retourne la meilleure correspondance (triple) ou None.
       Matching sur subject_norm OR object_norm, ou token overlap."""
    q = query_norm
    # 1) exact subject or object match
    for t in triples:
        if t.get("subject_norm") == q or t.get("object_norm") == q:
            return t
    # 2) token overlap: check if all words of triple.subject in query
    for t in triples:
        subj_words = set(t.get("subject_norm","").split())
        if subj_words and subj_words.issubset(set(q.split())):
            return t
    # 3) partial overlap: any word match
    for t in triples:
        if any(w in q.split() for w in t.get("subject_norm","").split()):
            return t
    return None

def query_knowledge(query_text, user_id=None):
    """Cherche d'abord dans la mémoire utilisateur (si user_id fourni), puis globalement.
       Retourne une phrase de réponse si trouvé, sinon None."""
    q_norm = normalize(query_text)
    # user memory first
    if user_id:
        utriples = load_user_memory(user_id)
        found = find_in_triples(q_norm, utriples)
        if found:
            # si la triple trouvée a object qui est lui-même sujet d'une autre triple, on peut enchaîner
            obj_n = found.get("object_norm")
            # chercher explication de object dans global knowledge
            g = load_global_knowledge()
            follow = find_in_triples(obj_n, g)
            if follow:
                return f"{found['object']} — {follow['object'] if 'object' in follow else ''}".strip()
            return f"{found['object']}"
    # global knowledge
    g = load_global_knowledge()
    found = find_in_triples(q_norm, g)
    if found:
        # try to expand: if object refers to another triple, include
        obj_n = found.get("object_norm")
        follow = find_in_triples(obj_n, g)
        if follow:
            return f"{found['object']} — {follow['object']}"
        return found['object']
    return None

# =============== Réponse générale et apprentissage avancé ===============
def answer_and_learn(text, user_id):
    """
    - si question (c'est quoi, qu'est-ce que, what is), cherche et répond
    - si déclaration factuelle detectée (X est Y), enregistre (global ou user) selon heuristique
    - sinon cherche correspondance dans knowledge, si rien -> mémorise comme question (avec generic answer)
    """
    t = text.strip()
    t_norm = normalize(t)

    # 1) check question patterns (FR/EN)
    # exemples: "C'est quoi X ?", "Qu'est-ce que X ?", "What is X?"
    q_match = re.match(r"(?i)^\s*(c'est quoi|quest ce que|qu'est ce que|qu'est-ce que|qu'est-ce qu'|qu'est-ce que|what is|what's)\s*(?P<target>.+?)\s*\??\s*$", t)
    if q_match:
        target = q_match.group("target")
        # try direct query of knowledge for target
        found = query_knowledge(target, user_id)
        if found:
            return found
        # else try searching for target as-is
        found2 = query_knowledge(t, user_id)
        if found2:
            return found2
        return "Désolé, je ne connais pas encore la réponse précise à ça — apprends-la moi !"

    # Another question phrasing: "C'est quoi une étoile?" or "C'est quoi le soleil?"
    q2 = re.match(r"(?i)^\s*(?:c'est quoi|c'est|definir|définis|définition de)\s*(?P<target>.+?)\s*\??\s*$", t)
    if q2:
        target = q2.group("target")
        found = query_knowledge(target, user_id)
        if found:
            return found
        return "Je ne connais pas encore ça. Peux-tu me dire ce que c'est ? (ex: 'X est Y')"

    # 2) Try detect declarative fact: "X est Y", "X : Y", "X is Y"
    fact = extract_fact(t)
    if fact:
        subj, pred, obj = fact
        # decide personal or global
        if looks_personal(t):
            add_user_fact(user_id, subj, pred, obj, t)
            return f"Ok, j'ai noté ça pour toi (privé). «{subj}» = «{obj}»."
        else:
            add_global_fact(subj, pred, obj, t)
            return f"Merci — j'ai appris : «{subj}» {pred} «{obj}»."

    # 3) If not a question nor a parsed fact, try to find something similar in knowledge
    found = query_knowledge(t, user_id)
    if found:
        return found

    # 4) fallback: we don't know -> ask user to rephrase as fact or give generic reply and record as unknown
    # Save as "unknown" global question so future might be matched (we store as question->generic answer)
    add_global_fact(t, "is_question", "unknown", t)
    return "Je ne connais pas encore cette question. Tu peux m'expliquer (ex: 'X est Y') ou je m'en souviendrai comme question."

# =============== Frontend (template) ===============
HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Mon IA - avancée</title>
{% raw %}
<style>
body {
    margin: 0;
    padding: 0;
    background: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3') no-repeat center center fixed;
    background-size: cover;
    font-family: Arial, sans-serif;
}
.container {
    max-width: 640px;
    margin: 40px auto;
    background: rgba(10,10,20,0.65);
    color: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 6px 30px rgba(0,0,0,0.6);
}
.header { text-align: center; margin-bottom: 8px; }
.chat-box {
    background: rgba(255,255,255,0.03);
    padding: 12px;
    border-radius: 8px;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 12px;
}
/* bulles */
.msg { display: block; clear: both; padding: 10px 14px; margin: 8px 0; border-radius: 18px; max-width: 80%; }
.user { background: #87CEFA; color: #000; float: right; text-align: right; }
.ai { background: #0b3d91; color: #fff; float: left; text-align: left; }
.form-row { display:flex; gap:8px; align-items:center; }
input[type=text] { flex:1; padding:10px 12px; border-radius:10px; border: none; }
button { padding:10px 14px; border-radius:10px; border:none; background:#1E90FF; color:#fff; cursor:pointer; }
footer { text-align:center; margin-top:10px; font-size:0.9em; color:#ddd; }
small.hint { color:#ddd; font-size:0.9em; display:block; text-align:center; margin-bottom:8px; }
</style>
{% endraw %}
</head>
<body>
<div class="container">
    <div class="header">
        <h2>Mon IA — Version avancée</h2>
        <small class="hint">Tu peux enseigner des faits : "Le soleil est une étoile". Pose ensuite "C'est quoi le soleil ?" </small>
    </div>

    <div class="chat-box" id="chatbox">
        {% for m in chat %}
            {% if m.sender == 'user' %}
                <div class="msg user">{{ m.text }}</div>
            {% else %}
                <div class="msg ai">{{ m.text }}</div>
            {% endif %}
        {% endfor %}
    </div>

    <form method="POST" class="form-row" onsubmit="document.getElementById('send').disabled=true;">
        <input name="question" id="question" placeholder="Pose ta question ou apprends-moi un fait (ex: 'Le soleil est une étoile')" autocomplete="off" required>
        <button id="send" type="submit">Envoyer</button>
    </form>

    <footer>Created by Jules Besson Vollaire</footer>
</div>

<script>
// scroll to bottom
const chatbox = document.getElementById('chatbox');
chatbox.scrollTop = chatbox.scrollHeight;
</script>
</body>
</html>
"""

# =============== Route principale ===============
@app.route("/", methods=["GET", "POST"])
def home():
    # initialise user
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        session["chat"] = []
    user_id = session["user_id"]
    chat = session.get("chat", [])

    if request.method == "POST":
        text = request.form.get("question", "").strip()
        if text:
            # add user message
            chat.append({"sender": "user", "text": text})
            # compute answer (and possibly learn)
            ans = answer_and_learn(text, user_id)
            chat.append({"sender": "ai", "text": ans})
            session["chat"] = chat

    return render_template_string(HTML, chat=chat)

# =============== Run ===============
if __name__ == "__main__":
    # si Render ou environnement définit PORT, tu peux utiliser:
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)






