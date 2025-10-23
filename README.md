# Course Materials RAG System

A Retrieval-Augmented Generation (RAG) system designed to answer questions about course materials using semantic search and AI-powered responses.

## Overview

This application is a full-stack web application that enables users to query course materials and receive intelligent, context-aware responses. It uses ChromaDB for vector storage, Anthropic's Claude for AI generation, and provides a web interface for interaction.

## Architecture

For a comprehensive understanding of the system architecture, component interactions, and data flows, see [Architecture Documentation](docs/architecture.md).

**Quick Architecture Overview:**
- **RAGSystem**: Central orchestrator coordinating all components
- **VectorStore**: ChromaDB-based semantic search with two collections (course catalog + content)
- **AIGenerator**: Claude API client with tool-calling support
- **ToolManager**: Extensible tool system enabling Claude to search when needed
- **SessionManager**: Conversation history management

The architecture documentation includes detailed diagrams for:
- System component interactions
- Query processing flow with tool-calling
- Vector search strategy
- Document processing pipeline

## Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- An Anthropic API key (for Claude AI)
- **For Windows**: Use Git Bash to run the application commands - [Download Git for Windows](https://git-scm.com/downloads/win)

## Installation

1. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install Python dependencies**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## Running the Application

### Quick Start

Use the provided shell script:
```bash
chmod +x run.sh
./run.sh
```

### Manual Start

```bash
cd backend
uv run uvicorn app:app --reload --port 8000
```

The application will be available at:
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Development

For information on code quality tools, linting, formatting, and development best practices, see [DEVELOPMENT.md](DEVELOPMENT.md).

