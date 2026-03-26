import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.tools.retriever import create_retriever_tool
from langgraph.checkpoint.memory import MemorySaver

from load_llm import model

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


class TangarinDBAnalyzer:
    def __init__(self, vector_store=None):
        self.db = SQLDatabase.from_uri(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=model)
        self.tools = self.toolkit.get_tools()

        # ✅ If a vector store is provided, add a retriever tool
        if vector_store is not None:
            retriever = vector_store.as_retriever(search_kwargs={"k": 5})
            retriever_tool = create_retriever_tool(
                retriever=retriever,
                name="search_uploaded_file",
                description=(
                    "Use this tool to search and retrieve information from the "
                    "user's uploaded CSV or Excel file. Use this when the question "
                    "is about the uploaded file rather than the database."
                ),
            )
            self.tools.append(retriever_tool)

        self.system_prompt = SystemMessage(
            """
        You are an agent designed to interact with a SQL database and optionally
        with uploaded data files (CSV, Excel).

        Given an input question, decide whether to query the SQL database, search
        the uploaded file, or both.

        When querying SQL:
        - Create a syntactically correct {dialect} query
        - Always limit results to at most {top_k} unless specified
        - Never query all columns — only relevant ones
        - Double check your query before executing
        - DO NOT use DML statements (INSERT, UPDATE, DELETE, DROP)
        - Always inspect available tables first

        When using the uploaded file:
        - Use the search_uploaded_file tool to retrieve relevant content
        - Summarize and present findings clearly

        If the question involves both the database and the uploaded file, use both
        tools and synthesize the results.
        """.format(
                dialect=self.db.dialect,
                top_k=5,
            )
        )

        self.checkpointer = MemorySaver()

        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=self.checkpointer,
        )


if __name__ == "__main__":
    analyzer = TangarinDBAnalyzer()
    thread_id = "cli-session"

    while True:
        question = input("Ask: ")
        if question in ["quit", "q"]:
            break
        else:
            result = analyzer.agent.invoke(
                {"messages": [HumanMessage(question)]},
                config={"configurable": {"thread_id": thread_id}},
            )
            print(result["messages"][-1].content)
