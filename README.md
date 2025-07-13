# 🔱 Agent Vyāsa — The Conversational Memory Oracle

> _"Speak, and I shall listen. Ask, and I shall retrieve."_

**Agent Vyāsa** is a CLI-based intelligent agent that merges memory, retrieval, and real-time inference to create a human-like conversation experience. Designed for deep inquiry, historical memory recall, and source-based answers, Vyāsa is not just a chatbot — it's an evolving digital companion.

---

## ✨ Features

### 🧠 Semantic Memory with Redis
- Stores and retrieves semantically indexed conversations.
- Memory is trimmed and rotated to preserve context without overloading.
- Memory retrieval works via keyword query or automated loading on session resume.

### 🧾 Chat Session Management
- Each chat is treated as a **session** identified by a UUID.
- Users can:
  - `✨ create session` — Start a new chat with a title.
  - `📂 select session` — Resume from existing saved chats.
  - `🧠 load memory` — Inject past context into the current session.

### 🔍 Deep Search: Tathya
- Ask `Tathya: <your query>` to invoke RAG (Retrieval-Augmented Generation).
- Uses external sources and memory to form rich, contextually backed answers.

### 🧭 Beautiful CLI Interface
- Built using `rich` for stunning visuals:
  - Boxed panels for welcome messages.
  - Center-aligned instructions.
  - Colored session listings and guide menu.

### 🧰 Modular Architecture
- Node-based execution (`bot_node`, `tathya_node`, etc.).
- Redis for fast cache.
- PostgreSQL via SQLAlchemy for long-term storage.
- LangChain + Ollama (Mistral) as the LLM interface.

---

## 🧠 Memory Architecture

```txt
┌───────────────────────────────┐
│          Chatbot Agent        │
│        (LangChain + LLM)      │
└──────────────┬────────────────┘
               │
         ┌─────▼─────┐
         │   Redis   │ ◄───► Semantic Cache (Recent Context: 20 Messages Max)
         └─────┬─────┘
               │
        ┌──────▼──────┐
        │ PostgreSQL  │ ◄───► Long-Term Storage (ChatSessions, ChatMessages)
        └─────────────┘

- Short-Term Memory: Redis stores the last 20 messages for blazing fast access.
- Long-Term Memory: Synced to PostgreSQL when session ends or memory is flushed.
- Context Injection: RAG can enrich context from memory or external tools (via Tathya).


🖥️ CLI Command Guide
- ✨ new session        → Begin a fresh chat thread.
- 📂 select session     → View and resume past chats.
- 🧠 load memory        → Inject remembered messages into current context.
- 🔍 Tathya: <query>    → Perform RAG-based answer with external search.
- 🧭 menu               → Show this command menu again.
- ❌ end                → Close the session and flush memory if needed.

## 🏗️ Stack Used

- 🧠 **[LangChain](https://www.langchain.com/)**  
  Framework for chaining LLMs with memory, tools, and more.

- 🤖 **[Ollama (Mistral)](https://ollama.com/)**  
  Lightweight local LLM backend serving the Mistral model.

- 🐘 **[PostgreSQL](https://www.postgresql.org/)** + 🧾 **[SQLAlchemy](https://www.sqlalchemy.org/)**  
  Robust relational database and Python ORM for storing sessions and messages.

- 🔄 **[Redis](https://redis.io/)** *(via Docker)*  
  Fast in-memory cache for recent chat history and temporary context.

- 🎨 **[Rich](https://github.com/Textualize/rich)**  
  Terminal formatting library used for stylish CLI rendering.

- 🚀 **[FastAPI](https://fastapi.tiangolo.com/)** *(Planned)*  
  A high-performance async framework for the upcoming API interface.

## ⚙️ Setup Instructions

Follow the steps below to get Agent **Vyāsa** up and running locally.

---

### 📁 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vyasa.git
cd vyasa

🐍 2. Create Virtual Environment & Install Dependencies
Make sure you're using Python 3.10+.
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

🧠 3. Start Ollama with Mistral
Install Ollama if not already installed.

🐘 4. Setup PostgreSQL Database
Ensure PostgreSQL is running locally. Then:
createdb vyasa_db
DATABASE_URL=postgresql://username:password@localhost:5432/vyasa_db
docker run -d --name vyasa-redis -p 6379:6379 redis

🎨 6. Run the CLI Agent
Once everything is ready, start Vyāsa’s CLI interface:
python main.py


*Developed by: Swastik Das*
_With inspiration from Vedantic wisdom and the need for meaningful memory in AI._
