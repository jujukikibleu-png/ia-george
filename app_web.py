from flask import Flask, request, render_template_string
import os

# Crée l'instance Flask
app = Flask(__name__)

HTML = """
<!doctype html>
<title>Chatbot</title>
<h1>Mon IA</h1>
<form method="POST">
    <input name="question" placeholder="Pose ta question">
    <input type="submit" value="Envoyer">
</form>
<p>{{ response }}</p>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    response = ""
    if request.method == "POST":
        question = request.form["question"]
        # Ici on appelle ta fonction IA pour générer une réponse
        # response = repondre(question)
        response = f"L'IA répond à : {question}"  # temporaire pour tester
    return render_template_string(HTML, response=response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

