# Architecture Documentation

This document provides a comprehensive overview of the RAG (Retrieval-Augmented Generation) system architecture, including component interactions, data flows, and key processes.

## System Overview

The RAG system is built as a full-stack application that enables intelligent querying of course materials using semantic search and AI-powered responses. It combines ChromaDB for vector storage, Anthropic's Claude API for natural language processing, and a web interface for user interaction.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web Interface<br/>HTML/CSS/JavaScript]
    end

    subgraph "API Layer"
        API[FastAPI Application<br/>app.py]
    end

    subgraph "RAG System Core"
        RAG[RAGSystem<br/>Orchestrator]
        SESSION[SessionManager<br/>Conversation History]
    end

    subgraph "AI & Tools"
        AI[AIGenerator<br/>Claude API Client]
        TOOL_MGR[ToolManager<br/>Tool Registry]
        SEARCH_TOOL[CourseSearchTool<br/>Search Interface]
    end

    subgraph "Data Processing"
        DOC[DocumentProcessor<br/>Text Chunking]
        VECTOR[VectorStore<br/>ChromaDB Client]
    end

    subgraph "Storage Layer"
        CATALOG[(ChromaDB<br/>course_catalog)]
        CONTENT[(ChromaDB<br/>course_content)]
        DOCS[Course Documents<br/>docs/ folder]
    end

    UI -->|HTTP Requests| API
    API -->|Query & Session| RAG
    RAG -->|Generate Response| AI
    RAG -->|Store/Retrieve History| SESSION
    RAG -->|Register Tools| TOOL_MGR
    AI -->|Execute Tools| TOOL_MGR
    TOOL_MGR -->|Search Content| SEARCH_TOOL
    SEARCH_TOOL -->|Vector Search| VECTOR
    RAG -->|Process Documents| DOC
    DOC -->|Store Chunks| VECTOR
    VECTOR -->|Read/Write| CATALOG
    VECTOR -->|Read/Write| CONTENT
    DOC -.->|Load Files| DOCS

    style RAG fill:#4A90E2,stroke:#2E5C8A,stroke-width:3px,color:#fff
    style VECTOR fill:#50C878,stroke:#2E7D4E,stroke-width:2px,color:#fff
    style AI fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#fff
```

## Core Components

### 1. RAGSystem (rag_system.py)
The central orchestrator that coordinates all system components:
- Initializes and manages all core components
- Handles document ingestion and processing
- Coordinates query processing with tool-based search
- Manages conversation sessions
- **Key Methods:**
  - `add_course_document()`: Process and store a single course
  - `add_course_folder()`: Batch process course documents
  - `query()`: Process user queries with RAG pipeline

### 2. VectorStore (vector_store.py)
Manages two ChromaDB collections for semantic search:
- **course_catalog**: Course metadata for semantic course name matching
- **course_content**: Chunked lesson content with embeddings
- **Key Features:**
  - Two-phase search (course resolution + content search)
  - Semantic course name matching
  - Flexible filtering by course and lesson
  - SentenceTransformer embeddings (all-MiniLM-L6-v2)

### 3. AIGenerator (ai_generator.py)
Handles Claude API interactions:
- Manages API client and parameters
- Supports tool-calling with Anthropic's API
- Handles multi-turn conversations with history
- Enforces "one search per query maximum" via system prompt

### 4. ToolManager & CourseSearchTool (search_tools.py)
Implements extensible tool system:
- **ToolManager**: Registry for tools available to Claude
- **CourseSearchTool**: Executes semantic search operations
- Tracks sources with links for UI display
- Enables Claude to decide when to search

### 5. DocumentProcessor (document_processor.py)
Parses and chunks course documents:
- Supports PDF, DOCX, and TXT formats
- Creates overlapping chunks (800 chars, 100 overlap)
- Extracts course metadata and lesson structure

### 6. SessionManager (session_manager.py)
Manages conversation state:
- Creates unique session IDs
- Maintains last N message pairs (default: 2)
- Injects history into Claude's system prompt
- In-memory storage (resets on server restart)

## Data Models

```mermaid
classDiagram
    class Course {
        +string title
        +string course_link
        +string instructor
        +List~Lesson~ lessons
    }

    class Lesson {
        +int lesson_number
        +string title
        +string lesson_link
    }

    class CourseChunk {
        +string content
        +string course_title
        +int lesson_number
        +int chunk_index
    }

    Course "1" --> "*" Lesson
    Course ..> CourseChunk : chunked into
```

## Query Processing Flow

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI
    participant RAG as RAGSystem
    participant Session as SessionManager
    participant AI as AIGenerator
    participant ToolMgr as ToolManager
    participant Search as CourseSearchTool
    participant Vector as VectorStore
    participant ChromaDB

    User->>API: POST /api/query<br/>{query, session_id}
    API->>RAG: query(query, session_id)

    RAG->>Session: get_conversation_history(session_id)
    Session-->>RAG: previous exchanges

    RAG->>AI: generate_response(query, history, tools)

    Note over AI: Claude decides to search
    AI->>ToolMgr: execute_tool("search_course_content", params)
    ToolMgr->>Search: execute(query, course_name, lesson_number)

    Search->>Vector: search(query, course_name, lesson_number)

    alt course_name provided
        Vector->>ChromaDB: Query course_catalog<br/>(semantic course matching)
        ChromaDB-->>Vector: matched course title
    end

    Vector->>ChromaDB: Query course_content<br/>(with filters)
    ChromaDB-->>Vector: relevant chunks
    Vector-->>Search: SearchResults

    Search->>Vector: get_lesson_link(course, lesson)
    Vector-->>Search: lesson link

    Search-->>ToolMgr: formatted results
    ToolMgr-->>AI: tool results

    Note over AI: Claude synthesizes response
    AI-->>RAG: final answer

    RAG->>ToolMgr: get_last_sources()
    ToolMgr-->>RAG: sources with links

    RAG->>Session: add_exchange(session_id, query, response)

    RAG-->>API: (answer, sources)
    API-->>User: JSON response
```

## Tool-Calling Architecture

The system uses Anthropic's tool-calling API instead of manual RAG retrieval:

```mermaid
graph LR
    subgraph "Tool Definition Phase"
        A[CourseSearchTool] -->|get_tool_definition| B[Tool Schema]
        B -->|register_tool| C[ToolManager]
    end

    subgraph "Request Phase"
        D[User Query] -->|with tools| E[Claude API]
        C -->|tool definitions| E
    end

    subgraph "Tool Use Phase"
        E -->|decides to search| F[Tool Use Block]
        F -->|tool_name + params| G[ToolManager.execute_tool]
        G -->|execute| H[CourseSearchTool]
        H -->|vector search| I[VectorStore]
    end

    subgraph "Response Phase"
        I -->|results| H
        H -->|formatted text| G
        G -->|tool results| J[Claude API Call 2]
        J -->|synthesized answer| K[Final Response]
    end

    style E fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#fff
    style I fill:#50C878,stroke:#2E7D4E,stroke-width:2px,color:#fff
```

**Key Benefits:**
- Claude decides when to search (no forced retrieval)
- Natural language tool parameters
- Cleaner separation of concerns
- "One search per query maximum" enforced by system prompt

## Vector Search Strategy

The VectorStore implements a two-phase search for flexible queries:

```mermaid
flowchart TD
    Start[Search Request] --> HasCourse{course_name<br/>provided?}

    HasCourse -->|Yes| Phase1[Phase 1: Course Resolution]
    HasCourse -->|No| Phase2[Phase 2: Content Search]

    Phase1 --> CatalogSearch[Semantic Search<br/>in course_catalog]
    CatalogSearch --> MatchFound{Match<br/>found?}

    MatchFound -->|No| ErrorReturn[Return: No course found]
    MatchFound -->|Yes| GetTitle[Get exact course title]
    GetTitle --> Phase2

    Phase2 --> BuildFilter[Build Filter Dict]
    BuildFilter --> HasFilters{Filters<br/>exist?}

    HasFilters -->|Yes| FilteredSearch[Search course_content<br/>with filters]
    HasFilters -->|No| UnfilteredSearch[Search course_content<br/>no filters]

    FilteredSearch --> FormatResults[Format Results<br/>with Metadata]
    UnfilteredSearch --> FormatResults

    FormatResults --> Return[Return SearchResults]

    style Phase1 fill:#E8F4F8,stroke:#4A90E2,stroke-width:2px
    style Phase2 fill:#F0E8F8,stroke:#9B59B6,stroke-width:2px
    style CatalogSearch fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    style FilteredSearch fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#fff
    style UnfilteredSearch fill:#9B59B6,stroke:#6C3483,stroke-width:2px,color:#fff
```

**Example:**
Query: "search for 'tool calling' in the MCP course"
1. **Phase 1**: "MCP" → semantic search in course_catalog → resolves to "Introduction to Model Context Protocol"
2. **Phase 2**: Search for "tool calling" in course_content filtered by course_title = "Introduction to Model Context Protocol"

## Document Processing Pipeline

```mermaid
flowchart LR
    subgraph Input
        Files[Course Documents<br/>.pdf .docx .txt]
    end

    subgraph Processing
        Parse[DocumentProcessor<br/>Parse Structure]
        Extract[Extract Metadata<br/>& Lessons]
        Chunk[Create Chunks<br/>800 chars, 100 overlap]
    end

    subgraph Storage
        Meta[course_catalog<br/>Course + Instructor]
        Content[course_content<br/>Chunked Text]
    end

    subgraph Embeddings
        Embed[SentenceTransformer<br/>all-MiniLM-L6-v2]
    end

    Files --> Parse
    Parse --> Extract
    Extract --> Chunk

    Extract -->|Course| Meta
    Chunk -->|CourseChunk| Content

    Meta --> Embed
    Content --> Embed

    style Parse fill:#4A90E2,stroke:#2E5C8A,stroke-width:2px,color:#fff
    style Embed fill:#50C878,stroke:#2E7D4E,stroke-width:2px,color:#fff
```

**Document Format:**
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

## API Endpoints

### POST /api/query
Process user queries with RAG system.

**Request:**
```json
{
  "query": "What is tool calling?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "Tool calling is...",
  "sources": [
    {
      "text": "Introduction to MCP - Lesson 3",
      "link": "https://example.com/lesson3"
    }
  ],
  "session_id": "session-12345"
}
```

### GET /api/courses
Get course catalog analytics.

**Response:**
```json
{
  "total_courses": 5,
  "course_titles": ["Course 1", "Course 2", ...]
}
```

## Configuration

Key settings in `backend/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| ANTHROPIC_MODEL | claude-sonnet-4-20250514 | Claude model version |
| EMBEDDING_MODEL | all-MiniLM-L6-v2 | SentenceTransformer model |
| CHUNK_SIZE | 800 | Characters per chunk |
| CHUNK_OVERLAP | 100 | Overlap between chunks |
| MAX_RESULTS | 5 | Max search results |
| MAX_HISTORY | 2 | Conversation turns retained |
| CHROMA_PATH | ./chroma_db | ChromaDB persistence path |

## Extensibility

### Adding New Tools

To extend the system with new capabilities:

1. Create a class inheriting from `Tool` (in `backend/search_tools.py`)
2. Implement required methods:
   ```python
   class MyTool(Tool):
       def get_tool_definition(self) -> dict:
           return {
               "name": "my_tool",
               "description": "What this tool does",
               "input_schema": {...}
           }

       def execute(self, **kwargs) -> str:
           # Tool logic here
           return "result"
   ```
3. Register with ToolManager in `backend/rag_system.py`:
   ```python
   my_tool = MyTool()
   self.tool_manager.register_tool(my_tool)
   ```

### Supporting New Document Formats

Extend `DocumentProcessor` to parse additional file types beyond PDF, DOCX, and TXT.

## Session Management

Sessions maintain conversation continuity:

```mermaid
stateDiagram-v2
    [*] --> NoSession: User opens app
    NoSession --> NewSession: First query without session_id
    NewSession --> ActiveSession: Create session ID
    ActiveSession --> ActiveSession: Subsequent queries<br/>(store exchanges)
    ActiveSession --> [*]: Server restart<br/>(sessions cleared)

    note right of ActiveSession
        Stores last MAX_HISTORY
        message pairs (user + assistant)
        Injected into system prompt
    end note
```

**Note:** Sessions are stored in-memory and reset on server restart. For production, consider persistent session storage.

## Deployment Considerations

1. **ChromaDB Persistence**: Stored in `./chroma_db` - ensure this directory is backed up
2. **API Keys**: Store `ANTHROPIC_API_KEY` securely in `.env` file
3. **Document Loading**: Documents loaded from `../docs` on startup
4. **Performance**: Embedding model runs locally (all-MiniLM-L6-v2 is lightweight)
5. **Scaling**: Consider Redis for session management in production

## References

- CLAUDE.md: Detailed development instructions
- backend/config.py: Configuration settings
- backend/rag_system.py: Main orchestrator implementation
