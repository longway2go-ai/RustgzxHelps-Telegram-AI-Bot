import os
import asyncio
import logging
import json
import aiohttp
from typing import List, Dict
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import openai

# Environment variables from Replit secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SERP_API_KEY = os.environ.get("SERP_API_KEY")

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("Missing required environment variables.")

# Configure OpenAI client (Groq)
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
model = "llama3-70b-8192"

class Reference:
    def __init__(self):
        self.response = ""
        self.conversation_history = []

reference = Reference()

# ------------------ Search & Book Tools ------------------

async def search_links(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    try:
        async with aiohttp.ClientSession() as session:
            if SERP_API_KEY:
                params = {'engine': 'google', 'q': query, 'api_key': SERP_API_KEY, 'num': num_results}
                async with session.get('https://serpapi.com/search', params=params) as res:
                    if res.status == 200:
                        data = await res.json()
                        return [{
                            'title': r.get('title', ''),
                            'link': r.get('link', ''),
                            'snippet': r.get('snippet', '')
                        } for r in data.get('organic_results', [])[:num_results]]
            else:
                params = {'q': query, 'format': 'json', 'no_html': '1', 'skip_disambig': '1'}
                async with session.get('https://api.duckduckgo.com/', params=params) as res:
                    if res.status == 200:
                        data = await res.json()
                        return [{
                            'title': t.get('Text', '').split(' - ')[0],
                            'link': t.get('FirstURL', ''),
                            'snippet': t.get('Text', '')
                        } for t in data.get('RelatedTopics', [])[:num_results] if isinstance(t, dict)]
    except Exception as e:
        logging.warning(f"Search error: {e}")
    return []

def get_book_recommendations(topic: str) -> List[Dict[str, str]]:
    db = {
        'python': [
            {'title': 'Automate the Boring Stuff', 'author': 'Al Sweigart', 'link': 'https://automatetheboringstuff.com/'},
            {'title': 'Python Crash Course', 'author': 'Eric Matthes', 'link': 'https://nostarch.com/pythoncrashcourse2e'},
            {'title': 'Fluent Python', 'author': 'Luciano Ramalho', 'link': 'https://www.oreilly.com/library/view/fluent-python/9781491946237/'}
        ],
        'machine learning': [
            {'title': 'Hands-On ML', 'author': 'Aurélien Géron', 'link': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/'},
            {'title': 'PRML', 'author': 'Christopher Bishop', 'link': 'https://www.microsoft.com/en-us/research/people/cmbishop/prml-book/'}
        ]
    }
    topic = topic.lower()
    for k, books in db.items():
        if k in topic:
            return books
    return [{
        'title': f'Search "{topic}" on Amazon',
        'author': 'Various',
        'link': f'https://www.amazon.com/s?k={topic.replace(" ", "+")}'
    }]

def create_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "search_links",
                "description": "Search online resources",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "num_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_book_recommendations",
                "description": "Get book suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"}
                    },
                    "required": ["topic"]
                }
            }
        }
    ]

async def handle_tool_calls(tool_calls, message: Message):
    for tool_call in tool_calls:
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])
        if name == "search_links":
            await message.answer("🔍 Searching the web...")
            links = await search_links(args["query"], args.get("num_results", 5))
            if links:
                response = f"🌐 **Top results for '{args['query']}':**\n\n"
                for i, l in enumerate(links, 1):
                    response += f"{i}. [{l['title']}]({l['link']})\n"
                    if l['snippet']:
                        response += f"   _{l['snippet'][:100]}..._\n\n"
                await message.answer(response, parse_mode="Markdown")
            else:
                await message.answer("❌ No results found.")
        elif name == "get_book_recommendations":
            await message.answer("📚 Looking up book recommendations...")
            books = get_book_recommendations(args["topic"])
            response = f"📘 **Recommended reads on '{args['topic']}':**\n\n"
            for i, b in enumerate(books, 1):
                response += f"{i}. [{b['title']}]({b['link']}) — _{b['author']}_\n\n"
            await message.answer(response, parse_mode="Markdown")

# ------------------ Bot Commands ------------------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 **Welcome to your AI assistant!**\n\n"
        "I'm a Groq-powered bot based on LLaMA3.\n"
        "I can help you with info, links, books & more.\n\n"
        "🧠 Just ask me questions or use commands like:\n"
        "`/search python`\n"
        "`/books machine learning`\n\n"
        "✨ _Created with ❤️ by Arnab_",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help(message: Message):
    await message.answer(
        "🛠 **Bot Commands:**\n"
        "`/start` – Welcome message\n"
        "`/help` – This help screen\n"
        "`/search <query>` – Search online\n"
        "`/books <topic>` – Get book recommendations\n\n"
        "💡 Just chat with me! Ask questions like:\n"
        "_“Recommend books on AI”_\n"
        "_“Find sources about quantum computing”_\n\n"
        "🤖 Powered by LLaMA3 via Groq\n"
        "👨‍💻 Created by *Arnab*",
        parse_mode="Markdown"
    )

@dp.message(Command("search"))
async def search_cmd(message: Message):
    query = message.text.replace("/search", "").strip()
    if not query:
        return await message.answer("❗ Usage: `/search python programming`", parse_mode="Markdown")
    links = await search_links(query)
    if links:
        text = f"🔍 **Search results for `{query}`:**\n\n"
        for i, l in enumerate(links, 1):
            text += f"{i}. [{l['title']}]({l['link']})\n"
            if l.get('snippet'):
                text += f"   _{l['snippet'][:100]}..._\n\n"
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("❌ No results found.")

@dp.message(Command("books"))
async def books_cmd(message: Message):
    topic = message.text.replace("/books", "").strip()
    if not topic:
        return await message.answer("❗ Usage: `/books data science`", parse_mode="Markdown")
    books = get_book_recommendations(topic)
    response = f"📚 **Books on `{topic}`:**\n\n"
    for i, b in enumerate(books, 1):
        response += f"{i}. [{b['title']}]({b['link']}) — _{b['author']}_\n\n"
    await message.answer(response, parse_mode="Markdown")

# ------------------ Main Chat Handler ------------------

@dp.message()
async def chat(message: Message):
    user_input = message.text
    reference.conversation_history.append({"role": "user", "content": user_input})
    reference.conversation_history = reference.conversation_history[-6:]

    try:
        tools = create_tools()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are a helpful, friendly assistant."}] + reference.conversation_history,
            temperature=0.7,
            tools=tools,
            tool_choice="auto"
        )

        reply = response.choices[0]["message"].get("content")
        tool_calls = response.choices[0]["message"].get("tool_calls")

        if reply:
            await message.answer(f"💬 {reply[:4000]}")
            reference.conversation_history.append({"role": "assistant", "content": reply})

        if tool_calls:
            await handle_tool_calls(tool_calls, message)

    except Exception as e:
        logging.error(f"Bot error: {e}")
        await message.answer("⚠️ Oops! Something went wrong. Please try again.")

# ------------------ Entrypoint ------------------

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🚀 Bot is running! Powered by Groq + LLaMA3")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
