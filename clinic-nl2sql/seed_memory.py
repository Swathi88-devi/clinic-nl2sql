"""
Step 5: Seed Agent Memory with Q&A Pairs
Alternative approach - directly add to memory store
"""

import logging
import asyncio
from vanna_setup import get_agent
from vanna.core.user import RequestContext

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ==================== Q&A PAIRS ====================

QA_PAIRS = [
    ("How many patients do we have?", "SELECT COUNT(*) as total_patients FROM patients"),
    ("List all doctors and their specializations", "SELECT name, specialization FROM doctors"),
    ("Show me all patients", "SELECT first_name, last_name, email, phone FROM patients LIMIT 100"),
    ("Get patient count by city", "SELECT city, COUNT(*) as count FROM patients GROUP BY city"),
    ("Show top 5 patients by spending", "SELECT p.first_name, p.last_name, SUM(i.total_amount) as total_spending FROM patients p LEFT JOIN invoices i ON p.id = i.patient_id GROUP BY p.id ORDER BY total_spending DESC LIMIT 5"),
    ("List all female patients", "SELECT first_name, last_name, email FROM patients WHERE gender = 'Female'"),
    ("Show all doctors", "SELECT name, specialization, department, phone FROM doctors"),
    ("How many doctors work in each department?", "SELECT department, COUNT(*) as doctor_count FROM doctors GROUP BY department"),
    ("List cardiologists", "SELECT name, department, phone FROM doctors WHERE specialization = 'Cardiology'"),
    ("Show all upcoming appointments", "SELECT a.appointment_date, p.first_name, p.last_name, d.name FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN doctors d ON a.doctor_id = d.id ORDER BY a.appointment_date DESC"),
    ("How many appointments per status?", "SELECT status, COUNT(*) as count FROM appointments GROUP BY status"),
    ("List completed appointments", "SELECT a.appointment_date, p.first_name, d.name FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN doctors d ON a.doctor_id = d.id WHERE a.status = 'Completed'"),
    ("Show total revenue", "SELECT SUM(total_amount) as total_revenue FROM invoices WHERE status = 'Paid'"),
    ("List unpaid invoices", "SELECT id, patient_id, invoice_date, total_amount FROM invoices WHERE status = 'Unpaid'"),
    ("Show outstanding balances", "SELECT patient_id, SUM(total_amount - paid_amount) as balance_due FROM invoices WHERE status = 'Unpaid' GROUP BY patient_id"),
    ("Calculate average treatment cost", "SELECT AVG(cost) as average_cost FROM treatments"),
    ("How many patients registered this month?", "SELECT COUNT(*) as new_patients FROM patients WHERE strftime('%Y-%m', registered_date) = strftime('%Y-%m', 'now')"),
    ("Show patient appointment history", "SELECT p.first_name, p.last_name, a.appointment_date, d.name, a.status FROM appointments a JOIN patients p ON a.patient_id = p.id JOIN doctors d ON a.doctor_id = d.id ORDER BY a.appointment_date DESC"),
]

# ==================== SEED FUNCTION ====================

async def seed_agent_memory():
    """Seed agent memory with Q&A pairs"""
    logger.info("=" * 70)
    logger.info("🌱 Seeding Agent Memory")
    logger.info("=" * 70 + "\n")
    
    try:
        agent = get_agent()
        request_context = RequestContext()
        
        logger.info(f"Attempting to add {len(QA_PAIRS)} Q&A pairs...\n")
        
        stored_count = 0
        
        for i, (question, sql) in enumerate(QA_PAIRS, 1):
            logger.info(f"{i}. Q: {question}")
            logger.info(f"   SQL: {sql[:70]}...")
            
            try:
                # Try different methods
                memory = agent.agent_memory
                
                # Method 1: Direct add_memory if available
                if hasattr(memory, 'add_memory'):
                    result = memory.add_memory(question, sql)
                    if asyncio.iscoroutine(result):
                        await result
                    logger.info("   ✓ Added via add_memory\n")
                    stored_count += 1
                
                # Method 2: store_question_and_sql
                elif hasattr(memory, 'store_question_and_sql'):
                    result = memory.store_question_and_sql(question, sql, request_context)
                    if asyncio.iscoroutine(result):
                        await result
                    logger.info("   ✓ Added via store_question_and_sql\n")
                    stored_count += 1
                
                # Method 3: Direct storage in internal list
                elif hasattr(memory, 'memories'):
                    memory.memories.append({"question": question, "sql": sql})
                    logger.info("   ✓ Added to memories list\n")
                    stored_count += 1
                
                else:
                    logger.warning("   ✗ No storage method found\n")
            
            except Exception as e:
                logger.warning(f"   ⚠️  Error: {str(e)[:60]}\n")
        
        logger.info("=" * 70)
        logger.info(f"✅ Seeding Complete - {stored_count} items added")
        logger.info("=" * 70 + "\n")
        
        # Verify
        try:
            memories = agent.agent_memory.get_recent_memories(context=request_context)
            if asyncio.iscoroutine(memories):
                memories = await memories
            
            if memories:
                logger.info(f"Verified: {len(memories)} memories in store")
            else:
                logger.info("Note: Memory verification returned empty (this may be normal)")
        except Exception as e:
            logger.info(f"Memory verification skipped: {e}")
    
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}", exc_info=True)

# ==================== MAIN ====================

if __name__ == "__main__":
    asyncio.run(seed_agent_memory())