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
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                await msg.stream_token(chunk.content)

    await msg.send()
