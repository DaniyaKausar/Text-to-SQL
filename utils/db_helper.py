import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "data/company.db"


def get_schema() -> str:
    """Returns database schema as readable string for LLM prompt"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = cursor.fetchall()

        if not tables:
            return "No tables found in database."

        schema_parts = []
        for (table_name,) in tables:
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Get row count for context
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            col_defs = []
            for col in columns:
                _, col_name, col_type, not_null, default, is_pk = col
                pk_marker   = " PRIMARY KEY" if is_pk else ""
                null_marker = " NOT NULL" if not_null else ""
                col_defs.append(f"  {col_name} {col_type}{pk_marker}{null_marker}")

            schema_parts.append(
                f"Table: {table_name} ({row_count} rows)\n" +
                "\n".join(col_defs)
            )

        conn.close()
        return "\n\n".join(schema_parts)

    except sqlite3.Error as e:
        raise Exception(f"Could not read database schema: {str(e)}")


def run_query(sql: str) -> pd.DataFrame:
    """
    Executes SQL and returns DataFrame.
    Raises descriptive exceptions on failure.
    """
    if not sql or not sql.strip():
        raise ValueError("Cannot execute empty SQL query.")

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()

        # Warn if result is very large
        if len(df) > 500:
            df = df.head(500)  # Safety cap

        return df

    except pd.io.sql.DatabaseError as e:
        error_msg = str(e)
        # Give user-friendly error messages
        if "no such table" in error_msg.lower():
            table = error_msg.split("no such table:")[-1].strip()
            raise Exception(f"Table '{table}' doesn't exist in the database.")
        elif "no such column" in error_msg.lower():
            col = error_msg.split("no such column:")[-1].strip()
            raise Exception(f"Column '{col}' doesn't exist.")
        else:
            raise Exception(f"Query failed: {error_msg}")

    except sqlite3.Error as e:
        raise Exception(f"Database connection error: {str(e)}")


def get_table_names() -> list:
    """Returns list of user-created table names (skips sqlite internal tables)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [
            row[0] for row in cursor.fetchall()
            if not row[0].startswith('sqlite_')
        ]
        conn.close()
        return tables
    except Exception:
        return []


def get_sample_rows(table_name: str, limit: int = 3) -> pd.DataFrame:
    """Returns sample rows for Schema Viewer"""
    try:
        # Validate table name (prevent injection via table name)
        allowed_tables = get_table_names()
        if table_name not in allowed_tables:
            return pd.DataFrame()

        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT {limit}", conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


def save_query_to_history(
    question: str,
    sql: str,
    success: bool,
    row_count: int,
    response_time: float
):
    """
    Saves query history to a persistent SQLite table.
    This is separate from session state — survives app restarts!
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create history table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                question      TEXT NOT NULL,
                sql_generated TEXT NOT NULL,
                success       INTEGER NOT NULL,
                row_count     INTEGER DEFAULT 0,
                response_time REAL DEFAULT 0,
                timestamp     TEXT NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO query_history
                (question, sql_generated, success, row_count, response_time, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            question,
            sql,
            1 if success else 0,
            row_count,
            round(response_time, 3),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()
        conn.close()
    except Exception:
        pass  # History saving should never crash the main app


def get_persistent_history(limit: int = 20) -> pd.DataFrame:
    """Fetches query history from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"""SELECT question, sql_generated, success,
                       row_count, response_time, timestamp
                FROM query_history
                ORDER BY id DESC
                LIMIT {limit}""",
            conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()