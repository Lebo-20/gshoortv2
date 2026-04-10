import os
import asyncpg
import logging
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

logger = logging.getLogger(__name__)

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute('''
        CREATE TABLE IF NOT EXISTS queue (
            id SERIAL PRIMARY KEY,
            user_id TEXT,
            file_id TEXT UNIQUE,
            file_name TEXT,
            order_num INT
        );
        ''')
        await conn.close()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to intialize database: {e}")

async def add_to_queue(user_id, file_id, file_name):
    """
    Returns True if added successfully, False if duplicate.
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Calculate order_num. We can just count the current rows and add 1.
        # Alternatively, get max order_num.
        order_row = await conn.fetchrow('SELECT COALESCE(MAX(order_num), 0) + 1 as next_order FROM queue')
        next_order_num = order_row['next_order']
        
        query = '''
        INSERT INTO queue (user_id, file_id, file_name, order_num)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (file_id) DO NOTHING
        RETURNING id;
        '''
        row = await conn.fetchrow(query, str(user_id), str(file_id), str(file_name), next_order_num)
        await conn.close()
        
        return row is not None # True if inserted, False if conflicted (duplicate)
    except Exception as e:
        logger.error(f"Error adding to queue: {e}")
        return False
