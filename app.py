from main import TangarinDBAnalyzer
from chainlit.data import get_data_layer
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from langchain_core.messages import HumanMessage, SystemMessage
import chainlit as cl
import os

from load_llm import model


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=os.getenv("DATABASE_URL"))


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if username == "admin" and password == os.getenv("ADMIN_PASSWORD"):
        return cl.User(identifier="admin", metadata={"role": "admin"})
    return None


async def generate_thread_title(first_message: str) -> str:
    response = await model.ainvoke(
        [
            SystemMessage(
                content=(
                    "You are a helpful assistant that generates very short, descriptive chat titles. "
                    "Given the user's first message, respond with ONLY a title of 3-6 words. "
                    "No punctuation at the end. No quotes. Just the title."
                )
            ),
            HumanMessage(content=first_message),
        ]
    )
    return response.content.strip()


@cl.on_chat_start
async def on_chat_start():
    analyzer = TangarinDBAnalyzer()
    cl.user_session.set("agent", analyzer.agent)
    cl.user_session.set("is_first_message", True)  # ✅ set the flag


@cl.on_chat_resume
async def on_chat_resume(thread):
    analyzer = TangarinDBAnalyzer()
    cl.user_session.set("agent", analyzer.agent)
    cl.user_session.set("is_first_message", False)  # ✅ already titled, skip


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.context.session.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    if cl.user_session.get("is_first_message"):
        title = await generate_thread_title(message.content)
        data_layer = get_data_layer()
        if data_layer:
            await data_layer.update_thread(thread_id=thread_id, name=title)
        cl.user_session.set("is_first_message", False)

    msg = cl.Message(content="")  # ✅ must be outside and after the if block

    async for event in agent.astream_events(
        {"messages": [HumanMessage(message.content)]},
        config=config,
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
