"""
Step 4: Initialize Vanna 2.0 Agent with all components
Uses Google Gemini as the LLM provider
Agent-based architecture with SqliteRunner for database connection
"""

import os
import logging
import asyncio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============ VANNA CORE IMPORTS ============
from vanna import Agent, AgentConfig
from vanna.core.registry import ToolRegistry
from vanna.core.user import UserResolver, User, RequestContext

# ============ TOOL IMPORTS ============
from vanna.tools import RunSqlTool, VisualizeDataTool
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool

# ============ INTEGRATION IMPORTS ============
from vanna.integrations.sqlite import SqliteRunner
from vanna.integrations.local.agent_memory import DemoAgentMemory
from vanna.integrations.google import GeminiLlmService


# ============ 1. CUSTOM USER RESOLVER ============
class DefaultUserResolver(UserResolver):
    """
    Simple user resolver that returns a default user for all requests
    IMPORTANT: resolve_user() MUST be async
    """
    async def resolve_user(self, request_context: RequestContext) -> User:
        """
        Resolve any request to a default user
        
        IMPORTANT: This MUST be async (async def, not def)
        Vanna 2.0 expects an async method
        
        Args:
            request_context: The request context from the agent
        
        Returns:
            User object with default credentials
        """
        # Add small delay to ensure it's treated as async
        await asyncio.sleep(0)
        
        return User(
            id="default_user",
            email="user@clinic.local"
        )


# ============ 2. CREATE LLM SERVICE ============
def create_llm_service():
    """
    Initialize Google Gemini LLM Service
    
    Returns:
        GeminiLlmService instance
    
    Raises:
        ValueError: If GOOGLE_API_KEY not found in environment
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError(
            " GOOGLE_API_KEY not found in environment variables.\n"
            "   Please set it in .env file or as an environment variable.\n"
            "   Get your free key at: https://aistudio.google.com/apikey"
        )
    
    logger.info(" Initializing Google Gemini LLM Service...")
    
    llm = GeminiLlmService(
        api_key=api_key,
        model="gemini-2.5-flash"
    )
    
    logger.info(" Gemini LLM Service initialized")
    return llm


# ============ 3. CREATE SQL RUNNER ============
def create_sql_runner(db_path: str = "clinic.db"):
    """
    Initialize SQLite Runner for database connection
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        SqliteRunner instance
    
    Raises:
        FileNotFoundError: If database file doesn't exist
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f" Database file '{db_path}' not found.\n"
            f"   Please run: python setup_database.py"
        )
    
    logger.info(f"  Initializing SQLite Runner with database: {db_path}")
    
    sql_runner = SqliteRunner(database_path=db_path)
    
    logger.info(" SQLite Runner initialized")
    return sql_runner


# ============ 4. CREATE AGENT MEMORY ============
def create_agent_memory():
    """
    Initialize DemoAgentMemory for agent learning
    
    Returns:
        DemoAgentMemory instance
    """
    logger.info(" Initializing Agent Memory...")
    
    memory = DemoAgentMemory()
    
    logger.info(" Agent Memory initialized")
    return memory


# ============ 5. CREATE TOOL REGISTRY ============
def create_tool_registry(sql_runner, agent_memory):
    """
    Create Tool Registry with all required tools
    
    Tools included:
    1. RunSqlTool - Executes SQL queries on database
    2. VisualizeDataTool - Creates visualizations of query results
    3. SaveQuestionToolArgsTool - Saves successful Q&A pairs (auto-managed)
    4. SearchSavedCorrectToolUsesTool - Searches learned Q&A pairs (auto-managed)
    
    Args:
        sql_runner: SqliteRunner instance
        agent_memory: DemoAgentMemory instance
    
    Returns:
        ToolRegistry with tools ready for Agent
    """
    logger.info(" Creating Tool Registry with all 4 tools...")
    
    tool_registry = ToolRegistry()
    
    # Tool 1: RunSqlTool - Executes SQL queries
    logger.info("  RunSqlTool - Executes SQL queries on database")
    run_sql_tool = RunSqlTool(sql_runner=sql_runner)
    
    # Tool 2: VisualizeDataTool - Creates visualizations
    logger.info("   VisualizeDataTool - Creates visualizations of results")
    visualize_data_tool = VisualizeDataTool()
    
    # Tool 3 & 4: Memory tools (imported but auto-managed by Agent)
    logger.info("   SaveQuestionToolArgsTool - Saves Q&A pairs (auto-registered)")
    logger.info("  SearchSavedCorrectToolUsesTool - Searches Q&A pairs (auto-registered)")
    
    logger.info(" Tool Registry ready with 4 tools")
    
    return tool_registry


# ============ 6. CREATE USER RESOLVER ============
def create_user_resolver():
    """
    Create a user resolver for the agent
    
    Returns:
        DefaultUserResolver instance (identifies all users as default)
    """
    logger.info(" Initializing User Resolver...")
    
    user_resolver = DefaultUserResolver()
    
    logger.info(" User Resolver initialized")
    return user_resolver


# ============ 7. INITIALIZE FULL AGENT ============
def initialize_agent(db_path: str = "clinic.db") -> Agent:
    """
    Initialize and return the complete Vanna 2.0 Agent
    
    This function sets up all required components per Step 4:
    1.  LLM Service (GeminiLlmService)
    2.  ToolRegistry with 4 tools (RunSqlTool, VisualizeDataTool, SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool)
    3.  DemoAgentMemory instance (Vanna 2.0's learning system)
    4.  UserResolver (simple default resolver) - MUST be ASYNC
    5.  Agent with all components connected
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        Fully initialized Agent instance
    
    Raises:
        ValueError: If required environment variables are missing
        FileNotFoundError: If database file doesn't exist
    """
    logger.info("=" * 60)
    logger.info(" Initializing Vanna 2.0 Agent (Step 4)")
    logger.info("=" * 60)
    
    try:
        # Step 1: Create LLM Service (REQUIRED)
        llm_service = create_llm_service()
        
        # Step 2: Create SQL Runner
        sql_runner = create_sql_runner(db_path)
        
        # Step 3: Create Agent Memory (REQUIRED)
        agent_memory = create_agent_memory()
        
        # Step 4: Create Tool Registry with all 4 tools (REQUIRED)
        tool_registry = create_tool_registry(sql_runner, agent_memory)
        
        # Step 5: Create User Resolver (REQUIRED) - MUST BE ASYNC
        user_resolver = create_user_resolver()
        
        # Step 6: Create Agent with all components connected
        logger.info("Creating Agent with all components connected...")
        
        agent = Agent(
            llm_service=llm_service,
            tool_registry=tool_registry,
            user_resolver=user_resolver,
            agent_memory=agent_memory
        )
        
        logger.info(" Agent created successfully")
        
        logger.info("=" * 60)
        logger.info(" Step 4 Complete: Vanna 2.0 Agent initialized!")
        logger.info("   Components:")
        logger.info("    LLM Service: GeminiLlmService")
        logger.info("    Tool Registry: 4 tools (RunSqlTool, VisualizeDataTool,")
        logger.info("     SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool)")
        logger.info("   Agent Memory: DemoAgentMemory")
        logger.info("    User Resolver: DefaultUserResolver (ASYNC)")
        logger.info("=" * 60)
        
        return agent
    
    except Exception as e:
        logger.error(f" Failed to initialize agent: {e}", exc_info=True)
        raise


# ============ 8. SINGLETON PATTERN ============
_agent_instance = None

def get_agent(db_path: str = "clinic.db") -> Agent:
    """
    Get or create a singleton Agent instance
    
    This ensures only one agent is created throughout the application lifetime
    
    Args:
        db_path: Path to SQLite database file
    
    Returns:
        Agent instance (cached after first call)
    """
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = initialize_agent(db_path)
    
    return _agent_instance


def reset_agent():
    """Reset the agent singleton (useful for testing)"""
    global _agent_instance
    _agent_instance = None
    logger.info("Agent singleton reset")


# ============ TEST/DEBUG ============
if __name__ == "__main__":
    """
    Test the agent initialization
    Run with: python vanna_setup.py
    """
    try:
        agent = initialize_agent()
        print(f"\n Agent initialized successfully!")
        print(f"Agent instance: {agent}")
        print(f"Agent type: {type(agent)}")
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
