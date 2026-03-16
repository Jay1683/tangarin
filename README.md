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
- 🔐 Password-based authentication
- 💾 Persistent chat history via SQLAlchemy data layer

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

1. User logs in via the Chainlit login screen.
2. User asks a question in plain English.
3. Agent inspects available tables.
4. Agent checks schema of relevant tables.
5. Agent generates a syntactically correct SQL query.
6. Query is validated.
7. Query is executed.
8. Final answer is streamed back to the user.

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

# SQLAlchemy async connection string for Chainlit data layer
DATABASE_URL=postgresql+asyncpg://your_db_user:your_db_password@localhost:5432/your_database

# Secret used to sign Chainlit auth tokens — generate with: chainlit create-secret
CHAINLIT_AUTH_SECRET=your_generated_secret
```

---

### 4️⃣ Set Up the Chainlit Data Layer Schema

Run the following SQL against your PostgreSQL database to create the required tables for Chainlit's persistence layer (chat history, users, feedback):

```sql
CREATE TABLE users (
    "id" UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" JSONB NOT NULL,
    "createdAt" TEXT
);

CREATE TABLE IF NOT EXISTS threads (
    "id" UUID PRIMARY KEY,
    "createdAt" TEXT,
    "name" TEXT,
    "userId" UUID,
    "userIdentifier" TEXT,
    "tags" TEXT[],
    "metadata" JSONB,
    FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS steps (
    "id" UUID PRIMARY KEY,
    "name" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "threadId" UUID NOT NULL,
    "parentId" UUID,
    "streaming" BOOLEAN NOT NULL,
    "waitForAnswer" BOOLEAN,
    "isError" BOOLEAN,
    "metadata" JSONB,
    "tags" TEXT[],
    "input" TEXT,
    "output" TEXT,
    "createdAt" TEXT,
    "command" TEXT,
    "start" TEXT,
    "end" TEXT,
    "generation" JSONB,
    "showInput" TEXT,
    "language" TEXT,
    "indent" INT,
    "defaultOpen" BOOLEAN,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS elements (
    "id" UUID PRIMARY KEY,
    "threadId" UUID,
    "type" TEXT,
    "url" TEXT,
    "chainlitKey" TEXT,
    "name" TEXT NOT NULL,
    "display" TEXT,
    "objectKey" TEXT,
    "size" TEXT,
    "page" INT,
    "language" TEXT,
    "forId" UUID,
    "mime" TEXT,
    "props" JSONB,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feedbacks (
    "id" UUID PRIMARY KEY,
    "forId" UUID NOT NULL,
    "threadId" UUID NOT NULL,
    "value" INT NOT NULL,
    "comment" TEXT,
    FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
);
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

You will be prompted with a login screen. Use the admin credentials configured in `app.py`.

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

## 🔐 Authentication

Tangarin uses **Chainlit's built-in password authentication**.

### How it works

- A login screen is shown before users can access the chat.
- Credentials are validated inside the `@cl.password_auth_callback` in `app.py`.
- On successful login, Chainlit issues a signed JWT using `CHAINLIT_AUTH_SECRET`.
- Chat history is persisted per user via the SQLAlchemy data layer.

### Generating the auth secret

```bash
chainlit create-secret
```

Copy the output into your `.env` as `CHAINLIT_AUTH_SECRET`.

> ⚠️ If you change `CHAINLIT_AUTH_SECRET`, all existing sessions are invalidated and users will need to log in again.

### Default credentials

The default admin credentials are hardcoded in `app.py` for development. **Change these before deploying to any shared or production environment.**

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

- Add self-service user registration
- Add memory for conversational continuity
- Add role-based DB access
- Deploy via Docker
- Add multi-database support

---

## 👨‍💻 Author

Jay Dhumal