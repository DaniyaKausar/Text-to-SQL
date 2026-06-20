import re
import sqlite3

DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT",
    "ALTER", "TRUNCATE", "CREATE", "REPLACE",
    "ATTACH", "DETACH", "PRAGMA",
]

def is_safe_sql(sql: str) -> tuple:
    """
    Multi-layer SQL safety check.
    Returns (True, "") if safe
    Returns (False, reason) if dangerous
    """
    if not sql or not sql.strip():
        return False, "Empty SQL query received."

    sql_upper = sql.upper().strip()

    # Rule 1: Must start with SELECT
    if not sql_upper.startswith("SELECT"):
        return False, "Only SELECT queries allowed. Query must start with SELECT."

    # Rule 2: Dangerous keywords check
    for keyword in DANGEROUS_KEYWORDS:
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Dangerous keyword detected: '{keyword}'. Not allowed."

    # Rule 3: No multiple statements (SQL injection prevention)
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    if len(statements) > 1:
        return False, "Multiple SQL statements not allowed."

    # Rule 4: No comments (can hide malicious code)
    if '--' in sql or '/*' in sql:
        return False, "SQL comments are not allowed."

    # Rule 5: Reasonable length check
    if len(sql) > 2000:
        return False, "Query too long. Please simplify your question."

    return True, ""


def validate_sql_syntax(sql: str, db_path: str = "data/company.db") -> tuple:
    """
    Actually tries to parse the SQL without executing it.
    SQLite's EXPLAIN just validates syntax — it doesn't run the query.
    Returns (True, "") if valid syntax
    Returns (False, error_message) if invalid
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # EXPLAIN parses SQL without executing — perfect for validation
        cursor.execute(f"EXPLAIN {sql}")
        conn.close()
        return True, ""
    except sqlite3.Error as e:
        return False, f"SQL syntax error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def clean_sql(sql: str) -> str:
    """
    Cleans SQL returned by LLM.
    Removes markdown, extra whitespace, backticks.
    """
    # Remove markdown code blocks
    sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'```\s*', '', sql)

    # Remove backtick wrapping (some models do this)
    sql = sql.replace('`', '')

    # Remove leading/trailing whitespace
    sql = sql.strip()

    # Remove trailing semicolon
    sql = sql.rstrip(';').strip()

    return sql


def get_query_type(sql: str) -> str:
    """Returns the type of SQL query for logging purposes"""
    sql_upper = sql.upper().strip()
    if sql_upper.startswith("SELECT"):
        if "JOIN" in sql_upper:
            return "SELECT_JOIN"
        elif "GROUP BY" in sql_upper:
            return "SELECT_AGGREGATE"
        else:
            return "SELECT_SIMPLE"
    return "UNKNOWN"