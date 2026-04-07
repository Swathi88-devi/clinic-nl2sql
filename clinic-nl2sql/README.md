## Project Description

This project is an AI-powered **Natural Language to SQL (NL2SQL) system** built using **Vanna 2.0 and FastAPI**.
The main goal of the system is to allow users to interact with a database using **plain English queries**, without needing to write SQL manually. The system takes a user’s question, converts it into a SQL query using an LLM (Google Gemini), executes it on a SQLite database, and returns the results in a structured format.
For example, a user can ask:
> "Show the top 5 patients by total spending"
The system will:
1. Convert the question into a SQL query
2. Validate the query for safety
3. Execute it on the database
4. Return results along with an optional chart
The backend is built using **FastAPI**, and the AI logic is handled using **Vanna 2.0’s agent-based architecture**, which includes tools for SQL execution, visualization, and memory learning.
A sample clinic management database is used, containing data about:
* patients
* doctors
* appointments
* treatments
* invoices
This project demonstrates how AI can be integrated into backend systems to enable **intelligent data querying**, while also handling real-world challenges like SQL validation, error handling, and schema mismatches.

## Setup Instructions

Follow the steps below to set up and run the complete NL2SQL system.
### 1. Clone the Repository

```bash
git clone <your-repository-link>
cd project
```
### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate   # On Windows
```
### 3. Install Dependencies

```bash
pip install -r requirements.txt
```
This installs:

* Vanna 2.0 (NL2SQL agent)
* FastAPI (backend framework)
* Plotly (charts)
* Google Gemini SDK (LLM)
### 4. Setup Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_api_key_here
```
Get your free API key from:
https://aistudio.google.com/apikey
### 5. Create and Populate Database

Run:

```bash
python setup_database.py
```

 What this does:

* Creates `clinic.db`
* Creates all 5 tables (patients, doctors, appointments, treatments, invoices)
* Inserts realistic dummy data (200 patients, 500 appointments, etc.)

---

### 6. Initialize Vanna Agent (vanna_setup.py)

No manual command needed, but this file is **automatically used** when the API starts.

👉 What it does:

* Connects to the SQLite database
* Initializes Gemini LLM
* Sets up tools (SQL execution, visualization, memory)
* Creates the Vanna agent

---

### 7. Seed Agent Memory

Run:

```bash
python seed_memory.py
```

👉 What this does:

* Adds predefined question–SQL pairs
* Helps the agent understand database schema and query patterns

---

### 8. Start the API Server

```bash
uvicorn main:app --port 8000
```

👉 What happens:

* `main.py` starts the FastAPI server
* Loads the Vanna agent
* Exposes API endpoints (`/chat`, `/health`)

---

### 9. Access the API

Open in browser:

```
http://localhost:8000/docs
```

This opens Swagger UI where you can test the system.

---

### Run Everything (Quick Setup)

```bash
pip install -r requirements.txt && \
python setup_database.py && \
python seed_memory.py && \
uvicorn main:app --port 8000
```
