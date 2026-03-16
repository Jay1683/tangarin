from main import TangarinDBAnalyzer
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from langchain_core.messages import HumanMessage
import chainlit as cl
import os


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=os.getenv("DATABASE_URL"))


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Replace this with your own logic — DB lookup, env vars, etc.
    if username == "admin" and password == "securepassword":
        return cl.User(identifier="admin", metadata={"role": "admin"})
    return None  # Returning None = login rejected


@cl.on_chat_start
async def on_chat_start():
    analyzer = TangarinDBAnalyzer()
    cl.user_session.set("agent", analyzer.agent)


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

            if (
                node == "model"
                and hasattr(chunk, "content")
                and chunk.content
                and not chunk.tool_call_chunks
            ):
                await msg.stream_token(chunk.content)

    await msg.send()
