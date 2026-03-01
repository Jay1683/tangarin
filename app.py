from main import TangarinDBAnalyzer
from langchain.messages import HumanMessage
import chainlit as cl


@cl.on_chat_start
async def on_chat_start():
    analyzer = TangarinDBAnalyzer()
    agent = analyzer.agent

    cl.user_session.set("agent", agent)


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")

    msg = cl.Message(content="")

    async for event in agent.astream_events(
        {"messages": [HumanMessage(message.content)]},
        version="v2",
    ):
        event_type = event["event"]
        if event_type == "on_chat_model_stream":
            metadata = event.get("metadata", {})
            node = metadata.get("langgraph_node")
            chunk = event["data"]["chunk"]

            # Only stream from the 'model' node (not 'tools')
            # and only when it's NOT building a tool call
            if (
                node == "model"
                and hasattr(chunk, "content")
                and chunk.content
                and not chunk.tool_call_chunks
            ):
                await msg.stream_token(chunk.content)

    await msg.send()
