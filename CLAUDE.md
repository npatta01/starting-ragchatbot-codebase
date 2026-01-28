# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A RAG (Retrieval-Augmented Generation) chatbot system for querying course materials. Uses ChromaDB for vector storage, Anthropic's Claude API for generation, and implements tool-based search with a two-stage API calling pattern.

## Development Commands

**IMPORTANT**: This project uses `uv` for package management. Always use `uv` commands - do NOT use `pip` or `pip install`.

### Running the Application

```bash
# Quick start (from root)
./run.sh

# Manual start (from root)
cd backend && uv run uvicorn app:app --reload --port 8000

# Access points
# - Web UI: http://localhost:8000
# - API docs: http://localhost:8000/docs
```

### Dependencies

```bash
# Install/sync dependencies
uv sync

# Add new dependency
uv add <package-name>
```

### Environment Setup

Required `.env` file in root:
```
ANTHROPIC_API_KEY=your_key_here
```

### Data Management

```bash
# Clear vector store (from backend/)
rm -rf chroma_db/

# Documents are auto-loaded from ../docs/ on startup
# To add courses: place .txt files in docs/ and restart
```

## Architecture

### RAG Query Flow (Two-Stage Pattern)

The system uses a **two-stage Claude API calling pattern** with tool execution:

1. **First API Call**: Claude receives the user query + available tools → decides to use `search_course_content` tool
2. **Tool Execution**: Search tool performs vector search in ChromaDB → returns formatted results
3. **Second API Call**: Claude receives search results → synthesizes final answer

Key files: `rag_system.py` orchestrates, `ai_generator.py` handles both API calls, `search_tools.py` executes search.

### Component Responsibilities

**RAGSystem (`rag_system.py`)**: Main orchestrator
- Coordinates all components (document processor, vector store, AI generator, session manager)
- Entry point: `query()` method handles user queries
- Entry point: `add_course_folder()` loads documents on startup

**AIGenerator (`ai_generator.py`)**: Claude API wrapper
- `generate_response()`: First API call with tools
- `_handle_tool_execution()`: Executes tools and makes second API call
- System prompt optimized for brief, educational responses

**SearchTools (`search_tools.py`)**: Tool implementations
- `CourseSearchTool`: Executes vector search, formats results with course/lesson context
- `ToolManager`: Registers tools, provides definitions to Claude, tracks sources
- Sources tracking: `last_sources` attribute stores references for UI display

**VectorStore (`vector_store.py`)**: ChromaDB interface
- Two collections: `course_catalog` (metadata) and `course_content` (chunks)
- `search()`: Main interface with semantic course name resolution
- `_resolve_course_name()`: Uses vector search to match partial course names

**DocumentProcessor (`document_processor.py`)**: File parsing
- `process_course_document()`: Parses structured course files
- `chunk_text()`: Sentence-based chunking with overlap (800 chars, 100 overlap)
- Context enrichment: Prepends course/lesson info to chunks

**SessionManager (`session_manager.py`)**: Conversation history
- In-memory storage (lost on restart)
- Limits to `MAX_HISTORY * 2` messages per session

### Data Models (`models.py`)

- **Course**: title (unique ID), course_link, instructor, lessons[]
- **Lesson**: lesson_number, title, lesson_link
- **CourseChunk**: content, course_title, lesson_number, chunk_index

### Configuration (`config.py`)

Key settings (dataclass):
- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2" (384-dim vectors)
- `CHUNK_SIZE`: 800 characters
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation turns

## Document Format

Course files in `docs/` must follow this structure:

```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [url]
[lesson content...]

Lesson 1: [lesson title]
Lesson Link: [url]
[lesson content...]
```

- First 3 lines: Course metadata
- Lesson markers: `Lesson N: [title]` (case-insensitive regex match)
- Optional lesson links immediately after lesson marker
- Content: Everything between lesson markers

## Processing Pipeline

**On Startup** (`app.py:startup_event`):
1. Load all `.txt` files from `docs/`
2. For each file: Parse → Chunk → Embed → Store in ChromaDB
3. Skip files with matching course titles (duplicate prevention)

**Document Processing**:
1. Extract course metadata (title, link, instructor)
2. Split into lessons by `Lesson N:` markers
3. Chunk lesson content (sentence-based, 800 chars with 100 overlap)
4. Add context: `"Course {title} Lesson {N} content: {chunk}"`
5. Generate embeddings with SentenceTransformer
6. Store in two collections:
   - `course_catalog`: Course metadata for semantic search
   - `course_content`: Chunks with metadata (course_title, lesson_number, chunk_index)

**Query Processing**:
1. Get conversation history from session
2. Claude API call #1 with search tool definition
3. Claude decides to search → returns tool_use
4. Execute search: Query → Embed → ChromaDB cosine similarity → Top 5 chunks
5. Format results with `[Course - Lesson N]` headers
6. Track sources in tool's `last_sources` attribute
7. Claude API call #2 with search results → synthesize answer
8. Return (answer, sources) tuple
9. Update session history

## Key Design Patterns

**Tool-Based Search**: Claude uses tools rather than receiving all context upfront. Enables:
- Dynamic search decisions
- Source attribution
- Filtering by course/lesson

**Semantic Course Resolution**: Course names use fuzzy matching via vector search in `course_catalog` collection.

**Chunk Context Enrichment**: Every chunk includes course title and lesson number in content for better semantic search.

**Session Management**: Stateless API with session IDs. History maintained server-side, limited to prevent context overflow.

**Source Tracking**: Search tool stores sources in `last_sources`, retrieved after AI generation, then reset for next query.

## API Endpoints (`app.py`)

**POST /api/query**
- Request: `{query: str, session_id?: str}`
- Response: `{answer: str, sources: str[], session_id: str}`
- Creates session if not provided

**GET /api/courses**
- Response: `{total_courses: int, course_titles: str[]}`
- Returns vector store statistics

**GET /**
- Serves frontend static files (HTML/CSS/JS)

## Frontend (`frontend/`)

**script.js**:
- `sendMessage()`: POST to /api/query, handles loading state
- `addMessage()`: Renders markdown responses with marked.js
- `currentSessionId`: Global session tracking
- Sources displayed in collapsible `<details>` element

**index.html**: Chat interface with sidebar (course stats, suggested questions)

**style.css**: Dark theme with monospace font

## Important Constraints

**ChromaDB Collections**: Always two collections (`course_catalog`, `course_content`). Don't add more without understanding the search resolution flow.

**Tool Execution Limit**: AI generator system prompt enforces "one search per query maximum". Multiple searches increase latency significantly.

**Course Title as ID**: Course title is the unique identifier across all components. Changing a title requires re-processing.

**Sentence Chunking**: `chunk_text()` never splits mid-sentence. Uses regex that handles abbreviations.

**No Streaming**: API calls don't use streaming. Claude generates complete responses.

## Modifying Behavior

**Change AI responses**: Edit system prompt in `ai_generator.py:SYSTEM_PROMPT`

**Adjust chunk size**: Modify `CHUNK_SIZE` and `CHUNK_OVERLAP` in `config.py`

**Change search results**: Modify `MAX_RESULTS` in `config.py`

**Add new tools**:
1. Create tool class inheriting from `Tool` in `search_tools.py`
2. Implement `get_tool_definition()` and `execute()`
3. Register in `rag_system.py:__init__()` via `tool_manager.register_tool()`

**Clear and rebuild index**: Delete `chroma_db/` directory and restart (will re-process all docs)

## Troubleshooting

**No search results**: Course name might not match. Check `vector_store._resolve_course_name()` for fuzzy matching logic.

**Session lost**: Sessions are in-memory. Server restart clears all history.

**Import errors**: Run `uv sync` to ensure dependencies match `uv.lock`

**Port already in use**: Change `--port 8000` in run command or kill existing process
