import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

from load_llm import model

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


class TangarinDBAnalyzer:
    def __init__(self):
        self.db = SQLDatabase.from_uri(
            f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

        # print(f"Dialect: {db.dialect}")
        # print(f"Available tables: {db.get_usable_table_names()}")
        # print(f'Sample output: {db.run("SELECT * FROM t_shirts LIMIT 5;")}')

        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=model)

        self.tools = self.toolkit.get_tools()

        # for tool in tools:
        #     print(f"{tool.name}: {tool.description}\n")

        self.system_prompt = SystemMessage(
            """
        You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct {dialect} query to run,
        then look at the results of the query and return the answer. Unless the user
        specifies a specific number of examples they wish to obtain, always limit your
        query to at most {top_k} results.

        You can order the results by a relevant column to return the most interesting
        examples in the database. Never query for all the columns from a specific table,
        only ask for the relevant columns given the question.

        You MUST double check your query before executing it. If you get an error while
        executing a query, rewrite the query and try again.

        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the
        database.

        To start you should ALWAYS look at the tables in the database to see what you
        can query. Do NOT skip this step.

        Then you should query the schema of the most relevant tables.
        """.format(
                dialect=self.db.dialect,
                top_k=5,
            )
        )

        self.agent = create_agent(
            model=model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )


if __name__ == "__main__":
    analyzer = TangarinDBAnalyzer()

    while True:
        question = input("Ask: ")
        if question in ["quit", "q"]:
            break
        else:
            print(analyzer.agent.invoke(HumanMessage(question))["messages"][-1].content)
