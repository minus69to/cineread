# CineRead

A cross-media AI recommendation agent that suggests movies, TV series, and books in a single conversational interface. Ask in English or Bengali — the agent understands both.

![Stack](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![Stack](https://img.shields.io/badge/LangGraph-0.2.28-FF6B35?style=flat-square)
![Stack](https://img.shields.io/badge/SvelteKit-2.x-FF3E00?style=flat-square&logo=svelte)
![Stack](https://img.shields.io/badge/ChromaDB-1.0.0-6C3483?style=flat-square)
![Stack](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)

---

## What it does

- Understands natural language requests in **English and Bengali**
- Recommends across all three media types in one response — *"movies like Oldboy, and books with a similar vibe"*
- Finds **thematic connections** between a book, its film adaptation, and similar series
- Streams responses in real time via **Server-Sent Events**
- Remembers conversation history per session and builds a **taste profile** from your saved/rated items
- All four searches (movies, series, books, RAG) run **in parallel** so responses stay fast

---

## Architecture

```
User message
     │
     ▼
┌─────────────────────────────────────────────────────┐
│                  LangGraph Pipeline                  │
│                                                     │
│  intent_node → router_node → ┌──────────────────┐  │
│                               │  parallel_search  │  │
│                               │  ┌─────────────┐ │  │
│                               │  │ movie_search│ │  │
│                               │  │series_search│ │  │
│                               │  │ book_search │ │  │
│                               │  │  rag_search │ │  │
│                               │  └─────────────┘ │  │
│                               └──────────────────┘  │
│                    → cross_media_node               │
│                    → ranking_node                   │
│                    → response_node                  │
└─────────────────────────────────────────────────────┘
     │
     ▼ SSE stream
SvelteKit frontend
```

### Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| Agent pipeline | LangGraph 0.2.28 |
| LLM | OpenRouter (configurable — any model) |
| Vector store | ChromaDB 1.0.0 |
| Embeddings | `all-MiniLM-L6-v2` (384-dim) |
| Movie/series data | TMDB API |
| Book data | Open Library |
| Database | PostgreSQL 15 (async via asyncpg) |
| Auth | JWT (python-jose + passlib bcrypt) |
| Frontend | SvelteKit 2 + TailwindCSS 3 |
| Streaming | Server-Sent Events |

---

## RAG design

Each media item is stored in ChromaDB as an **LLM-enriched document** — not just title and description, but themes, mood, style, keywords, similar titles, and target audience. This is what makes semantic queries like *"dark psychological thriller with a slow burn"* actually work.

```
Title: Oldboy (2003)
Director: Park Chan-wook
Genres: Mystery, Thriller, Drama
Themes: revenge, identity crisis, captivity, moral ambiguity, trauma
Mood: dark, tense, disturbing, visceral
Style: neo-noir, slow burn, psychological horror
Keywords: twist ending, Korean cinema, unreliable narrator
Similar to: I Saw the Devil, Memories of Murder, The Chaser
```

Collections: `movies` (500 docs), `series` (300 docs), `books` (139 docs)

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- [TMDB API key](https://www.themoviedb.org/settings/api) (free)
- [OpenRouter API key](https://openrouter.ai/) (free tier available)

---

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/minus69to/cineread.git
cd cineread
```

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

```env
TMDB_API_KEY=your_tmdb_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
LLM_PROVIDER=openrouter
LLM_MODEL=google/gemini-2.0-flash-exp:free   # any OpenRouter model works
DATABASE_URL=postgresql+asyncpg://cineread:cineread@localhost:5433/cineread
CHROMA_HOST=localhost
CHROMA_PORT=8001
JWT_SECRET=change_this_to_something_random
JWT_ALGORITHM=HS256
```

### 2. Start infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL on port `5433` and ChromaDB on port `8001`.

### 3. Install backend dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Ingest data into ChromaDB

This runs once. Each script fetches data, enriches it with an LLM call, and stores embeddings. Takes ~10–15 minutes total.

```bash
# From backend/
python -m app.scripts.ingest_movies   # 500 top-rated movies from TMDB
python -m app.scripts.ingest_series   # 300 top-rated series from TMDB
python -m app.scripts.ingest_books    # 139 curated books
```

### 5. Start the backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Usage examples

```
"I loved Oldboy. What should I watch next?"
"Dark dekhlam, ki dekhbo?"
"Dune er moto kono book ache?"
"Show me something psychological with a slow burn — movie or series, doesn't matter"
"I want a book like Man's Search for Meaning"
"Korean thriller with a mind-bending plot"
```

The agent detects intent, runs all searches in parallel, finds cross-media connections, ranks results, and streams the response.

---

## Project structure

```
cineread/
├── docker-compose.yml
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   └── app/
│       ├── agents/
│       │   ├── graph.py              # LangGraph pipeline definition
│       │   ├── state.py              # AgentState TypedDict
│       │   ├── intent_agent.py       # Extracts mood, vibe, query from message
│       │   ├── media_router_agent.py # Decides search strategy
│       │   ├── movie_search_agent.py # TMDB movie recommendations
│       │   ├── series_search_agent.py# TMDB series recommendations
│       │   ├── book_search_agent.py  # Open Library search
│       │   ├── rag_agent.py          # ChromaDB semantic search
│       │   ├── cross_media_agent.py  # Finds book↔movie↔series connections
│       │   ├── ranking_agent.py      # Scores and deduplicates candidates
│       │   ├── response_agent.py     # Generates conversational response
│       │   └── llm.py                # LLM factory (OpenRouter / Gemini)
│       ├── routers/
│       │   ├── chat.py               # SSE streaming chat endpoint
│       │   ├── auth.py               # JWT register / login / me
│       │   ├── media.py              # Media search and detail endpoints
│       │   └── list.py               # Save / rate / delete saved items
│       ├── services/
│       │   ├── tmdb_service.py       # TMDB API client
│       │   ├── book_service.py       # Open Library API client
│       │   ├── rag_service.py        # ChromaDB query wrapper
│       │   └── memory_service.py     # Conversation history + taste profile
│       ├── models/                   # SQLAlchemy ORM models
│       ├── schemas/                  # Pydantic request/response schemas
│       └── scripts/
│           ├── ingest_movies.py      # One-time movie ingest with LLM enrichment
│           ├── ingest_series.py      # One-time series ingest with LLM enrichment
│           └── ingest_books.py       # One-time book ingest with LLM enrichment
└── frontend/
    └── src/
        ├── lib/
        │   ├── api.js                # SSE stream consumer
        │   └── components/
        │       ├── MediaCard.svelte  # Movie/series/book result card
        │       ├── MessageBubble.svelte
        │       ├── ChatInput.svelte
        │       ├── MediaBadge.svelte
        │       └── TypingIndicator.svelte
        └── routes/
            ├── +page.svelte          # Landing page
            └── chat/+page.svelte     # Main chat interface
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Stream recommendations via SSE |
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/auth/me` | Current user |
| `GET` | `/media/search?q=&type=` | Search movies/series/books |
| `GET` | `/media/{id}` | Media detail |
| `POST` | `/list/save` | Save a media item |
| `GET` | `/list/` | Get saved items |
| `PATCH` | `/list/{id}/rate` | Rate a saved item |
| `DELETE` | `/list/{id}` | Remove saved item |
| `GET` | `/health` | Health check |

### Chat SSE protocol

```javascript
// Send
POST /chat
{ "message": "...", "session_id": "uuid" }

// Receive (event stream)
data: {"type": "media", "items": [...]}   // recommendation cards
data: {"type": "text",  "content": "..."}  // conversational response
data: {"type": "error", "content": "..."}  // on failure
data: [DONE]
```

---

## Switching LLM provider

Edit `backend/.env`:

```env
# Use any OpenRouter model
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=sk-or-...

# Or use Gemini directly
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
GEMINI_API_KEY=AIza...
```

No code changes needed — `agents/llm.py` reads the provider at startup.

---

## Running tests

```bash
cd backend
pytest
```

---

## Known limitations

- Book coverage is 139 curated titles. Queries about books outside this list may return weak results.
- Open Library API is unreliable from some networks — book live search falls back to empty on timeout.
- ChromaDB vector data is not included in the repo. Run the ingest scripts after setup.

---

## License

MIT
