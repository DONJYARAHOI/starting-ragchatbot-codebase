"""
Tests for AIGenerator tool calling functionality
These tests verify the AI correctly uses tools when appropriate
"""

from unittest.mock import MagicMock, patch

import pytest
from ai_generator import AIGenerator


class TestAIGeneratorToolDefinitions:
    """Test that AIGenerator correctly handles tool definitions"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_accepts_tool_definitions(self, mock_anthropic):
        """Test that generator accepts and uses tool definitions"""
        # Create a mock client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Setup mock response (no tool use)
        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Test response")]
        mock_client.messages.create.return_value = mock_response

        # Create generator
        generator = AIGenerator(api_key="test-key", model="test-model")

        # Create mock tools
        tools = [
            {
                "name": "search_course_content",
                "description": "Search for course content",
                "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            }
        ]

        # Generate response with tools
        response = generator.generate_response(query="Test query", tools=tools)

        # Verify tools were passed to API
        call_args = mock_client.messages.create.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == tools


class TestAIGeneratorToolCalling:
    """Test that AIGenerator correctly calls tools"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_tool_call_triggers_execution(self, mock_anthropic):
        """Test that when AI requests tool use, it gets executed"""
        # Create a mock client
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Setup mock response indicating tool use
        initial_response = MagicMock()
        initial_response.stop_reason = "tool_use"

        # Mock tool use content block
        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.id = "test-tool-id"
        tool_use_block.input = {"query": "test query"}

        initial_response.content = [tool_use_block]

        # Setup final response after tool execution
        final_response = MagicMock()
        final_response.stop_reason = "end_turn"
        final_response.content = [MagicMock(text="Final response")]

        # Configure mock to return different responses on subsequent calls
        mock_client.messages.create.side_effect = [initial_response, final_response]

        # Create generator
        generator = AIGenerator(api_key="test-key", model="test-model")

        # Create mock tool manager
        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Tool result"

        # Generate response
        tools = [{"name": "search_course_content", "description": "test"}]
        response = generator.generate_response(
            query="What is machine learning?", tools=tools, tool_manager=mock_tool_manager
        )

        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with("search_course_content", query="test query")

        # Verify we got the final response
        assert response == "Final response"

    @patch("ai_generator.anthropic.Anthropic")
    def test_tool_result_passed_back_to_ai(self, mock_anthropic):
        """Test that tool results are correctly passed back to AI"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Initial response with tool use
        initial_response = MagicMock()
        initial_response.stop_reason = "tool_use"
        tool_use_block = MagicMock()
        tool_use_block.type = "tool_use"
        tool_use_block.name = "search_course_content"
        tool_use_block.id = "tool-123"
        tool_use_block.input = {"query": "test"}
        initial_response.content = [tool_use_block]

        # Final response
        final_response = MagicMock()
        final_response.stop_reason = "end_turn"
        final_response.content = [MagicMock(text="Answer based on tool result")]

        mock_client.messages.create.side_effect = [initial_response, final_response]

        generator = AIGenerator(api_key="test-key", model="test-model")

        mock_tool_manager = MagicMock()
        mock_tool_manager.execute_tool.return_value = "Search results here"

        tools = [{"name": "search_course_content"}]
        response = generator.generate_response(query="test", tools=tools, tool_manager=mock_tool_manager)

        # Verify second call included tool results
        assert mock_client.messages.create.call_count == 2
        second_call = mock_client.messages.create.call_args_list[1]

        # Check that messages include tool result
        messages = second_call.kwargs["messages"]
        # Should have 3 messages: User query, Assistant (tool use), User (tool result)
        assert len(messages) == 3

        # Find the tool result message (should be the last one)
        tool_result_msg = messages[2]
        assert tool_result_msg["role"] == "user"
        assert isinstance(tool_result_msg["content"], list)

        # Verify tool result content
        tool_result_content = tool_result_msg["content"][0]
        assert tool_result_content["type"] == "tool_result"
        assert tool_result_content["tool_use_id"] == "tool-123"
        assert tool_result_content["content"] == "Search results here"


class TestAIGeneratorWithoutTools:
    """Test that AIGenerator works correctly without tools"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_works_without_tools(self, mock_anthropic):
        """Test generator works when no tools provided"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Direct answer")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(api_key="test-key", model="test-model")

        response = generator.generate_response(query="What is 2+2?")

        assert response == "Direct answer"

        # Verify tools were not passed
        call_args = mock_client.messages.create.call_args
        assert "tools" not in call_args.kwargs or call_args.kwargs.get("tools") is None


class TestAIGeneratorConversationHistory:
    """Test that AIGenerator handles conversation history"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_includes_conversation_history(self, mock_anthropic):
        """Test that conversation history is included in system prompt"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(api_key="test-key", model="test-model")

        history = "User: Previous question\nAssistant: Previous answer"

        generator.generate_response(query="New question", conversation_history=history)

        # Verify history was included in system prompt
        call_args = mock_client.messages.create.call_args
        system_content = call_args.kwargs["system"]
        assert history in system_content


class TestAIGeneratorSystemPrompt:
    """Test AIGenerator system prompt for tool usage guidance"""

    def test_system_prompt_mentions_search_tool(self):
        """Test that system prompt mentions search tool usage"""
        # The SYSTEM_PROMPT should guide the AI to use search tools
        assert hasattr(AIGenerator, "SYSTEM_PROMPT")
        system_prompt = AIGenerator.SYSTEM_PROMPT

        # Check for key guidance about tool usage
        assert "search" in system_prompt.lower()

    def test_system_prompt_limits_searches(self):
        """Test that system prompt limits number of searches"""
        system_prompt = AIGenerator.SYSTEM_PROMPT

        # Should mention limiting searches
        assert "one search" in system_prompt.lower() or "single search" in system_prompt.lower()


class TestAIGeneratorParameters:
    """Test AIGenerator parameter handling"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_uses_configured_model(self, mock_anthropic):
        """Test that generator uses the configured model"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        test_model = "claude-3-sonnet-20240229"
        generator = AIGenerator(api_key="test-key", model=test_model)

        generator.generate_response(query="test")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == test_model

    @patch("ai_generator.anthropic.Anthropic")
    def test_uses_configured_temperature(self, mock_anthropic):
        """Test that generator uses temperature 0"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(api_key="test-key", model="test-model")

        generator.generate_response(query="test")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["temperature"] == 0

    @patch("ai_generator.anthropic.Anthropic")
    def test_uses_configured_max_tokens(self, mock_anthropic):
        """Test that generator uses max_tokens setting"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Response")]
        mock_client.messages.create.return_value = mock_response

        generator = AIGenerator(api_key="test-key", model="test-model")

        generator.generate_response(query="test")

        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["max_tokens"] == 800


class TestAIGeneratorErrorHandling:
    """Test AIGenerator error handling"""

    @patch("ai_generator.anthropic.Anthropic")
    def test_handles_api_errors(self, mock_anthropic):
        """Test that generator handles API errors gracefully"""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Simulate API error
        mock_client.messages.create.side_effect = Exception("API Error")

        generator = AIGenerator(api_key="test-key", model="test-model")

        # Should raise exception (or could be caught and handled)
        with pytest.raises(Exception) as exc_info:
            generator.generate_response(query="test")

        assert "API Error" in str(exc_info.value)
