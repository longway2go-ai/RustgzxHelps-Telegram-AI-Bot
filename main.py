import os
import asyncio
import logging
import json
import aiohttp
from typing import List, Dict
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from openai import OpenAI

# Load .env variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")  # Optional: for enhanced search results

if not TELEGRAM_BOT_TOKEN or not GROQ_API_KEY:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN or GROQ_API_KEY")

# Initialize Groq API client
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# In-memory chat history
class Reference:
    def __init__(self):
        self.response = ""
        self.conversation_history = []

reference = Reference()
model = "llama3-70b-8192"

# Initialize bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Tool functions
async def search_links(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """Search for relevant links using DuckDuckGo or SERP API"""
    try:
        if SERP_API_KEY:
            # Use SERP API if available
            async with aiohttp.ClientSession() as session:
                params = {
                    'engine': 'google',
                    'q': query,
                    'api_key': SERP_API_KEY,
                    'num': num_results
                }
                async with session.get('https://serpapi.com/search', params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for result in data.get('organic_results', [])[:num_results]:
                            results.append({
                                'title': result.get('title', ''),
                                'link': result.get('link', ''),
                                'snippet': result.get('snippet', '')
                            })
                        return results
        
        # Fallback to DuckDuckGo search (free alternative)
        async with aiohttp.ClientSession() as session:
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            async with session.get('https://api.duckduckgo.com/', params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    # Get related topics
                    for topic in data.get('RelatedTopics', [])[:num_results]:
                        if isinstance(topic, dict) and 'FirstURL' in topic:
                            results.append({
                                'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                                'link': topic.get('FirstURL', ''),
                                'snippet': topic.get('Text', '')
                            })
                    
                    return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_book_recommendations(topic: str) -> List[Dict[str, str]]:
    """Get book recommendations based on topic"""
    # Predefined book recommendations for common topics
    book_database = {
        'python': [
            {'title': 'Automate the Boring Stuff with Python', 'author': 'Al Sweigart', 'link': 'https://automatetheboringstuff.com/'},
            {'title': 'Python Crash Course', 'author': 'Eric Matthes', 'link': 'https://nostarch.com/pythoncrashcourse2e'},
            {'title': 'Fluent Python', 'author': 'Luciano Ramalho', 'link': 'https://www.oreilly.com/library/view/fluent-python/9781491946237/'}
        ],
        'machine learning': [
            {'title': 'Hands-On Machine Learning', 'author': 'Aurélien Géron', 'link': 'https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/'},
            {'title': 'Pattern Recognition and Machine Learning', 'author': 'Christopher Bishop', 'link': 'https://www.microsoft.com/en-us/research/people/cmbishop/prml-book/'},
            {'title': 'The Elements of Statistical Learning', 'author': 'Hastie, Tibshirani, Friedman', 'link': 'https://web.stanford.edu/~hastie/ElemStatLearn/'}
        ],
        'data science': [
            {'title': 'Python for Data Analysis', 'author': 'Wes McKinney', 'link': 'https://wesmckinney.com/book/'},
            {'title': 'Data Science from Scratch', 'author': 'Joel Grus', 'link': 'https://www.oreilly.com/library/view/data-science-from/9781492041122/'},
            {'title': 'R for Data Science', 'author': 'Hadley Wickham', 'link': 'https://r4ds.had.co.nz/'}
        ],
        'artificial intelligence': [
            {'title': 'Artificial Intelligence: A Modern Approach', 'author': 'Stuart Russell, Peter Norvig', 'link': 'http://aima.cs.berkeley.edu/'},
            {'title': 'Life 3.0', 'author': 'Max Tegmark', 'link': 'https://space.mit.edu/home/tegmark/life3.0.html'},
            {'title': 'Superintelligence', 'author': 'Nick Bostrom', 'link': 'https://www.amazon.com/Superintelligence-Dangers-Strategies-Nick-Bostrom/dp/0198739834'}
        ]
    }
    
    # Find matching books
    topic_lower = topic.lower()
    for key, books in book_database.items():
        if key in topic_lower or any(word in topic_lower for word in key.split()):
            return books
    
    # Generic recommendations if no specific match
    return [
        {'title': f'Search "{topic}" on Amazon', 'author': 'Various Authors', 'link': f'https://www.amazon.com/s?k={topic.replace(" ", "+")}&i=stripbooks'},
        {'title': f'Search "{topic}" on Goodreads', 'author': 'Various Authors', 'link': f'https://www.goodreads.com/search?q={topic.replace(" ", "+")}'},
        {'title': f'Search "{topic}" on Google Books', 'author': 'Various Authors', 'link': f'https://books.google.com/books?q={topic.replace(" ", "+")}'}
    ]

def create_tools_for_llm():
    """Define tools that the LLM can use"""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_links",
                "description": "Search for relevant links and resources on the internet for a given topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query or topic to find links for"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of search results to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_book_recommendations",
                "description": "Get book recommendations for a specific topic or subject",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic or subject to get book recommendations for"
                        }
                    },
                    "required": ["topic"]
                }
            }
        }
    ]

async def handle_tool_calls(tool_calls, message: Message):
    """Handle tool function calls"""
    results = []
    
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        if function_name == "search_links":
            query = function_args.get("query")
            num_results = function_args.get("num_results", 5)
            
            await message.answer("🔍 Searching for relevant links...")
            
            links = await search_links(query, num_results)
            if links:
                response = f"🔗 **Found {len(links)} relevant links for '{query}':**\n\n"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                
                for i, link in enumerate(links, 1):
                    response += f"{i}. **{link['title']}**\n"
                    if link['snippet']:
                        response += f"   _{link['snippet'][:100]}..._\n"
                    response += f"   🔗 [View Link]({link['link']})\n\n"
                    
                    # Add inline button
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(text=f"📖 {link['title'][:30]}...", url=link['link'])
                    ])
                
                await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer("❌ No links found for this topic.")
        
        elif function_name == "get_book_recommendations":
            topic = function_args.get("topic")
            
            await message.answer("📚 Finding book recommendations...")
            
            books = get_book_recommendations(topic)
            if books:
                response = f"📚 **Book recommendations for '{topic}':**\n\n"
                keyboard = InlineKeyboardMarkup(inline_keyboard=[])
                
                for i, book in enumerate(books, 1):
                    response += f"{i}. **{book['title']}**\n"
                    response += f"   👤 Author: {book['author']}\n"
                    response += f"   🔗 [View Book]({book['link']})\n\n"
                    
                    # Add inline button
                    keyboard.inline_keyboard.append([
                        InlineKeyboardButton(text=f"📖 {book['title'][:30]}...", url=book['link'])
                    ])
                
                await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
            else:
                await message.answer("❌ No book recommendations found for this topic.")

# Commands
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "👋 Welcome! I'm an enhanced Groq-powered LLaMA3 bot.\n\n"
        "🔧 **New Features:**\n"
        "• 🔍 I can search for relevant links\n"
        "• 📚 I can recommend books on topics\n"
        "• 💬 Just ask me anything and I'll provide sources!\n\n"
        "Type /help for more commands."
    )

@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "📌 **Commands:**\n"
        "/start - Begin a new chat\n"
        "/clear - Clear previous memory\n"
        "/search <topic> - Search for links on a topic\n"
        "/books <topic> - Get book recommendations\n"
        "/help - Show this message\n\n"
        "💬 **Features:**\n"
        "• Ask any question and I'll provide sources\n"
        "• Request links: 'Can you find links about Python?'\n"
        "• Request books: 'Recommend books on machine learning'\n"
        "• I automatically detect when to provide additional resources!",
        parse_mode="Markdown"
    )

@dp.message(Command("clear"))
async def clear_handler(message: Message):
    reference.response = ""
    reference.conversation_history = []
    await message.answer("🧹 Conversation cleared.")

@dp.message(Command("search"))
async def search_command(message: Message):
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.answer("❌ Please provide a search query. Example: /search python programming")
        return
    
    links = await search_links(query)
    if links:
        response = f"🔍 **Search results for '{query}':**\n\n"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        
        for i, link in enumerate(links, 1):
            response += f"{i}. **{link['title']}**\n"
            if link['snippet']:
                response += f"   _{link['snippet'][:100]}..._\n"
            response += f"   🔗 [View Link]({link['link']})\n\n"
            
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=f"📖 {link['title'][:30]}...", url=link['link'])
            ])
        
        await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await message.answer("❌ No search results found.")

@dp.message(Command("books"))
async def books_command(message: Message):
    topic = message.text.replace("/books", "").strip()
    if not topic:
        await message.answer("❌ Please provide a topic. Example: /books machine learning")
        return
    
    books = get_book_recommendations(topic)
    response = f"📚 **Book recommendations for '{topic}':**\n\n"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, book in enumerate(books, 1):
        response += f"{i}. **{book['title']}**\n"
        response += f"   👤 Author: {book['author']}\n"
        response += f"   🔗 [View Book]({book['link']})\n\n"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"📖 {book['title'][:30]}...", url=book['link'])
        ])
    
    await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)

# Main chat handler with tool support
@dp.message()
async def message_handler(message: Message):
    user_input = message.text
    print(f">>> USER: {user_input}")
    
    try:
        # Build conversation history
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant. When users ask questions, you can use tools to provide relevant links and book recommendations. Always try to be helpful and provide comprehensive answers. If a user's question would benefit from additional resources, proactively suggest using the search_links or get_book_recommendations tools."
            }
        ]
        
        # Add conversation history
        messages.extend(reference.conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        # Check if the user is asking for links or books
        needs_tools = any(keyword in user_input.lower() for keyword in [
            'link', 'source', 'reference', 'find', 'search', 'book', 'recommend', 'read', 'learn more'
        ])
        
        tools = create_tools_for_llm() if needs_tools else None
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
            tools=tools,
            tool_choice="auto" if tools else None
        )
        
        reply = response.choices[0].message.content
        tool_calls = response.choices[0].message.tool_calls
        
        # Handle regular response
        if reply:
            # Update conversation history
            reference.conversation_history.append({"role": "user", "content": user_input})
            reference.conversation_history.append({"role": "assistant", "content": reply})
            
            # Keep only last 10 messages to avoid token limits
            if len(reference.conversation_history) > 10:
                reference.conversation_history = reference.conversation_history[-10:]
            
            reference.response = reply
            print(f">>> BOT: {reply}")
            await message.answer(reply[:4096])
        
        # Handle tool calls
        if tool_calls:
            await handle_tool_calls(tool_calls, message)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        await message.answer("⚠️ Something went wrong. Please try again.")

# Entrypoint
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Bot starting with enhanced search and book recommendation features...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
