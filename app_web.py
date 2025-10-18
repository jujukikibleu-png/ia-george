from flask import Flask, request, render_template_string, session
from flask_session import Session

# Crée l'instance Flask
app = Flask(__name__)

# Configurer les sessions côté serveur (mémoire)
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "une_clef_tres_secrete_pour_la_session"
Session(app)

# Historique simple de réponses connues
default_responses = {
    "bonjour": "Bonjour ! Comment vas-tu ?",
    "salut": "Salut ! Ça va ?",
    "ça va": "Super ! Et toi ?",
    "comment tu t'appelles": "Je suis ton IA personnelle !",
}

# Fonction pour générer une réponse IA
def repondre(question):
    question_lower = question.lower()
    # Cherche une réponse connue
    if question_lower in default_responses:
        return default_responses[question_lower]
    # Sinon réponse générique
    return f"L'IA répond à : {question}"

# HTML avec style
HTML = """
<!doctype html>
<html>
<head>
<title>Chatbot</title>
<style>
body {
    margin: 0;
    font-family: Arial, sans-serif;
    background-image: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3');
    background-size: cover;
    background-attachment: fixed;
}
.container {
    max-width: 600px;
    margin: 50px auto;
    background: rgba(255,255,255,0.8);
    padding: 20px;
    border-radius: 15px;
}
.bubble {
    padding: 10px 15px;
    border-radius: 15px;
    margin: 10px 0;
    display: inline-block;
    max-width: 80%;
}
.user {
    background-color: #1a73e8;
    color: white;
    align-self: flex-end;
}
.ai {
    background-color: #0b3d91;
    color: white;
    align-self: flex-start;
}
.chat {
    display: flex;
    flex-direction: column;
}
footer {
    text-align: center;
    margin-top: 20px;
    font-size: 0.9em;
    color: #333;
}
input[type=text] {
    width: 80%;
    padding: 10px;
    border-radius: 10px;
    border: 1px solid #ccc;
}
input[type=submit] {
    padding: 10px 20px;
    border-radius: 10px;
    border: none;
    background-color: #1a73e8;
    color: white;
    cursor: pointer;
}
</style>
</head>
<body>
<div class="container">
<h1>Mon IA</h1>
<div class="chat">
{% for q, a in chat_history %}
    <div class="bubble user">{{ q }}</div>
    <div class="bubble ai">{{ a }}</div>
{% endfor %}
</div>
<form method="POST">
    <input type="text" name="question" placeholder="Pose ta question" required>
    <input type="submit" value="Envoyer">
</form>
<footer>Created by Jules Besson Vollaire</footer>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if "chat_history" not in session:
        session["chat_history"] = []
    if request.method == "POST":
        question = request.form["question"]
        answer = repondre(question)
        session["chat_history"].append((question, answer))
    return render_template_string(HTML, chat_history=session["chat_history"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)








