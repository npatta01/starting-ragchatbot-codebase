from typing import Any, Dict, List, Optional

import anthropic


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive tools for course information.

Available Tools:
- **search_course_content**: Search for specific information within course materials
- **get_course_outline**: Retrieve complete course structure including all lessons and metadata

Tool Usage Guidelines:
- Use **get_course_outline** when users ask about:
  - Course structure or organization
  - What lessons/topics are covered
  - Course overview or table of contents
  - List of lessons in a course

- Use **search_course_content** when users ask about:
  - Specific topics or concepts within courses
  - Detailed explanations or examples
  - Content from specific lessons

- **Multi-Round Tool Usage**:
  - You can make up to 2 sequential tool calls per query for complex questions
  - First call: Get broad context or initial information
  - Second call (if needed): Refine search or get additional details
  - Example: First get course outline → then search specific lesson content
  - Most queries should use just 1 tool call - only use 2 when first result is insufficient

- Synthesize tool results into accurate, fact-based responses
- Do not mention "I'll search again" or announce tool usage - just provide the answer
- If a tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without tools
- **Course-specific questions**: Use appropriate tool first, then answer
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool selection explanations, or question-type analysis
 - Do not mention "based on the outline" or "according to the search results"

Formatting Course Outlines:
- When presenting course outlines, organize information clearly
- Include course title, instructor, and lesson structure
- Present lessons in numbered order
- Include links when available

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        # Validate API key
        if not api_key or api_key.strip() == "":
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. Please add it to your .env file:\n"
                "ANTHROPIC_API_KEY=your_key_here"
            )

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with optional tool usage and conversation context.

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude with error handling
        try:
            response = self.client.messages.create(**api_params)
        except anthropic.AuthenticationError as e:
            raise ValueError(f"Invalid API key: {str(e)}")
        except anthropic.RateLimitError as e:
            raise RuntimeError(
                f"Rate limit exceeded: {str(e)}. Please try again later."
            )
        except anthropic.APIConnectionError as e:
            raise RuntimeError(
                f"Network connection error: {str(e)}. Please check your internet connection."
            )
        except anthropic.APIStatusError as e:
            raise RuntimeError(f"API error (status {e.status_code}): {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error calling AI: {str(e)}")

        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution_iterative(
                response, api_params, tool_manager, max_rounds=2
            )

        # Return direct response
        return response.content[0].text

    def _handle_tool_execution_iterative(
        self,
        initial_response,
        base_params: Dict[str, Any],
        tool_manager,
        max_rounds: int = 2,
    ) -> str:
        """
        Handle sequential tool execution rounds.

        Flow:
        - Round 0: Initial tool call → execute → results to Claude
        - Round 1: Claude sees results → may call another tool OR return final answer
        - Round 2+: Continue until max_rounds or Claude returns end_turn

        Termination conditions:
        1. iteration >= max_rounds
        2. stop_reason != "tool_use" (Claude returned text)
        3. Tool execution error (graceful degradation)

        Args:
            initial_response: The response containing initial tool use requests
            base_params: Base API parameters (includes tools, system, model, etc.)
            tool_manager: Manager to execute tools
            max_rounds: Maximum number of tool call rounds (default: 2)

        Returns:
            Final response text after all tool executions complete
        """
        # Initialize message history with the original user query
        messages = base_params["messages"].copy()

        # Track current response (starts with initial tool_use response)
        current_response = initial_response

        # Iteration counter
        iteration = 0

        # Iterative loop for sequential tool calling
        while iteration < max_rounds:
            iteration += 1

            # Check if current response contains tool use
            if current_response.stop_reason != "tool_use":
                # No more tool calls - Claude provided final answer
                break

            # Add Claude's tool use request to message history
            messages.append({"role": "assistant", "content": current_response.content})

            # Execute all tool calls in current response
            tool_results = []

            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        tool_result = tool_manager.execute_tool(
                            content_block.name, **content_block.input
                        )

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": tool_result,
                            }
                        )

                    except Exception as e:
                        # Tool execution failed - add error result
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": content_block.id,
                                "content": f"Tool execution error: {str(e)}",
                                "is_error": True,
                            }
                        )

            # Add tool results to message history
            if tool_results:
                messages.append({"role": "user", "content": tool_results})

            # Prepare next API call WITH tools still available
            next_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"],
                "tools": base_params["tools"],  # KEY: Keep tools available
                "tool_choice": {"type": "auto"},  # Let Claude decide
            }

            # Make next API call with error handling
            try:
                current_response = self.client.messages.create(**next_params)
            except anthropic.AuthenticationError as e:
                raise ValueError(
                    f"Invalid API key in tool execution round {iteration}: {str(e)}"
                )
            except anthropic.RateLimitError as e:
                raise RuntimeError(
                    f"Rate limit exceeded in tool execution round {iteration}: {str(e)}. Please try again later."
                )
            except anthropic.APIConnectionError as e:
                raise RuntimeError(
                    f"Network error in tool execution round {iteration}: {str(e)}. Please check your internet connection."
                )
            except anthropic.APIStatusError as e:
                raise RuntimeError(
                    f"API error in tool execution round {iteration} (status {e.status_code}): {str(e)}"
                )
            except Exception as e:
                raise RuntimeError(
                    f"Unexpected error in tool execution round {iteration}: {str(e)}"
                )

        # After loop completes, current_response contains the final answer
        # Extract text from response (handle both text blocks and tool_use followed by text)
        for content_block in current_response.content:
            if hasattr(content_block, "text"):
                return content_block.text

        # Fallback if no text found
        return "Unable to generate response after tool execution."
