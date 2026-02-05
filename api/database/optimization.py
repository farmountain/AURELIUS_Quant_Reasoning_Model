"""
Database optimization utilities
Includes index creation and query optimization helpers
"""
from sqlalchemy import text, Index
from database.session import engine
import logging

logger = logging.getLogger(__name__)


def create_performance_indexes():
    """Create database indexes for improved query performance"""
    indexes = [
        # Strategy indexes
        "CREATE INDEX IF NOT EXISTS idx_strategies_user_id ON strategies(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_strategies_created_at ON strategies(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies(name)",
        
        # Backtest indexes
        "CREATE INDEX IF NOT EXISTS idx_backtests_strategy_id ON backtests(strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_backtests_user_id ON backtests(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_backtests_created_at ON backtests(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_backtests_final_value ON backtests(final_value DESC)",
        
        # Validation indexes
        "CREATE INDEX IF NOT EXISTS idx_validations_strategy_id ON validations(strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_validations_created_at ON validations(created_at DESC)",
        
        # Gate indexes
        "CREATE INDEX IF NOT EXISTS idx_gates_strategy_id ON gates(strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_gates_gate_type ON gates(gate_type)",
        "CREATE INDEX IF NOT EXISTS idx_gates_passed ON gates(passed)",
        "CREATE INDEX IF NOT EXISTS idx_gates_created_at ON gates(created_at DESC)",
        
        # Reflexion indexes
        "CREATE INDEX IF NOT EXISTS idx_reflexion_strategy_id ON reflexion_history(strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_reflexion_created_at ON reflexion_history(created_at DESC)",
        
        # User indexes
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
        
        # Composite indexes for common queries
        "CREATE INDEX IF NOT EXISTS idx_backtests_strategy_created ON backtests(strategy_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_gates_strategy_type ON gates(strategy_id, gate_type)",
    ]
    
    try:
        with engine.connect() as conn:
            for index_sql in indexes:
                try:
                    conn.execute(text(index_sql))
                    logger.info(f"Created/verified index: {index_sql[:80]}...")
                except Exception as e:
                    logger.warning(f"Index creation skipped: {e}")
            
            conn.commit()
        logger.info("Database indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False


def analyze_tables():
    """Run ANALYZE on all tables to update statistics"""
    tables = [
        "users",
        "strategies", 
        "backtests",
        "validations",
        "gates",
        "reflexion_history",
    ]
    
    try:
        with engine.connect() as conn:
            for table in tables:
                conn.execute(text(f"ANALYZE {table}"))
                logger.info(f"Analyzed table: {table}")
            conn.commit()
        logger.info("Table analysis completed")
        return True
    except Exception as e:
        logger.error(f"Error analyzing tables: {e}")
        return False


def get_table_stats():
    """Get table size and row count statistics"""
    query = text("""
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
            pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
            n_tup_ins AS inserts,
            n_tup_upd AS updates,
            n_tup_del AS deletes
        FROM pg_stat_user_tables
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            stats = []
            for row in result:
                stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "indexes_size": row[4],
                    "inserts": row[5],
                    "updates": row[6],
                    "deletes": row[7],
                })
            return stats
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return []


def get_slow_queries():
    """Get slow query statistics (requires pg_stat_statements extension)"""
    query = text("""
        SELECT 
            query,
            calls,
            total_exec_time / 1000 AS total_time_seconds,
            mean_exec_time / 1000 AS mean_time_seconds,
            max_exec_time / 1000 AS max_time_seconds
        FROM pg_stat_statements
        WHERE query NOT LIKE '%pg_stat_statements%'
        ORDER BY total_exec_time DESC
        LIMIT 10
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(query)
            queries = []
            for row in result:
                queries.append({
                    "query": row[0][:200],  # Truncate long queries
                    "calls": row[1],
                    "total_time": round(row[2], 3),
                    "mean_time": round(row[3], 3),
                    "max_time": round(row[4], 3),
                })
            return queries
    except Exception as e:
        logger.warning(f"Could not get slow queries (pg_stat_statements may not be enabled): {e}")
        return []


def vacuum_tables():
    """Run VACUUM on all tables to reclaim space"""
    tables = [
        "users",
        "strategies",
        "backtests",
        "validations",
        "gates",
        "reflexion_history",
    ]
    
    try:
        # VACUUM cannot run inside a transaction block
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for table in tables:
                conn.execute(text(f"VACUUM ANALYZE {table}"))
                logger.info(f"Vacuumed table: {table}")
        logger.info("Table vacuum completed")
        return True
    except Exception as e:
        logger.error(f"Error vacuuming tables: {e}")
        return False
