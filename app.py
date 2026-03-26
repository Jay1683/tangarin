from main import TangarinDBAnalyzer
from file_handler import process_csv_excel, load_faiss, get_thread_dir
from chainlit.data import get_data_layer
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from langchain_core.messages import HumanMessage, SystemMessage
import chainlit as cl
import os
import shutil
from pathlib import Path

from load_llm import model


@cl.data_layer
def get_data_layer_instance():
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


def init_agent(thread_id: str):
    """Initialize agent, reloading FAISS index if one exists for this thread."""
    vector_store = load_faiss(thread_id)
    analyzer = TangarinDBAnalyzer(vector_store=vector_store)
    cl.user_session.set("agent", analyzer.agent)


@cl.on_chat_start
async def on_chat_start():
    thread_id = cl.context.session.thread_id
    init_agent(thread_id)
    cl.user_session.set("is_first_message", True)


@cl.on_chat_resume
async def on_chat_resume(thread):
    thread_id = cl.context.session.thread_id
    init_agent(thread_id)
    cl.user_session.set("is_first_message", False)


@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent")
    thread_id = cl.context.session.thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # ✅ Handle any uploaded files first
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                ext = Path(element.name).suffix.lower()

                if ext in [".csv", ".xlsx", ".xls"]:
                    # Save file to uploads/<thread_id>/
                    thread_dir = get_thread_dir(thread_id)
                    dest_path = thread_dir / element.name
                    shutil.copy(element.path, str(dest_path))

                    await cl.Message(
                        content=f"📂 Processing `{element.name}`..."
                    ).send()

                    # Build vector store and reinitialize agent with it
                    vector_store = await process_csv_excel(str(dest_path), thread_id)
                    analyzer = TangarinDBAnalyzer(vector_store=vector_store)
                    cl.user_session.set("agent", analyzer.agent)
                    agent = analyzer.agent

                    await cl.Message(
                        content=f"✅ `{element.name}` is ready. You can now ask questions about it."
                    ).send()
                else:
                    await cl.Message(
                        content=f"⚠️ `{element.name}` is not supported in Phase 1. CSV and Excel only for now."
                    ).send()

        # If the message was only a file upload with no text, stop here
        if not message.content.strip():
            return

    # ✅ Title generation on first message
    if cl.user_session.get("is_first_message"):
        title = await generate_thread_title(message.content)
        data_layer = get_data_layer()
        if data_layer:
            await data_layer.update_thread(thread_id=thread_id, name=title)
        cl.user_session.set("is_first_message", False)

    msg = cl.Message(content="")

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
