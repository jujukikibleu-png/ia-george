from flask import Flask, request, render_template_string
import json
import os

# --- Mémoire --- #
MEMORY_FILE = "memory.json"

# Mémoire de base
base_memory = [
    {"question": "bonjour", "answer": "Bonjour ! Comment vas-tu ?"},
    {"question": "salut", "answer": "Salut ! Comment ça va ?"},
    {"question": "comment vas-tu", "answer": "Je vais bien, merci ! Et toi ?"},
    {"question": "ça va", "answer": "Ça va très bien, merci ! Et toi ?"},
    {"question": "merci", "answer": "Avec plaisir !"},
    {"question": "au revoir", "answer": "Au revoir ! À bientôt !"}
]

# Charge la mémoire depuis le fichier
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

# Sauvegarde la mémoire dans le fichier
def save_memory_entry(question, answer):
    memory = load_memory()
    memory.append({"question": question.lower(), "answer": answer})
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# Retourne toute la mémoire combinée (base + utilisateur)
def get_memory():
    return base_memory + load_memory()

# Fonction pour générer une réponse
def repondre(question):
    question_lower = question.lower()
    for item in get_memory():
        if item["question"] in question_lower or question_lower in item["question"]:
            return item["answer"]
    # Si inconnu, mémorise et répond génériquement
    answer = f"Je ne connais pas encore cette question, mais je m'en souviendrai !"
    save_memory_entry(question, answer)
    return answer

# --- Flask --- #
app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
    <title>Chatbot</title>
    <style>
        body {
            background-image: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3');
            background-size: cover;
            font-family: Arial, sans-serif;
            color: white;
            text-align: center;
            padding-top: 50px;
        }
        input[type=text] {
            width: 300px;
            padding: 10px;
            margin: 10px;
        }
        input[type=submit] {
            padding: 10px 20px;
            cursor: pointer;
        }
        p {
            font-size: 18px;
        }
        form {
            margin-bottom: 30px;
        }
        footer {
            position: fixed;
            bottom: 10px;
            width: 100%;
            text-align: center;
            font-size: 14px;
            color: #fff;
        }
    </style>
</head>
<body>
    <h1>Mon IA</h1>
    <form method="POST">
        <input name="question" placeholder="Pose ta question" required>
        <input type="submit" value="Envoyer">
    </form>
    <p>{{ response }}</p>
    <footer>Created by Jules Besson Vollaire</footer>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    response = ""
    if request.method == "POST":
        question = request.form["question"]
        response = repondre(question)
    return render_template_string(HTML, response=response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)





