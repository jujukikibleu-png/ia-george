from flask import Flask, request, render_template_string
from pyngrok import ngrok

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
        response = f"L'IA répond à : {question}"  # remplacer par ton vrai code IA
    return render_template_string(HTML, response=response)

if __name__ == "__main__":
    # 🔹 Crée un tunnel ngrok aléatoire HTTPS
    public_url = ngrok.connect(5000, bind_tls=True)
    print("Nouvelle URL publique :", public_url)

    # Lancer Flask
    app.run(host="0.0.0.0", port=5000, debug=True)
