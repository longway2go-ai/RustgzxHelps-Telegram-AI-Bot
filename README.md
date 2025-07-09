# 🤖 RustgzxHelps — Telegram AI Bot

RustgzxHelps is a Telegram bot built with `aiogram`, powered by LLaMA 3 via [Groq API](https://groq.com/), and deployed on [Replit](https://replit.com/). It provides fast, smart responses using LLMs — all through Telegram.

---

## 🚀 Features

- ✨ Powered by LLaMA 3 (70B) from Groq
- 🤖 Telegram bot via [aiogram](https://docs.aiogram.dev/)
- 🔐 Secure token handling via Replit Secrets
- ☁️ Fully deployed on **Replit**
- 🔄 Long polling — no webhooks needed
- 🧠 Uses OpenAI-compatible API calls for maximum compatibility

---

## 🧩 Tech Stack

| Tool       | Purpose                              |
|------------|--------------------------------------|
| `aiogram`  | Telegram bot framework (asyncio)     |
| `openai`   | OpenAI client for Groq's LLaMA model |
| `dotenv`   | Loads environment variables (locally)|
| `Replit`   | Deployment platform                  |

---

## 📁 File Structure
# 🤖 RustgzxHelps — Telegram AI Bot

RustgzxHelps is a Telegram bot built with `aiogram`, powered by LLaMA 3 via [Groq API](https://groq.com/), and deployed on [Replit](https://replit.com/). It provides fast, smart responses using LLMs — all through Telegram.

---

## 🚀 Features

- ✨ Powered by LLaMA 3 (70B) from Groq
- 🤖 Telegram bot via [aiogram](https://docs.aiogram.dev/)
- 🔐 Secure token handling via Replit Secrets
- ☁️ Fully deployed on **Replit**
- 🔄 Long polling — no webhooks needed
- 🧠 Uses OpenAI-compatible API calls for maximum compatibility

---

## 🧩 Tech Stack

| Tool       | Purpose                              |
|------------|--------------------------------------|
| `aiogram`  | Telegram bot framework (asyncio)     |
| `openai`   | OpenAI client for Groq's LLaMA model |
| `dotenv`   | Loads environment variables (locally)|
| `Replit`   | Deployment platform                  |

---

## 📁 File Structure

📦 RustgzxHelps/
┣ 📄 main.py # Main bot logic
┣ 📄 requirements.txt # Python dependencies
┣ 📄 README.md # You're reading it :)


---

## 🛠️ Environment Variables (set in Replit Secrets)

| Variable       | Description                        |
|----------------|------------------------------------|
| `BOT_TOKEN`     | Your Telegram Bot Token            |
| `GROQ_API_KEY`  | Groq API key (OpenAI-compatible)   |

In Replit, go to **Tools > Secrets**, and set the above.

---

## ⚙️ Installation (for local development)

```bash
git clone https://github.com/yourusername/RustgzxHelps.git
cd RustgzxHelps
python -m venv venv
source venv/bin/activate     # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python main.py


