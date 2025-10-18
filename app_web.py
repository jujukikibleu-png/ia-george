from flask import Flask, request, render_template_string, session
from flask_session import Session
import os
import json
import uuid

# --- Configuration mémoire ---
MEMORY_FOLDER = "user_memories"
os.makedirs(MEMORY_FOLDER, exist_ok=True)
BASE_MEMORY = [
    {"question": "bonjour", "answer": "Bonjour ! Comment vas-tu ?"},
    {"question": "salut", "answer": "Salut ! Ça va ?"},
    {"question": "ça va", "answer": "Super ! Et toi ?"},
    {"question": "comment tu t'appelles", "answer": "Je suis ton IA personnelle, George !"},
]

# --- Fonctions mémoire ---
def get_user_memory_file():
    user_id = session.get("user_id")
    if not user_id:
        user_id = str(uuid.uuid4())
        session["user_id"] = user_id
    return os.path.join(MEMORY_FOLDER, f"{user_id}.json")

def load_memory():
    file = get_user_memory_file()
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory_entry(question, answer):
    memory = load_memory()
    memory.append({"question": question.lower(), "answer": answer})
    with open(get_user_memory_file(), "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def get_memory():
    return BASE_MEMORY + load_memory()

def repondre(question):
    q_lower = question.lower()
    for item in get_memory():
        if item["question"] in q_lower or q_lower in item["question"]:
            return item["answer"]
    answer = f"Je ne connais pas encore cette question, mais je m'en souviendrai !"
    save_memory_entry(question, answer)
    return answer

# --- Flask App ---
app = Flask(__name__)
app.secret_key = "change_this_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

HTML = """
<!doctype html>
<title>Chatbot</title>
{% raw %}
<style>
body {
    margin: 0;
    padding: 0;
    background: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3') no-repeat center center fixed;
    background-size: cover;
    font-family: Arial, sans-serif;
}
#chatbox {
    max-width: 600px;
    margin: 50px auto;
    background: rgba(255,255,255,0.8);
    padding: 20px;
    border-radius: 10px;
}
.bubble {
    padding: 10px;
    margin: 10px;
    border-radius: 10px;
    max-width: 80%;
}
.user { background-color: #1E90FF; color: white; margin-left: auto; }
.ai { background-color: #2F4F4F; color: white; margin-right: auto; }
input[type=text] { width: 80%; padding: 10px; }
input[type=submit] { padding: 10px; }
footer { text-align: center; margin-top: 20px; color: white; }
</style>
{% endraw %}
<div id="chatbox">
<h1>Mon IA</h1>
<form method="POST">
    <input name="question" placeholder="Pose ta question" required>
    <input type="submit" value="Envoyer">
</form>
{% for msg in chat %}
    <div class="bubble user">{{ msg['question'] }}</div>
    <div class="bubble ai">{{ msg['answer'] }}</div>
{% endfor %}
</div>
<footer>Created by Jules Besson Vollaire</footer>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if "chat" not in session:
        session["chat"] = []
    chat = session["chat"]
    if request.method == "POST":
        question = request.form["question"]
        answer = repondre(question)
        chat.append({"question": question, "answer": answer})
        session["chat"] = chat
    return render_template_string(HTML, chat=chat)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)










