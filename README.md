# Tangarin 🧠💬

### Natural Language SQL Agent with Chainlit + LangChain + Groq

Tangarin is a **Natural Language to SQL AI Agent** that connects to a PostgreSQL database and allows users to ask questions in plain English.

It automatically:

- Inspects database tables
- Generates safe SQL queries
- Executes them
- Returns clean, readable answers
- Streams responses in real-time using Chainlit

Built using:

- LangChain
- LangGraph Agent Runtime
- Chainlit UI
- Groq LLM (gpt-oss-120b)
- PostgreSQL

---

## 🚀 Features

- 🔎 Automatic schema discovery
- 🧠 LLM-powered SQL query generation
- ⚠️ Safe query execution (No DML allowed)
- 📡 Streaming responses in UI
- 🛠 Tool-based agent architecture
- 🗄 PostgreSQL support

---

## 🏗 Project Structure

```bash
├── answer.md
├── app.py
├── chainlit.md
├── load_llm.py
├── main.py
├── __pycache__
├── pyproject.toml
├── README.md
├── test.ipynb
└── uv.lock
```

---

## 🧠 How It Works

1. User asks a question in plain English.
2. Agent inspects available tables.
3. Agent checks schema of relevant tables.
4. Agent generates a syntactically correct SQL query.
5. Query is validated.
6. Query is executed.
7. Final answer is streamed back to the user.

The agent is strictly instructed to:

- Never modify data
- Never use DML statements (INSERT, UPDATE, DELETE, DROP)
- Always limit results (top 5 unless specified)
- Double-check queries before execution

---

## 🛠 Installation

### 1️⃣ Clone the repository

```bash
git clone git@github.com:Jay1683/tangarin.git
cd tangarin
```

---

### 2️⃣ Install dependencies (Recommended: uv)

```bash
uv sync
```

Or using pip:

```bash
pip install -r requirements.txt
```

---

### 3️⃣ Setup Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key

DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
```

---

## ▶️ Running the Application

### Run Chainlit UI

```bash
chainlit run app.py
```

Then open:

```
http://localhost:8000
```

---

### Run CLI Mode (Optional)

```bash
python main.py
```

Then ask:

```
Ask: Show top 5 customers by revenue
```

Type `quit` or `q` to exit.

---

## 🧠 LLM Configuration

Model used:

```
openai/gpt-oss-120b
```

Configured with:

- Temperature: 0
- Streaming: Enabled
- Max retries: 2
- Reasoning format: parsed

You can modify the model configuration inside:

```
load_llm.py
```

---

## 🔐 Safety Guardrails

The system prompt enforces:

- No INSERT
- No UPDATE
- No DELETE
- No DROP
- No schema changes
- Limited result size
- Mandatory schema inspection before querying

---

## 📡 Streaming Logic

In `app.py`, only content from the `"model"` node is streamed.

Tool call chunks are filtered to prevent raw SQL or internal tool reasoning from appearing in the UI.

This ensures:

- Clean user responses
- No tool debug leakage
- Smooth token streaming

---

## 📊 Example Queries

You can ask:

- "What are the top 5 selling products?"
- "Show total revenue by month"
- "Which customers placed the most orders?"
- "List all available tables"

---

## 🔧 Customization Ideas

- Add memory for conversational continuity
- Add role-based DB access
- Deploy via Docker
- Add authentication layer
- Add multi-database support

---

## 👨‍💻 Author

Jay Dhumal
