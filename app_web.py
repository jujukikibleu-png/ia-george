from flask import Flask, request, render_template_string
import json
import os

# --- Mémoire --- #
MEMORY_FILE = "memory.json"

base_memory = [
    {"question": "bonjour", "answer": "Bonjour ! Comment vas-tu ?"},
    {"question": "salut", "answer": "Salut ! Comment ça va ?"},
    {"question": "comment vas-tu", "answer": "Je vais bien, merci ! Et toi ?"},
    {"question": "ça va", "answer": "Ça va très bien, merci ! Et toi ?"},
    {"question": "merci", "answer": "Avec plaisir !"},
    {"question": "au revoir", "answer": "Au revoir ! À bientôt !"}
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
            display: flex;
            justify-content: center;
            padding-top: 50px;
            color: white;
        }
        .chat-container {
            background: rgba(0, 0, 0, 0.6);
            padding: 20px;
            border-radius: 15px;
            width: 400px;
            box-shadow: 0 0 10px black;
        }
        input[type=text] {
            width: 80%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 20px;
            border: none;
        }
        input[type=submit] {
            padding: 10px 20px;
            border-radius: 20px;
            border: none;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
        }
        .message {
            padding: 10px 15px;
            margin: 5px;
            border-radius: 20px;
            max-width: 80%;
            clear: both;
        }
        .user {
            background-color: #87CEFA;  /* bleu clair pour toi */
            float: right;
            color: black;
        }
        .bot {
            background-color: #1E3A8A;  /* bleu foncé pour l'IA */
            float: left;
            color: white;
        }
        footer {
            text-align: center;
            font-size: 14px;
            color: #fff;
            margin-top: 20px;
        }
        .chat-box {
            max-height: 300px;
            overflow-y: auto;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Mon IA</h2>
        <div class="chat-box" id="chat-box">
            {% for q, a in chat_history %}
                <div class="message user">{{ q }}</div>
                <div class="message bot">{{ a }}</div>
            {% endfor %}
        </div>
        <form method="POST">
            <input name="question" placeholder="Pose ta question" required>
            <input type="submit" value="Envoyer">
        </form>
        <footer>Created by Jules Besson Vollaire</footer>
    </div>
    <script>
        // Scroll automatique vers le dernier message
        var chatBox = document.getElementById("chat-box");
        chatBox.scrollTop = chatBox.scrollHeight;
    </script>
</body>
</html>
"""

chat_history = []

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        question = request.form["question"]
        answer = repondre(question)
        chat_history.append((question, answer))
    return render_template_string(HTML, chat_history=chat_history)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)







