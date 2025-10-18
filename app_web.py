import os
import json
from flask import Flask, request, render_template_string

app = Flask(__name__)
data_file = "memory.json"

# Mémoire de base
base_memory = [
    {"question": "bonjour", "answer": "Bonjour ! Comment vas-tu aujourd'hui ?"},
    {"question": "salut", "answer": "Salut ! Comment ça va ?"},
    {"question": "ça va", "answer": "Je vais bien, merci ! Et toi ?"},
    {"question": "merci", "answer": "Avec plaisir !"},
    {"question": "au revoir", "answer": "Au revoir ! À bientôt !"}
]

# Initialiser memory.json si vide
if not os.path.exists(data_file):
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(base_memory, f, ensure_ascii=False, indent=2)

# Fonction pour récupérer la mémoire
def get_memory():
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Fonction pour sauvegarder une info
def save_memory(question, answer):
    memory = get_memory()
    memory.append({"question": question, "answer": answer})
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# Fonction qui répond intelligemment
def repondre(question):
    question_lower = question.lower()
    for item in get_memory():
        if question_lower in item["question"].lower() or item["question"].lower() in question_lower:
            return item["answer"]
    # Sinon, réponse générique et on mémorise
    answer = f"L'IA répond à : {question}"
    save_memory(question, answer)
    return answer
HTML = """
<!doctype html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Mon IA</title>
<style>
body {
    font-family: Arial, sans-serif;
    background-image: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    color: #FFFFFF;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
}
.chat-container {
    background-color: rgba(46,46,62,0.85);
    padding: 20px;
    border-radius: 15px;
    width: 90%;
    max-width: 500px;
    box-shadow: 0 0 10px rgba(0,0,0,0.5);
}
h1 { text-align: center; color: #00FFFF; }
form { display: flex; gap: 10px; margin-top: 10px; }
input[type="text"] { flex: 1; padding: 10px; border-radius: 10px; border: none; }
input[type="submit"], button {
    padding: 10px 15px;
    border: none;
    border-radius: 10px;
    background-color: #00FFFF;
    color: #000;
    cursor: pointer;
    font-weight: bold;
}
.chat-box {
    background-color: #1B1B2F;
    padding: 10px;
    border-radius: 10px;
    margin-top: 15px;
    max-height: 300px;
    overflow-y: auto;
}
.user { color: #FFD700; }
.ai { color: #00FFFF; }
</style>
</head>
<body>
<div class="chat-container">
<h1>Mon IA</h1>
<div class="chat-box">
    {% if question %}
        <p class="user"><b>Vous :</b> {{ question }}</p>
        <p class="ai"><b>IA :</b> {{ response }}</p>
    {% endif %}
</div>
<form method="POST">
    <input name="question" placeholder="Pose ta question" required>
    <input type="submit" value="Envoyer">
</form>
<form method="GET">
    <button>Effacer la conversation</button>
</form>
</div>
</body>
</html>
"""
@app.route("/", methods=["GET", "POST"])
def home():
    response = ""
    question = ""
    if request.method == "POST":
        question = request.form["question"]
        response = repondre(question)  # réponse intelligente
    return render_template_string(HTML, response=response, question=question)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




