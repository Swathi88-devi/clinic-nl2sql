"""
Step 6: FastAPI Application - FINAL VERSION WITH SQL CORRECTION
Extracts SQL from messages and auto-corrects common errors
"""

import logging
import json
import sqlite3
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import plotly.graph_objects as go
import pandas as pd
from vanna_setup import get_agent
from vanna.core.user import RequestContext

# ==================== LOGGING ====================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = "clinic.db"

# ==================== SCHEMA MAPPING ====================
# Common column name variations - map to correct names
COLUMN_CORRECTIONS = {
    'doctor_name': 'name',
    'patient_name': 'first_name',  # Usually need first_name, last_name
    'patient_id': 'id',  # In patients table context
    'doctor_id': 'id',   # In doctors table context
    'treatment_id': 'id', # In treatments table context
}

TABLE_SCHEMA = {
    'patients': ['id', 'first_name', 'last_name', 'email', 'phone', 'gender', 'city', 'registered_date'],
    'doctors': ['id', 'name', 'specialization', 'department', 'phone'],
    'appointments': ['id', 'patient_id', 'doctor_id', 'appointment_date', 'status', 'notes'],
    'invoices': ['id', 'patient_id', 'invoice_date', 'total_amount', 'paid_amount', 'status'],
    'treatments': ['id', 'appointment_id', 'treatment_name', 'cost', 'notes'],
}

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    message: str
    sql_query: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[List[Any]]] = None
    row_count: Optional[int] = None
    chart: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    agent_memory_items: Optional[int] = None
    timestamp: str

# ==================== FASTAPI APP ====================

app = FastAPI(
    title="Clinic Natural Language to SQL API",
    description="AI-powered Natural Language to SQL chatbot",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== HELPERS ====================

def check_database_connection() -> bool:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except:
        return False

def get_memory_count(agent) -> int:
    try:
        memories = agent.agent_memory.get_recent_memories(None)
        return len(memories) if memories else 0
    except:
        return 0
def validate_sql_query(sql: str) -> tuple[bool, str]:
    """Validate SQL for safety (STEP 7 FINAL)"""
    try:
        if not sql or not sql.strip():
            return False, "Empty SQL query"

        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # Only SELECT allowed
        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries allowed"

        # Dangerous keywords
        dangerous_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
            "EXEC", "TRUNCATE",
            "GRANT", "REVOKE", "SHUTDOWN",
            "XP_", "SP_"
        ]

        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"Dangerous keyword detected: {keyword}"

        # System tables block
        system_tables = [
            "SQLITE_MASTER",
            "SQLITE_SCHEMA",
            "PRAGMA"
        ]

        for table in system_tables:
            if table in sql_upper:
                return False, f"Access to system table '{table}' is not allowed"

        # Prevent multiple queries
        if ";" in sql_clean[:-1]:
            return False, "Multiple SQL statements are not allowed"

        return True, ""

    except Exception as e:
        return False, str(e)

def correct_sql_query(sql: str) -> str:
    """
    Auto-correct common SQL errors
    """
    corrected = sql
    
    # Replace common column name mistakes
    for wrong, correct in COLUMN_CORRECTIONS.items():
        # Case-insensitive replacement
        corrected = re.sub(r'\b' + wrong + r'\b', correct, corrected, flags=re.IGNORECASE)
    
    logger.info(f"Original: {sql[:80]}")
    logger.info(f"Corrected: {corrected[:80]}")
    
    return corrected

def extract_sql_from_markdown(text: str) -> Optional[str]:
    """Extract SQL query from markdown code blocks in text"""
    if not text:
        return None
    
    # Try ```sql ... ``` format
    sql_pattern = r'```sql\s*(.*?)\s*```'
    match = re.search(sql_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        logger.info(f"Extracted SQL from ```sql block: {sql[:80]}")
        return sql
    
    # Try generic ``` ... ``` format
    code_pattern = r'```\s*(.*?)\s*```'
    match = re.search(code_pattern, text, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if code.upper().startswith('SELECT'):
            logger.info(f"Extracted SQL from generic code block: {code[:80]}")
            return code
    
    return None

def execute_sql_query(sql: str) -> tuple[bool, Optional[List[str]], Optional[List[List[Any]]], str]:
    """
    Execute SQL query and return results
    
    Returns:
        (success, columns, rows, message)
    """
    try:
        logger.info(f"Executing SQL: {sql[:100]}")
        
        # Validate first
        is_valid, error = validate_sql_query(sql)
        if not is_valid:
            return False, None, None, error
        
        # Try to correct common errors
        corrected_sql = correct_sql_query(sql)
        
        # Execute
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(corrected_sql)
        except sqlite3.OperationalError as e:
            # If corrected SQL fails, try original
            logger.warning(f"Corrected SQL failed: {e}, trying original...")
            cursor.execute(sql)
        
        # Get results
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"✓ Query executed: {len(rows)} rows, {len(columns)} columns")
        return True, columns, rows, ""
    
    except sqlite3.OperationalError as e:
        logger.error(f"SQL execution error: {e}")
        error_msg = str(e)
        
        # Try to suggest fix
        if "no such column" in error_msg:
            # Extract the column name
            match = re.search(r"no such column: (\w+)", error_msg)
            if match:
                wrong_col = match.group(1)
                # Look for suggestions
                for table_cols in TABLE_SCHEMA.values():
                    if wrong_col in table_cols:
                        error_msg += f" (Did you mean '{wrong_col}'?)"
        
        return False, None, None, error_msg
    
    except Exception as e:
        logger.error(f"SQL execution error: {e}")
        return False, None, None, str(e)

def generate_chart(columns: List[str], rows: List[List[Any]]) -> Optional[Dict[str, Any]]:
    """Generate Plotly chart from query results"""
    try:
        if not rows or len(rows) == 0:
            return None
        
        df = pd.DataFrame(rows, columns=columns)
        
        if len(columns) == 2:
            fig = go.Figure(data=[go.Bar(x=df[columns[0]], y=df[columns[1]])])
            fig.update_layout(title=f"{columns[0]} vs {columns[1]}", template="plotly_white")
            return json.loads(fig.to_json())
        elif len(columns) > 2:
            fig = go.Figure()
            for col in columns[1:]:
                try:
                    pd.to_numeric(df[col])
                    fig.add_trace(go.Scatter(x=df[columns[0]], y=df[col], mode='lines', name=col))
                except:
                    pass
            fig.update_layout(title="Trend Chart", template="plotly_white")
            return json.loads(fig.to_json())
        return None
    except Exception as e:
        logger.warning(f"Chart generation failed: {e}")
        return None

def extract_message_from_components(components) -> str:
    """Extract text message from components"""
    messages = []
    
    for component in components:
        try:
            if hasattr(component, 'simple_component') and component.simple_component:
                simple = component.simple_component
                if hasattr(simple, 'text') and simple.text:
                    messages.append(simple.text)
            
            if hasattr(component, 'rich_component') and component.rich_component:
                rich = component.rich_component
                
                if hasattr(rich, 'content') and rich.content:
                    messages.append(rich.content)
                
                if hasattr(rich, 'text') and rich.text:
                    messages.append(rich.text)
        except:
            pass
    
    final_message = " ".join(dict.fromkeys(messages))
    return final_message.strip() if final_message else "Query processed"

# ==================== MAIN ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "name": "Clinic NL2SQL API",
        "version": "1.0.0",
        "endpoints": {"chat": "POST /chat", "health": "GET /health", "status": "GET /status"}
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat endpoint - Main interaction"""
    
    logger.info(f"📨 Question: {request.question}")
    
    # Validate input
    if not request.question or len(request.question) > 500:
        return ChatResponse(
            message="Invalid input",
            error="Question must be 1-500 characters"
        )
    
    try:
        # Get agent
        agent = get_agent()
        request_context = RequestContext()
        
        logger.info("Processing with Vanna agent...")
        
        # Send message and collect components
        response_stream = agent.send_message(
            message=request.question,
            request_context=request_context
        )
        
        components = []
        async for component in response_stream:
            components.append(component)
        
        logger.info(f"Received {len(components)} components")
        
        # Extract message from components
        message = extract_message_from_components(components)
        logger.info(f"Message: {message[:100]}")
        
        # Extract SQL from message (markdown code blocks)
        sql_query = extract_sql_from_markdown(message)
        
        if sql_query:
            logger.info(f"✓ Extracted SQL: {sql_query[:80]}")
        else:
            logger.info("No SQL found in message")
        
        # Execute SQL if we have it
        columns = None
        rows = None
        error_msg = None
        
        if sql_query:
            logger.info("Executing SQL query...")
            success, columns, rows, exec_error = execute_sql_query(sql_query)
            
            if not success:
                error_msg = exec_error
                logger.error(f"SQL execution failed: {exec_error}")
            else:
                logger.info(f"✓ SQL executed: {len(rows) if rows else 0} rows")
        
        # Generate chart if we have data
        chart_data = None
        chart_type = None
        if rows and columns and len(rows) > 0:
            chart_data = generate_chart(columns, rows)
            if chart_data:
                chart_type = "bar" if len(columns) == 2 else "line"
                logger.info(f"📊 Chart generated: {chart_type}")
        
        return ChatResponse(
            message=message,
            sql_query=sql_query,
            columns=columns,
            rows=rows,
            row_count=len(rows) if rows else 0,
            chart=chart_data,
            chart_type=chart_type,
            error=error_msg
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return ChatResponse(
            message="Error processing question",
            error=str(e)
        )

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check"""
    try:
        db_ok = check_database_connection()
        agent = get_agent()
        memory = get_memory_count(agent)
        
        return HealthResponse(
            status="ok" if db_ok else "degraded",
            database="connected" if db_ok else "disconnected",
            agent_memory_items=memory,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health error: {e}")
        return HealthResponse(
            status="error",
            database="unknown",
            agent_memory_items=0,
            timestamp=datetime.now().isoformat()
        )

@app.get("/status")
async def status():
    """Status endpoint"""
    try:
        return {
            "timestamp": datetime.now().isoformat(),
            "database": {"path": DB_PATH, "connected": check_database_connection()},
            "agent": {"memory_items": get_memory_count(get_agent())},
            "api": {"version": "1.0.0"}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": str(exc)})

# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 70)
    logger.info("🚀 Starting Clinic NL2SQL API")
    logger.info("=" * 70)
    try:
        if check_database_connection():
            logger.info("✓ Database connected")
        agent = get_agent()
        memory = get_memory_count(agent)
        logger.info(f"✓ Agent ready with {memory} memory items")
        logger.info("✅ API Ready!")
        logger.info("=" * 70)
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down...")

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")

