#!/usr/bin/env python3
"""
chatbot.py
Simple but robust command-line chatbot using OpenAI Chat Completions.
Features:
- Conversation memory (keeps history, compresses old turns when trop long)
- System prompt customizable
- Save / load conversation
- Fallback to a polite message if API key is missing
Requires: Python 3.10+
"""

import os
import json
import time
from typing import List, Dict
from tqdm import tqdm
from dotenv import load_dotenv

# Load .env (optional)
load_dotenv()

try:
    import openai
except Exception as e:
    raise SystemExit("Install dependencies first: pip install -r requirements.txt") from e

# CONFIG
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # change to gpt-4 if you have access
MAX_MEMORY_TURNS = 12          # number of most recent user/assistant turns to keep
SUMMARY_TRIGGER_TURNS = 20     # when history exceeds this many turns, summarize older ones
CONV_SAVE_PATH = "last_conversation.json"

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY not found in environment. Set OPENAI_API_KEY in ~/.env or environment variables.")
openai.api_key = OPENAI_API_KEY

# System prompt - change as you like
SYSTEM_PROMPT = (
    "Tu es un assistant conversationnel utile, concentré et créatif. Répond de façon claire, concise et polie. "
    "Si l'utilisateur demande du code, fournis un exemple exécutable et explique brièvement. "
)

# Helpers
def save_conversation(messages: List[Dict], path: str = CONV_SAVE_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    print(f"[saved conversation → {path}]")

def load_conversation(path: str = CONV_SAVE_PATH) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_messages(messages: List[Dict], keep_recent: int = MAX_MEMORY_TURNS) -> List[Dict]:
    """
    Compress older messages into a short summary using the model,
    keeping the most recent `keep_recent` turns intact.
    """
    if len(messages) <= SUMMARY_TRIGGER_TURNS:
        return messages

    # Build prompt to summarize older messages (everything except recent)
    older = messages[:-keep_recent]
    recent = messages[-keep_recent:]
    text_to_summarize = []
    for m in older:
        role = m.get("role")
        content = m.get("content", "")
        text_to_summarize.append(f"{role}: {content}")
    big_text = "\n".join(text_to_summarize)[:20000]  # safety clip

    prompt = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            "Résume de façon courte et structurée (3-6 lignes) le contexte suivant et les informations importantes "
            "que l'assistant doit retenir pour la suite de la conversation. Ne liste pas chaque message, mais extrait "
            "les faits, préférences et objectifs de l'utilisateur :\n\n" + big_text
        )}
    ]

    try:
        resp = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,
            messages=prompt,
            max_tokens=300,
            temperature=0.3,
        )
        summary = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[WARN] échec du résumé automatique:", e)
        # fallback: simple manual short summary
        summary = "Résumé automatique indisponible — l'historique contient des échanges nombreux."

    # Create a compact "system" message encoding the summary + keep recent
    summarized_message = {"role": "system", "content": "Contexte résumé : " + summary}
    return [summarized_message] + recent

def build_messages(history: List[Dict], user_text: str) -> List[Dict]:
    # Start from system prompt unless history already contains a system message
    if not any(m["role"] == "system" for m in history):
        base = [{"role": "system", "content": SYSTEM_PROMPT}]
    else:
        base = []

    msgs = base + history + [{"role": "user", "content": user_text}]
    return msgs

def chat_once(history: List[Dict], user_text: str) -> Dict:
    messages = build_messages(history, user_text)
    # If messages very long, compress
    if len(messages) > SUMMARY_TRIGGER_TURNS:
        history = summarize_messages(history, keep_recent=MAX_MEMORY_TURNS)
        messages = build_messages(history, user_text)

    # Call the API
    try:
        resp = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            n=1,
        )
        assistant_msg = resp["choices"][0]["message"]["content"].strip()
        return {"role": "assistant", "content": assistant_msg}
    except Exception as e:
        return {"role": "assistant", "content": f"[Erreur API] {e}"}

def cli_loop():
    print("=== Chatbot CLI — tape '/help' pour les commandes. Ctrl+C pour quitter. ===")
    history = load_conversation()
    if history:
        print(f"[conversation chargée, {len(history)} messages]")

    while True:
        try:
            user_in = input("\nToi: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAu revoir 👋")
            break

        if not user_in:
            continue

        # Commands
        if user_in.startswith("/"):
            cmd = user_in.lower()
            if cmd == "/help":
                print(
                    "/help      -> afficher cette aide\n"
                    "/save      -> sauvegarder la conversation\n"
                    "/load      -> recharger la dernière conversation\n"
                    "/clear     -> effacer l'historique en mémoire\n"
                    "/history   -> afficher résumé de l'historique\n"
                    "/exit      -> quitter\n"
                )
                continue
            elif cmd == "/save":
                save_conversation(history)
                continue
            elif cmd == "/load":
                history = load_conversation()
                print("[conversation chargée]")
                continue
            elif cmd == "/clear":
                history = []
                print("[historique vidé]")
                continue
            elif cmd == "/history":
                print(f"[messages en mémoire: {len(history)}]")
                for i, m in enumerate(history[-MAX_MEMORY_TURNS:]):
                    print(f"{i+1}. {m['role']}: {m['content'][:120].replace('\\n',' ')}")
                continue
            elif cmd == "/exit":
                save_conversation(history)
                print("Bye.")
                break
            else:
                print("Commande inconnue. Tape /help.")
                continue

        # Otherwise normal chat flow
        # Add user message
        history.append({"role": "user", "content": user_in})
        # Get assistant response
        assistant_msg = chat_once([m for m in history if m["role"] != "system"], user_in)
        print("\nBot:", assistant_msg["content"])
        history.append(assistant_msg)

        # Keep history size reasonable
        if len(history) > 200:
            history = summarize_messages(history, keep_recent=MAX_MEMORY_TURNS)

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("Erreur : aucune clé OpenAI. Pour utiliser ce chatbot, exporte OPENAI_API_KEY dans ton environnement.")
        print("Exemple (Linux/macOS): export OPENAI_API_KEY='ta_cle'  ou crée un fichier .env avec OPENAI_API_KEY=ta_cle")
        # We'll let the user still interact but responses will fail gracefully when calling API.
    try:
        cli_loop()
    except Exception as e:
        print("Erreur inattendue:", e)
