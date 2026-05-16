from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph

from app.config import settings

_SYSTEM_PROMPT = """You are an expert AWS documentation assistant.

Always respond directly. Never include <thinking> tags or expose \
internal reasoning in your response.

For AWS-related questions:
- Use the web_search tool to search official AWS documentation
- Base your answer strictly on the search results
- End your answer with a "**Sources:**" section listing the relevant URLs

For greetings (e.g. "hello", "hi"):
- Respond briefly, let the user know you answer AWS documentation questions
- Do not add a Sources section

For any question not related to AWS products, services, or concepts:
- Reply with one sentence: explain you only answer AWS-related questions
- Do not use any tools
- Do not add a Sources section

Conversation history is available in context. Use it to understand follow-up questions \
and resolve pronouns like "it", "that", or "them" before searching."""


def build_agent() -> CompiledStateGraph:  # type: ignore[type-arg]
    llm = ChatBedrockConverse(
        model=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )
    tool = TavilySearch(
        name="web_search",
        description=(
            "Search official AWS documentation at docs.aws.amazon.com. "
            "Use this for any question about AWS services, features, APIs, "
            "or best practices. Input should be a specific search query."
        ),
        max_results=5,
        include_domains=["docs.aws.amazon.com"],
        search_depth="advanced",
        tavily_api_key=settings.tavily_api_key,
    )
    return create_agent(
        model=llm,
        tools=[tool],
        system_prompt=_SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
