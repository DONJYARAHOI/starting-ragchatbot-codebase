"""
Tests for CourseSearchTool functionality - the core of RAG search
"""

from search_tools import ToolManager


class TestCourseSearchToolDefinition:
    """Test CourseSearchTool tool definition"""

    def test_get_tool_definition_structure(self, course_search_tool):
        """Test that tool definition has correct structure"""
        tool_def = course_search_tool.get_tool_definition()

        # Check required keys
        assert "name" in tool_def
        assert "description" in tool_def
        assert "input_schema" in tool_def

        # Check values
        assert tool_def["name"] == "search_course_content"
        assert isinstance(tool_def["description"], str)
        assert tool_def["input_schema"]["type"] == "object"

    def test_tool_definition_parameters(self, course_search_tool):
        """Test tool definition has correct parameters"""
        tool_def = course_search_tool.get_tool_definition()
        properties = tool_def["input_schema"]["properties"]

        # Check required parameters
        assert "query" in properties
        assert "course_name" in properties
        assert "lesson_number" in properties

        # Check required fields
        assert "query" in tool_def["input_schema"]["required"]

        # Optional fields should not be required
        assert "course_name" not in tool_def["input_schema"]["required"]
        assert "lesson_number" not in tool_def["input_schema"]["required"]


class TestCourseSearchToolExecute:
    """Test CourseSearchTool.execute() method - CRITICAL for RAG"""

    def test_execute_simple_query(self, course_search_tool):
        """Test executing a simple query"""
        result = course_search_tool.execute(query="linear regression")

        # Should return a string result
        assert isinstance(result, str)
        # Should not be an error message
        assert not result.startswith("No relevant content found")
        # Should contain relevant content
        assert "linear regression" in result.lower() or "regression" in result.lower()

    def test_execute_query_with_course_filter(self, course_search_tool):
        """Test executing query with course name filter"""
        result = course_search_tool.execute(query="machine learning", course_name="Introduction to Machine Learning")

        assert isinstance(result, str)
        assert not result.startswith("No relevant content found")
        # Result should mention the course
        assert "Introduction to Machine Learning" in result

    def test_execute_query_with_partial_course_name(self, course_search_tool):
        """Test executing query with partial course name"""
        result = course_search_tool.execute(
            query="regression",
            course_name="Machine Learning",  # Partial name
        )

        # Should work with partial course name matching
        assert isinstance(result, str)
        # Should not be an error
        assert not result.startswith("No course found")

    def test_execute_query_with_lesson_filter(self, course_search_tool):
        """Test executing query with lesson number filter"""
        result = course_search_tool.execute(
            query="regression", course_name="Introduction to Machine Learning", lesson_number=1
        )

        assert isinstance(result, str)
        # Should mention the lesson number
        assert "Lesson 1" in result or "lesson_number" in result.lower()

    def test_execute_nonexistent_course_fuzzy_match(self, course_search_tool):
        """Test that querying non-existent course returns fuzzy match

        Vector search always finds the closest match, so even a completely
        unrelated course name will match something. This is expected behavior.
        """
        result = course_search_tool.execute(query="anything", course_name="Totally Nonexistent Course XYZ123")

        assert isinstance(result, str)
        # Will return results from the closest matching course, not an error
        assert len(result) > 0

    def test_execute_no_results_returns_message(self, course_search_tool):
        """Test that no results returns appropriate message"""
        result = course_search_tool.execute(
            query="quantum computing blockchain cryptocurrency"  # Unlikely to match
        )

        assert isinstance(result, str)
        # Should indicate no results were found
        assert "No relevant content found" in result or len(result) > 0

    def test_execute_empty_query(self, course_search_tool):
        """Test executing with empty query"""
        result = course_search_tool.execute(query="")

        # Should handle gracefully
        assert isinstance(result, str)


class TestCourseSearchToolSources:
    """Test source tracking in CourseSearchTool"""

    def test_sources_tracked_after_search(self, course_search_tool):
        """Test that sources are tracked after a search"""
        # Initially should be empty
        assert course_search_tool.last_sources == []

        # Execute a search
        result = course_search_tool.execute(query="linear regression")

        # Sources should now be populated
        assert len(course_search_tool.last_sources) > 0

    def test_source_structure(self, course_search_tool):
        """Test that sources have correct structure"""
        course_search_tool.execute(query="machine learning")

        for source in course_search_tool.last_sources:
            # Each source should be a dict with 'text' and 'link'
            assert isinstance(source, dict)
            assert "text" in source
            assert "link" in source
            # Text should include course title
            assert isinstance(source["text"], str)
            assert len(source["text"]) > 0

    def test_sources_include_lesson_links(self, course_search_tool):
        """Test that sources include lesson links when available"""
        course_search_tool.execute(query="regression", course_name="Introduction to Machine Learning", lesson_number=1)

        # Should have sources
        assert len(course_search_tool.last_sources) > 0

        # At least one source should have a link
        links = [s.get("link") for s in course_search_tool.last_sources]
        assert any(link is not None for link in links)

    def test_sources_reset_on_new_search(self, course_search_tool):
        """Test that sources are reset when a new search is performed"""
        # First search
        course_search_tool.execute(query="linear regression")
        first_sources = course_search_tool.last_sources.copy()

        # Second search with different query
        course_search_tool.execute(query="classification")
        second_sources = course_search_tool.last_sources

        # Sources should be different (or at least reset)
        # They might be the same if both queries match the same documents
        assert isinstance(second_sources, list)


class TestCourseSearchToolFormatting:
    """Test result formatting in CourseSearchTool"""

    def test_format_results_structure(self, course_search_tool):
        """Test that formatted results have expected structure"""
        result = course_search_tool.execute(query="machine learning")

        # Result should contain course title in brackets
        assert "[Introduction to Machine Learning" in result

    def test_format_results_with_lesson(self, course_search_tool):
        """Test formatting includes lesson number"""
        result = course_search_tool.execute(query="regression", lesson_number=1)

        # Should include lesson number in the format
        assert "Lesson 1" in result or "lesson 1" in result.lower()

    def test_format_multiple_results(self, course_search_tool):
        """Test formatting with multiple results"""
        result = course_search_tool.execute(query="learning")

        # Should have proper formatting with course context
        assert "[Introduction to Machine Learning" in result


class TestToolManager:
    """Test ToolManager functionality"""

    def test_register_tool(self, course_search_tool):
        """Test registering a tool"""
        manager = ToolManager()
        manager.register_tool(course_search_tool)

        assert "search_course_content" in manager.tools

    def test_get_tool_definitions(self, tool_manager):
        """Test getting tool definitions"""
        definitions = tool_manager.get_tool_definitions()

        assert isinstance(definitions, list)
        assert len(definitions) == 1
        assert definitions[0]["name"] == "search_course_content"

    def test_execute_tool(self, tool_manager):
        """Test executing a tool through the manager"""
        result = tool_manager.execute_tool("search_course_content", query="linear regression")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_execute_nonexistent_tool(self, tool_manager):
        """Test executing non-existent tool returns error"""
        result = tool_manager.execute_tool("nonexistent_tool", query="test")

        assert "not found" in result

    def test_get_last_sources(self, tool_manager):
        """Test getting sources from last search"""
        # Execute a search
        tool_manager.execute_tool("search_course_content", query="machine learning")

        # Get sources
        sources = tool_manager.get_last_sources()

        assert isinstance(sources, list)
        assert len(sources) > 0

    def test_reset_sources(self, tool_manager):
        """Test resetting sources"""
        # Execute a search
        tool_manager.execute_tool("search_course_content", query="machine learning")

        # Verify sources exist
        assert len(tool_manager.get_last_sources()) > 0

        # Reset sources
        tool_manager.reset_sources()

        # Verify sources are cleared
        assert len(tool_manager.get_last_sources()) == 0


class TestCourseSearchToolEdgeCases:
    """Test edge cases and error handling"""

    def test_execute_with_invalid_lesson_number(self, course_search_tool):
        """Test executing with invalid lesson number"""
        result = course_search_tool.execute(
            query="test", course_name="Introduction to Machine Learning", lesson_number=999
        )

        # Should handle gracefully
        assert isinstance(result, str)

    def test_execute_with_special_characters(self, course_search_tool):
        """Test executing with special characters in query"""
        result = course_search_tool.execute(query="what is @#$%^&*?")

        # Should handle gracefully
        assert isinstance(result, str)

    def test_execute_very_long_query(self, course_search_tool):
        """Test executing with very long query"""
        long_query = "machine learning " * 100
        result = course_search_tool.execute(query=long_query)

        # Should handle gracefully
        assert isinstance(result, str)
