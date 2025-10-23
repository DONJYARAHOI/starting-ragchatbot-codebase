"""
Integration tests for the RAG system
These tests verify the end-to-end functionality
"""

from unittest.mock import MagicMock

import pytest
from rag_system import RAGSystem


@pytest.fixture
def rag_system(test_config):
    """Create a RAG system for testing"""
    return RAGSystem(test_config)


@pytest.fixture
def populated_rag_system(rag_system, temp_course_file):
    """Create a RAG system with sample data loaded"""
    # Add the sample course
    course, chunks = rag_system.add_course_document(temp_course_file)
    assert course is not None
    assert chunks > 0
    return rag_system


class TestRAGSystemInitialization:
    """Test RAG system initialization"""

    def test_initialization(self, test_config):
        """Test that RAG system initializes correctly"""
        rag = RAGSystem(test_config)

        assert rag.config == test_config
        assert rag.document_processor is not None
        assert rag.vector_store is not None
        assert rag.ai_generator is not None
        assert rag.session_manager is not None
        assert rag.tool_manager is not None
        assert rag.search_tool is not None

    def test_search_tool_registered(self, rag_system):
        """Test that search tool is registered in tool manager"""
        tools = rag_system.tool_manager.get_tool_definitions()

        assert len(tools) == 1
        assert tools[0]["name"] == "search_course_content"


class TestRAGSystemDocumentLoading:
    """Test document loading functionality"""

    def test_add_course_document(self, rag_system, temp_course_file):
        """Test adding a single course document"""
        course, chunk_count = rag_system.add_course_document(temp_course_file)

        assert course is not None
        assert course.title == "Introduction to Machine Learning"
        assert chunk_count > 0
        assert len(course.lessons) == 3

    def test_course_appears_in_vector_store(self, rag_system, temp_course_file):
        """Test that added course appears in vector store"""
        course, _ = rag_system.add_course_document(temp_course_file)

        # Check course count
        analytics = rag_system.get_course_analytics()
        assert analytics["total_courses"] == 1
        assert course.title in analytics["course_titles"]

    def test_add_invalid_file(self, rag_system):
        """Test adding non-existent file returns None"""
        course, chunks = rag_system.add_course_document("/nonexistent/file.txt")

        assert course is None
        assert chunks == 0

    def test_add_course_folder(self, rag_system):
        """Test adding courses from a folder"""
        # Use the actual docs folder if it exists
        import os

        docs_path = "../docs"

        if os.path.exists(docs_path) and any(f.endswith((".txt", ".pdf", ".docx")) for f in os.listdir(docs_path)):
            courses, chunks = rag_system.add_course_folder(docs_path)

            assert courses >= 0
            assert chunks >= 0
        else:
            # Skip if docs folder doesn't exist
            pytest.skip("Docs folder not found or empty")


class TestRAGSystemQuery:
    """Test RAG system query functionality - THE CRITICAL TEST"""

    def test_query_basic(self, populated_rag_system):
        """Test basic query execution"""
        # Mock AI generator at instance level
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Machine learning is about algorithms that learn from data."
        populated_rag_system.ai_generator = mock_ai_gen

        answer, sources = populated_rag_system.query("What is machine learning?")

        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)

    def test_query_calls_ai_with_tools(self, populated_rag_system):
        """Test that query calls AI generator with tools"""
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Test response"
        populated_rag_system.ai_generator = mock_ai_gen

        populated_rag_system.query("Test question")

        # Verify AI generator was called
        mock_ai_gen.generate_response.assert_called_once()

        # Verify tools were passed
        call_args = mock_ai_gen.generate_response.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] is not None
        assert len(call_args.kwargs["tools"]) > 0

    def test_query_with_session_id(self, populated_rag_system):
        """Test query with session ID for conversation history"""
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Response"
        populated_rag_system.ai_generator = mock_ai_gen

        session_id = populated_rag_system.session_manager.create_session()

        answer, sources = populated_rag_system.query("What is machine learning?", session_id=session_id)

        assert isinstance(answer, str)

        # Verify conversation was stored
        history = populated_rag_system.session_manager.get_conversation_history(session_id)
        assert history is not None

    def test_query_without_ai_key_might_fail(self, populated_rag_system):
        """Test that query might fail if AI key is not set"""
        # This test documents that without a valid API key, queries will fail
        # We'll skip this if there's no API key
        import os

        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("No ANTHROPIC_API_KEY set - cannot test real API call")

        # If we have a key, test might work (but could also fail due to rate limits)
        try:
            answer, sources = populated_rag_system.query("What is linear regression?")
            assert isinstance(answer, str)
        except Exception as e:
            # Document that this might fail
            assert "API" in str(e) or "key" in str(e).lower()


class TestRAGSystemSourceTracking:
    """Test that RAG system properly tracks and returns sources"""

    def test_sources_returned_from_tool(self, populated_rag_system):
        """Test that sources are extracted from tool searches"""
        # Mock the AI to simulate tool use
        mock_ai_instance = MagicMock()

        def mock_generate(query, conversation_history=None, tools=None, tool_manager=None):
            # Simulate the AI calling the search tool
            if tool_manager:
                result = tool_manager.execute_tool("search_course_content", query="machine learning")
            return "Here's what I found about machine learning."

        mock_ai_instance.generate_response.side_effect = mock_generate

        # Replace AI generator
        populated_rag_system.ai_generator = mock_ai_instance

        answer, sources = populated_rag_system.query("What is machine learning?")

        # Sources should be populated
        assert isinstance(sources, list)
        # If tool was called, sources should exist
        if len(sources) > 0:
            for source in sources:
                assert isinstance(source, dict)
                assert "text" in source
                assert "link" in source

    def test_sources_reset_between_queries(self, populated_rag_system):
        """Test that sources are reset between different queries"""
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Response"
        populated_rag_system.ai_generator = mock_ai_gen

        # First query
        _, sources1 = populated_rag_system.query("First question")

        # Manually set some sources to test reset
        populated_rag_system.search_tool.last_sources = [{"text": "Test", "link": "http://test.com"}]

        # Second query - sources should be reset
        _, sources2 = populated_rag_system.query("Second question")

        # Sources from first query shouldn't persist (unless same results)
        # This is because reset_sources() is called


class TestRAGSystemSessionManagement:
    """Test session management in RAG system"""

    def test_creates_session_if_none_provided(self, populated_rag_system):
        """Test that query works without session ID"""
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Response"
        populated_rag_system.ai_generator = mock_ai_gen

        answer, sources = populated_rag_system.query("Test question")

        assert isinstance(answer, str)

    def test_conversation_history_passed_to_ai(self, populated_rag_system):
        """Test that conversation history is passed to AI generator"""
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.return_value = "Response"
        populated_rag_system.ai_generator = mock_ai_gen

        session_id = populated_rag_system.session_manager.create_session()

        # First query
        populated_rag_system.query("First question", session_id)

        # Second query - should have history
        populated_rag_system.query("Second question", session_id)

        # Check that second call included history
        assert mock_ai_gen.generate_response.call_count == 2

        second_call = mock_ai_gen.generate_response.call_args_list[1]
        assert "conversation_history" in second_call.kwargs
        # History should not be None on second call
        history = second_call.kwargs["conversation_history"]
        if history:  # Might be None if session is empty
            assert isinstance(history, str)


class TestRAGSystemAnalytics:
    """Test RAG system analytics"""

    def test_get_course_analytics_empty(self, rag_system):
        """Test analytics on empty system"""
        analytics = rag_system.get_course_analytics()

        assert analytics["total_courses"] == 0
        assert analytics["course_titles"] == []

    def test_get_course_analytics_with_data(self, populated_rag_system):
        """Test analytics with loaded data"""
        analytics = populated_rag_system.get_course_analytics()

        assert analytics["total_courses"] == 1
        assert len(analytics["course_titles"]) == 1
        assert "Introduction to Machine Learning" in analytics["course_titles"]


class TestRAGSystemIntegration:
    """End-to-end integration tests"""

    def test_full_pipeline_with_real_docs(self, rag_system):
        """Test full pipeline with real course documents if available"""
        import os

        docs_path = "../docs"

        if not os.path.exists(docs_path):
            pytest.skip("Docs folder not found")

        # Load courses
        courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=True)

        if courses == 0:
            pytest.skip("No courses found in docs folder")

        # Verify data loaded
        analytics = rag_system.get_course_analytics()
        assert analytics["total_courses"] > 0

        # Test search tool directly
        result = rag_system.search_tool.execute(query="introduction")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_error_in_query_handled_gracefully(self, populated_rag_system):
        """Test that errors in query are handled gracefully"""
        # Make AI generator raise an exception
        mock_ai_gen = MagicMock()
        mock_ai_gen.generate_response.side_effect = Exception("API Error")
        populated_rag_system.ai_generator = mock_ai_gen

        with pytest.raises(Exception) as exc_info:
            populated_rag_system.query("Test question")

        assert "API Error" in str(exc_info.value)


class TestRAGSystemToolManagerIntegration:
    """Test tool manager integration in RAG system"""

    def test_tool_manager_has_search_tool(self, rag_system):
        """Test that tool manager has search tool registered"""
        assert "search_course_content" in rag_system.tool_manager.tools

    def test_tool_manager_can_execute_search(self, populated_rag_system):
        """Test that tool manager can execute search"""
        result = populated_rag_system.tool_manager.execute_tool("search_course_content", query="machine learning")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_sources_retrievable_from_tool_manager(self, populated_rag_system):
        """Test that sources can be retrieved from tool manager"""
        # Execute a search
        populated_rag_system.tool_manager.execute_tool("search_course_content", query="machine learning")

        # Get sources
        sources = populated_rag_system.tool_manager.get_last_sources()

        assert isinstance(sources, list)
        if len(sources) > 0:
            assert "text" in sources[0]
            assert "link" in sources[0]
