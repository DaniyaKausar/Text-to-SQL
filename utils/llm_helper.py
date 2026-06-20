"""
LLM Helper — Now with:
1. Schema RAG (only relevant tables in prompt)
2. Self-correction loop (auto-fix failed SQL)
3. sqlglot validation
"""

from groq import Groq
import os
from dotenv import load_dotenv
from utils.guardrails import clean_sql

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file.")

client = Groq(api_key=api_key)
MODEL  = "llama-3.3-70b-versatile"


def generate_sql(user_question: str, schema: str) -> str:
    """
    Now uses RAG schema instead of full schema.
    schema parameter comes from schema_rag.get_relevant_schema()
    """
    prompt = f"""You are an expert SQLite SQL developer.

DATABASE SCHEMA (only relevant tables shown):
{schema}

RULES:
1. Only SELECT statements
2. Use EXACT column/table names from schema above
3. Dates stored as TEXT 'YYYY-MM-DD'
4. Add LIMIT 100 if not specified
5. Return ONLY raw SQL — no markdown, no backticks
6. For multi-table questions, use proper JOINs
7. If unanswerable, return: CANNOT_ANSWER

QUESTION: {user_question}
SQL:"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=300,
    )
    return clean_sql(response.choices[0].message.content.strip())


def generate_sql_with_correction(
    user_question: str,
    schema: str
) -> tuple:
    """
    ENTERPRISE FUNCTION:
    1. Generate SQL
    2. Validate with sqlglot
    3. Test in sandbox
    4. If fails → self-correct
    
    Returns: (sql, was_corrected, correction_attempts, error)
    """
    from utils.sql_validator import (
        parse_and_validate,
        sandbox_execute,
        self_correct_sql
    )

    # Step 1: Generate
    try:
        generated = generate_sql(user_question, schema)
    except Exception as e:
        return None, False, 0, str(e)

    if "CANNOT_ANSWER" in generated.upper():
        return "CANNOT_ANSWER", False, 0, None

    # Step 2: sqlglot parse
    is_valid, parse_error, clean = parse_and_validate(generated)
    if not is_valid:
        # Try self-correction immediately
        fixed, corrected, attempts = self_correct_sql(
            generated, parse_error,
            user_question, schema,
            client, MODEL
        )
        return fixed, corrected, attempts, parse_error

    # Step 3: Sandbox test
    success, exec_error, _ = sandbox_execute(clean)
    if not success:
        # Self-correct execution error
        fixed, corrected, attempts = self_correct_sql(
            clean, exec_error,
            user_question, schema,
            client, MODEL
        )
        return fixed, corrected, attempts, exec_error

    return clean, False, 1, None


def generate_explanation(sql: str, user_question: str) -> str:
    prompt = f"""User asked: "{user_question}"
SQL: {sql}
Explain in 2 simple sentences. No jargon."""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=120,
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return "Explanation not available."


def generate_summary(user_question: str, results: str) -> str:
    prompt = f"""User asked: "{user_question}"
Data: {results}
One sentence business insight with specific numbers."""
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=100,
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return "Summary not available."