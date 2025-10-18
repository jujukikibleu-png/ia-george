from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>George l'IA</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1E1E2F;
            color: #FFFFFF;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .chat-container {
            background-color: #2E2E3E;
            padding: 20px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
        }
        h1 {
            text-align: center;
            color: #00FFFF;
        }
        form {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 10px;
            border-radius: 10px;
            border: none;
        }
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
        <h1>George</h1>
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
        # Appelle ici ta fonction IA réelle
        # response = repondre(question)
        response = f"L'IA répond à : {question}"
    return render_template_string(HTML, response=response, question=question)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

