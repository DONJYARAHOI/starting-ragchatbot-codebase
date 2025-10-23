# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack RAG (Retrieval-Augmented Generation) system for querying course materials. The system uses ChromaDB for vector storage, Anthropic's Claude API with tool-calling for intelligent search, and provides a web interface for user interaction.

## Commands

### Running the Application

**Quick start (recommended):**
```bash
./run.sh
```

**Manual start:**
```bash
cd backend && uv run uvicorn app:app --reload --port 8000
```

**Alternative (bind to all interfaces):**
```bash
cd backend && uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Windows users:** Use Git Bash to run commands.

The application serves at:
- Web Interface: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Dependency Management

Install dependencies:
```bash
uv sync
```

The project uses `uv` as the package manager. Dependencies are specified in `pyproject.toml`.

### Environment Setup

Create a `.env` file with:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture

### Core RAG Pipeline (backend/rag_system.py)

The `RAGSystem` class is the main orchestrator connecting all components:

1. **Document Processing**: `DocumentProcessor` parses course documents with a specific format (course metadata + lessons)
2. **Vector Storage**: `VectorStore` manages two ChromaDB collections:
   - `course_catalog`: Course-level metadata for semantic course name matching
   - `course_content`: Chunked lesson content for semantic search
3. **AI Generation**: `AIGenerator` handles Claude API interactions with tool-calling support
4. **Session Management**: `SessionManager` maintains conversation history per session
5. **Tool-based Search**: `ToolManager` and `CourseSearchTool` enable Claude to search via tool calls

### Data Model (backend/models.py)

Three main data structures:
- `Course`: Contains title, instructor, course_link, and list of lessons
- `Lesson`: Contains lesson_number, title, and lesson_link
- `CourseChunk`: Text chunks with course_title, lesson_number, and chunk_index for vector storage

### Vector Search Strategy (backend/vector_store.py)

The `VectorStore.search()` method implements a two-phase search:
1. **Course resolution**: If `course_name` provided, use semantic search on `course_catalog` to find the exact course title
2. **Content search**: Search `course_content` with optional filters for course_title and lesson_number

This allows flexible queries like "search for 'tool calling' in the MCP course" where "MCP" gets resolved to the full course title.

### Document Format (docs/)

Course documents follow this structure:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [lesson url]
[lesson content]

Lesson 1: [lesson title]
...
```

The `DocumentProcessor` parses this format and creates chunks with overlap (configurable via `backend/config.py`).

### Tool-Calling Architecture (backend/search_tools.py, backend/ai_generator.py)

The system uses Anthropic's tool-calling API instead of manual RAG:
- `CourseSearchTool` is registered with the `ToolManager`
- Claude decides when to call `search_course_content` tool
- Tool results are passed back to Claude in a second API call
- The system enforces "one search per query maximum" via system prompt

Sources are tracked in `CourseSearchTool.last_sources` and retrieved after generation.

### Configuration (backend/config.py)

Key settings:
- `ANTHROPIC_MODEL`: "claude-sonnet-4-20250514"
- `EMBEDDING_MODEL`: "all-MiniLM-L6-v2" (sentence-transformers)
- `CHUNK_SIZE`: 800 characters
- `CHUNK_OVERLAP`: 100 characters
- `MAX_RESULTS`: 5 search results
- `MAX_HISTORY`: 2 conversation turns retained

### FastAPI Application (backend/app.py)

Two main endpoints:
- `POST /api/query`: Process queries with RAG system, returns answer + sources
- `GET /api/courses`: Get course analytics (total count, titles)

The app loads documents from `../docs` on startup and serves the frontend from `../frontend`.

## Development Notes

### Adding New Course Documents

Place course documents in `docs/` directory. Supported formats: `.pdf`, `.docx`, `.txt`. The system auto-loads on startup and skips duplicate courses based on course title.

### Extending Tool Capabilities

To add new tools:
1. Create a class that inherits from `Tool` (in `backend/search_tools.py`)
2. Implement `get_tool_definition()` and `execute()` methods
3. Register with `ToolManager` in `backend/rag_system.py`

### ChromaDB Persistence

The vector database persists to `./chroma_db` (configurable in `backend/config.py`). To rebuild from scratch, call `rag_system.add_course_folder(path, clear_existing=True)`.

### Frontend Integration

The frontend is vanilla HTML/CSS/JavaScript in `frontend/` directory. It communicates with the backend via `/api/query` and maintains session IDs for conversation continuity.

### Session Management Flow

The `SessionManager` (backend/session_manager.py) tracks conversations:
- Creates unique session IDs for each conversation
- Maintains last `MAX_HISTORY` message pairs (user + assistant)
- Conversation history is formatted as text and injected into Claude's system prompt
- Sessions persist in memory only (reset on server restart)

### AI Response Generation Flow

1. User query arrives via `/api/query` endpoint
2. `RAGSystem.query()` retrieves session history from `SessionManager`
3. `AIGenerator` constructs prompt with history + available tools
4. Claude may call `search_course_content` tool (via `ToolManager`)
5. If tool called: `CourseSearchTool` performs two-phase vector search
6. Tool results passed back to Claude for final response generation
7. Sources extracted from `CourseSearchTool.last_sources`
8. Response + sources returned to frontend; conversation stored in session
