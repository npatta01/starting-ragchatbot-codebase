"""
Shared pytest fixtures for RAG system tests.

This module provides common test fixtures for mocking dependencies,
creating test data, and setting up test clients.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List
from fastapi.testclient import TestClient
import sys
import os

# Ensure backend directory is in path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from models import Course, Lesson, CourseChunk
from config import Config


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """
    Create a test configuration with safe defaults.
    Uses in-memory databases and test API keys.
    """
    return Config(
        ANTHROPIC_API_KEY="test-api-key-12345",
        ANTHROPIC_MODEL="claude-sonnet-4-20250514",
        EMBEDDING_MODEL="all-MiniLM-L6-v2",
        CHUNK_SIZE=800,
        CHUNK_OVERLAP=100,
        MAX_RESULTS=5,
        MAX_HISTORY=2,
        MAX_TOOL_ROUNDS=2,
        CHROMA_PATH=":memory:"  # Use in-memory for tests
    )


# ============================================================================
# Mock Component Fixtures
# ============================================================================

@pytest.fixture
def mock_vector_store():
    """
    Mock VectorStore for testing without database dependencies.
    """
    mock_store = Mock()
    mock_store.search.return_value = [
        {
            "content": "Python is a high-level programming language.",
            "course_title": "Introduction to Python",
            "lesson_number": 1,
            "chunk_index": 0
        }
    ]
    mock_store.get_course_count.return_value = 2
    mock_store.get_existing_course_titles.return_value = [
        "Introduction to Python",
        "Advanced Python"
    ]
    mock_store.add_course_metadata.return_value = None
    mock_store.add_course_content.return_value = None
    mock_store.clear_all_data.return_value = None

    return mock_store


@pytest.fixture
def mock_ai_generator():
    """
    Mock AIGenerator for testing without API calls.
    """
    mock_gen = Mock()
    mock_gen.generate_response.return_value = "This is a test response from the AI."
    return mock_gen


@pytest.fixture
def mock_session_manager():
    """
    Mock SessionManager for testing session handling.
    """
    mock_manager = Mock()
    mock_manager.create_session.return_value = "test-session-123"
    mock_manager.get_conversation_history.return_value = "User: Hello\nAssistant: Hi!"
    mock_manager.add_exchange.return_value = None
    return mock_manager


@pytest.fixture
def mock_tool_manager():
    """
    Mock ToolManager for testing tool execution.
    """
    mock_manager = Mock()
    mock_manager.get_tool_definitions.return_value = [
        {
            "name": "search_course_content",
            "description": "Search course content",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                }
            }
        }
    ]
    mock_manager.execute_tool.return_value = "Search results: Python is a language."
    mock_manager.get_last_sources.return_value = [
        "[Introduction to Python - Lesson 1]"
    ]
    mock_manager.reset_sources.return_value = None
    return mock_manager


@pytest.fixture
def mock_document_processor():
    """
    Mock DocumentProcessor for testing document processing.
    """
    mock_processor = Mock()

    # Create sample course data
    sample_course = Course(
        title="Test Course",
        course_link="http://example.com/course",
        instructor="Test Instructor",
        lessons=[
            Lesson(lesson_number=1, title="Test Lesson", lesson_link="http://example.com/lesson1")
        ]
    )

    sample_chunks = [
        CourseChunk(
            content="Test content chunk 1",
            course_title="Test Course",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Test content chunk 2",
            course_title="Test Course",
            lesson_number=1,
            chunk_index=1
        )
    ]

    mock_processor.process_course_document.return_value = (sample_course, sample_chunks)
    return mock_processor


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_course():
    """
    Create a sample Course object for testing.
    """
    return Course(
        title="Introduction to Python",
        course_link="http://example.com/python-course",
        instructor="Jane Doe",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Getting Started",
                lesson_link="http://example.com/lesson0"
            ),
            Lesson(
                lesson_number=1,
                title="Python Basics",
                lesson_link="http://example.com/lesson1"
            ),
            Lesson(
                lesson_number=2,
                title="Data Structures",
                lesson_link="http://example.com/lesson2"
            )
        ]
    )


@pytest.fixture
def sample_course_chunks():
    """
    Create sample CourseChunk objects for testing.
    """
    return [
        CourseChunk(
            content="Python is a high-level, interpreted programming language.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Python supports multiple programming paradigms including procedural, object-oriented, and functional programming.",
            course_title="Introduction to Python",
            lesson_number=1,
            chunk_index=1
        ),
        CourseChunk(
            content="Lists are ordered, mutable collections in Python.",
            course_title="Introduction to Python",
            lesson_number=2,
            chunk_index=0
        )
    ]


@pytest.fixture
def sample_query_request():
    """
    Sample query request payload for API testing.
    """
    return {
        "query": "What is Python?",
        "session_id": "test-session-123"
    }


@pytest.fixture
def sample_query_response():
    """
    Sample query response for API testing.
    """
    return {
        "answer": "Python is a high-level programming language.",
        "sources": ["[Introduction to Python - Lesson 1]"],
        "session_id": "test-session-123"
    }


# ============================================================================
# API Test Client Fixtures
# ============================================================================

@pytest.fixture
def test_app():
    """
    Create a test FastAPI app without static file mounting.

    This fixture creates an app instance that includes only the API endpoints,
    avoiding the static file mounting issue that occurs in the main app.
    """
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional

    # Create test app
    app = FastAPI(title="Course Materials RAG System - Test")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Pydantic models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    # Mock RAG system for testing
    mock_rag = Mock()
    mock_rag.session_manager.create_session.return_value = "test-session-123"
    mock_rag.query.return_value = (
        "Python is a programming language.",
        ["[Introduction to Python - Lesson 1]"]
    )
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Introduction to Python", "Advanced Python"]
    }

    # Store mock for access in tests
    app.state.rag_system = mock_rag

    # API endpoints
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = app.state.rag_system.session_manager.create_session()

            answer, sources = app.state.rag_system.query(request.query, session_id)

            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = app.state.rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


@pytest.fixture
def test_client(test_app):
    """
    Create a TestClient for the test app.

    This client can be used to make HTTP requests to the test app
    without running an actual server.
    """
    from fastapi.testclient import TestClient
    return TestClient(test_app)


# ============================================================================
# Anthropic API Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_anthropic_client():
    """
    Mock Anthropic client for testing AI generator without API calls.
    """
    mock_client = MagicMock()

    # Default response - text only (no tools)
    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [MagicMock(text="Test response from Claude")]

    mock_client.messages.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_anthropic_with_tool_use():
    """
    Mock Anthropic client that simulates tool use (two-stage pattern).
    """
    mock_client = MagicMock()

    # First response - tool use
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.name = "search_course_content"
    mock_tool_block.id = "tool_123"
    mock_tool_block.input = {"query": "test query"}

    mock_first_response = MagicMock()
    mock_first_response.stop_reason = "tool_use"
    mock_first_response.content = [mock_tool_block]

    # Second response - final answer
    mock_second_response = MagicMock()
    mock_second_response.stop_reason = "end_turn"
    mock_second_response.content = [MagicMock(text="Final answer based on search results")]

    mock_client.messages.create.side_effect = [mock_first_response, mock_second_response]

    return mock_client
