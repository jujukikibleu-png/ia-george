from flask import Flask, request, render_template_string, session
from flask_session import Session
import os, json, uuid

app = Flask(__name__)
app.secret_key = "ton_secret_key"
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

MEMORY_FILE = "memory.json"

# Mémoire globale avec réponses de base
base_memory = [
    {"question": "bonjour", "answer": "Bonjour ! Comment vas-tu ?"},
    {"question": "salut", "answer": "Salut ! Ça va ?"},
    {"question": "ça va", "answer": "Super ! Et toi ?"},
    {"question": "comment tu t'appelles", "answer": "Je suis ton IA personnelle, George !"}
]

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []

def save_memory_entry(question, answer):
    memory = load_memory()
    memory.append({"question": question.lower(), "answer": answer})
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def get_memory():
    return base_memory + load_memory()

def repondre(question):
    question_lower = question.lower()
    for item in get_memory():
        if item["question"] in question_lower or question_lower in item["question"]:
            return item["answer"]
    answer = f"Je ne connais pas encore cette question, mais je m'en souviendrai !"
    save_memory_entry(question, answer)
    return answer

HTML = """
<!doctype html>
<title>Chatbot</title>
<style>
body {{
    margin: 0;
    padding: 0;
    background: url('https://tse4.mm.bing.net/th/id/OIP.Lq7aFYBXxxO5aSAeDK9jGgHaD4?cb=12&rs=1&pid=ImgDetMain&o=7&rm=3') no-repeat center center fixed;
    background-size: cover;
    font-family: Arial, sans-serif;
}}
#chatbox {{
    max-width: 600px;
    margin: 50px auto;
    background: rgba(255,255,255,0.8);
    padding: 20px;
    border-radius: 10px;
}}
.bubble {{
    padding: 10px;
    margin: 10px;
    border-radius: 10px;
    max-width: 80%;
}}
.user {{ background-color: #1E90FF; color: white; margin-left: auto; }}
.ai {{ background-color: #2F4F4F; color: white; margin-right: auto; }}
input[type=text] {{ width: 80%; padding: 10px; }}
input[type=submit] {{ padding: 10px; }}
footer {{ text-align: center; margin-top: 20px; color: white; }}
</style>
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
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
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










