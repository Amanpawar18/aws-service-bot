from unittest.mock import MagicMock, patch

from app.agent.agent import build_agent


def test_build_agent_configures_tavily() -> None:
    with (
        patch("app.agent.agent.ChatBedrockConverse"),
        patch("app.agent.agent.TavilySearch") as mock_tool_cls,
        patch("app.agent.agent.create_agent") as mock_create,
    ):
        mock_create.return_value = MagicMock()
        build_agent()

    mock_tool_cls.assert_called_once_with(
        name="web_search",
        description=(
            "Search official AWS documentation at docs.aws.amazon.com. "
            "Use this for any question about AWS services, features, APIs, "
            "or best practices. Input should be a specific search query."
        ),
        max_results=5,
        include_domains=["docs.aws.amazon.com"],
        search_depth="advanced",
        tavily_api_key="test-key-for-unit-tests",
    )


def test_build_agent_uses_memory_checkpointer() -> None:
    with (
        patch("app.agent.agent.ChatBedrockConverse"),
        patch("app.agent.agent.TavilySearch"),
        patch("app.agent.agent.MemorySaver") as mock_saver_cls,
        patch("app.agent.agent.create_agent") as mock_create,
    ):
        mock_saver_instance = MagicMock()
        mock_saver_cls.return_value = mock_saver_instance
        mock_create.return_value = MagicMock()
        build_agent()

    kwargs = mock_create.call_args.kwargs
    assert kwargs.get("checkpointer") is mock_saver_instance


def test_build_agent_passes_system_prompt() -> None:
    with (
        patch("app.agent.agent.ChatBedrockConverse"),
        patch("app.agent.agent.TavilySearch"),
        patch("app.agent.agent.MemorySaver"),
        patch("app.agent.agent.create_agent") as mock_create,
    ):
        mock_create.return_value = MagicMock()
        build_agent()

    kwargs = mock_create.call_args.kwargs
    assert "system_prompt" in kwargs
    assert "AWS" in kwargs["system_prompt"]
