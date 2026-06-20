"""
Evaluation Runner
=================
Yeh script 50 questions run karke real metrics calculate karta hai.
Resume ke liye honest numbers generate karta hai.

Run: python run_evaluation.py
"""

import time
import json
import sqlite3
from datetime import datetime
from eval_dataset import EVAL_DATASET

# Import project modules
from utils.schema_rag import get_relevant_schema
from utils.llm_helper import generate_sql_with_correction
from utils.guardrails import is_safe_sql, clean_sql
from utils.db_helper import run_query


# ── METRICS STORAGE ───────────────────────────────────────────────
results = []


def check_sql_accuracy(generated_sql: str, expected_keywords: list) -> tuple:
    """
    Checks if generated SQL contains expected keywords.
    Returns (score, matched, missed)
    
    Not perfect but honest — checks structural correctness.
    """
    if not generated_sql:
        return 0.0, [], expected_keywords

    sql_upper = generated_sql.upper()

    matched = []
    missed  = []

    for kw in expected_keywords:
        if kw.upper() in sql_upper:
            matched.append(kw)
        else:
            missed.append(kw)

    score = len(matched) / len(expected_keywords) if expected_keywords else 0
    return score, matched, missed


def check_table_coverage(generated_sql: str, expected_tables: list) -> float:
    """Checks if correct tables are referenced in SQL"""
    if not expected_tables:
        return 1.0  # Out-of-scope questions — no tables expected

    sql_lower = generated_sql.lower()
    covered   = sum(1 for t in expected_tables if t in sql_lower)
    return covered / len(expected_tables)


def run_single_eval(item: dict) -> dict:
    """Runs one evaluation question and returns detailed result"""

    question   = item["question"]
    category   = item["category"]
    complexity = item["complexity"]

    print(f"\n[{item['id']:02d}/50] {question[:55]}...")

    start_time = time.time()

    # ── Generate SQL ──────────────────────────────────────────────
    try:
        schema = get_relevant_schema(question)
        generated_sql, was_corrected, attempts, error = \
            generate_sql_with_correction(question, schema)

        if generated_sql is None:
            raise Exception(error or "Generation failed")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Generation failed: {str(e)[:50]}")
        return {
            "id":            item["id"],
            "question":      question,
            "category":      category,
            "complexity":    complexity,
            "generated_sql": None,
            "execution_success": False,
            "keyword_score": 0.0,
            "table_score":   0.0,
            "was_corrected": False,
            "attempts":      0,
            "response_time": elapsed,
            "row_count":     0,
            "error":         str(e),
            "status":        "GENERATION_FAILED"
        }

    elapsed = time.time() - start_time

    # ── Out of scope / Security check ────────────────────────────
    is_cannot = "CANNOT_ANSWER" in generated_sql.upper()
    expected_cannot = "CANNOT_ANSWER" in [
        k.upper() for k in item["expected_keywords"]
    ]

    if is_cannot and expected_cannot:
        print(f"   ✅ Correctly refused ({elapsed:.2f}s)")
        return {
            "id":            item["id"],
            "question":      question,
            "category":      category,
            "complexity":    complexity,
            "generated_sql": generated_sql,
            "execution_success": True,
            "keyword_score": 1.0,
            "table_score":   1.0,
            "was_corrected": was_corrected,
            "attempts":      attempts,
            "response_time": elapsed,
            "row_count":     0,
            "error":         None,
            "status":        "CORRECTLY_REFUSED"
        }

    # ── Safety check ──────────────────────────────────────────────
    is_safe, reason = is_safe_sql(generated_sql)
    if not is_safe:
        print(f"   🚫 Blocked by guardrails")
        return {
            "id":            item["id"],
            "question":      question,
            "category":      category,
            "complexity":    complexity,
            "generated_sql": generated_sql,
            "execution_success": False,
            "keyword_score": 0.0,
            "table_score":   0.0,
            "was_corrected": was_corrected,
            "attempts":      attempts,
            "response_time": elapsed,
            "row_count":     0,
            "error":         reason,
            "status":        "BLOCKED_BY_GUARDRAIL"
        }

    # ── Keyword accuracy ──────────────────────────────────────────
    kw_score, matched, missed = check_sql_accuracy(
        generated_sql, item["expected_keywords"]
    )
    table_score = check_table_coverage(
        generated_sql, item["expected_tables"]
    )

    # ── Execute SQL ───────────────────────────────────────────────
    try:
        df        = run_query(generated_sql)
        exec_ok   = True
        row_count = len(df)
        status    = "SUCCESS"
        print(
            f"   ✅ OK | {row_count} rows | "
            f"{elapsed:.2f}s | kw:{kw_score:.0%}"
        )
    except Exception as e:
        exec_ok   = False
        row_count = 0
        status    = "EXECUTION_FAILED"
        print(f"   ❌ Exec failed: {str(e)[:50]}")

    return {
        "id":                item["id"],
        "question":          question,
        "category":          category,
        "complexity":        complexity,
        "generated_sql":     generated_sql,
        "execution_success": exec_ok,
        "keyword_score":     kw_score,
        "table_score":       table_score,
        "was_corrected":     was_corrected,
        "attempts":          attempts,
        "response_time":     elapsed,
        "row_count":         row_count,
        "error":             None if exec_ok else "Execution failed",
        "status":            status,
    }


def calculate_final_metrics(results: list) -> dict:
    """Calculate all resume-worthy metrics"""

    total = len(results)

    # Execution success rate
    exec_success = [r for r in results if r["execution_success"]]
    exec_rate    = len(exec_success) / total * 100

    # Keyword accuracy (SQL structural correctness)
    avg_kw_score = sum(r["keyword_score"] for r in results) / total * 100

    # Table coverage
    avg_table_score = sum(r["table_score"] for r in results) / total * 100

    # Response time
    times    = [r["response_time"] for r in results]
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    # Self-correction stats
    corrected     = [r for r in results if r["was_corrected"]]
    correction_rate = len(corrected) / total * 100

    # By complexity
    simple_results = [r for r in results if r["complexity"] == "simple"]
    medium_results = [r for r in results if r["complexity"] == "medium"]
    hard_results   = [r for r in results if r["complexity"] == "hard"]

    simple_acc = (
        sum(r["execution_success"] for r in simple_results) /
        len(simple_results) * 100
    ) if simple_results else 0

    medium_acc = (
        sum(r["execution_success"] for r in medium_results) /
        len(medium_results) * 100
    ) if medium_results else 0

    hard_acc = (
        sum(r["execution_success"] for r in hard_results) /
        len(hard_results) * 100
    ) if hard_results else 0

    # By category
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["execution_success"])

    cat_accuracy = {
        cat: sum(vals) / len(vals) * 100
        for cat, vals in categories.items()
    }

    # Failed queries
    failed = [r for r in results if not r["execution_success"]]

    return {
        "total_questions":      total,
        "execution_success_rate": round(exec_rate, 1),
        "keyword_accuracy":     round(avg_kw_score, 1),
        "table_coverage":       round(avg_table_score, 1),
        "avg_response_time_ms": round(avg_time * 1000, 0),
        "min_response_time_ms": round(min_time * 1000, 0),
        "max_response_time_ms": round(max_time * 1000, 0),
        "self_correction_rate": round(correction_rate, 1),
        "accuracy_by_complexity": {
            "simple": round(simple_acc, 1),
            "medium": round(medium_acc, 1),
            "hard":   round(hard_acc, 1),
        },
        "accuracy_by_category": {
            k: round(v, 1) for k, v in cat_accuracy.items()
        },
        "failed_count":  len(failed),
        "failed_queries": [
            {"id": r["id"], "question": r["question"], "error": r["error"]}
            for r in failed
        ],
    }


def print_report(metrics: dict):
    """Pretty print the evaluation report"""

    print("\n")
    print("=" * 60)
    print("   TEXT-TO-SQL EVALUATION REPORT")
    print(f"   Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print(f"""
📊 OVERALL METRICS
──────────────────
Total Questions    : {metrics['total_questions']}
Execution Success  : {metrics['execution_success_rate']}%
Keyword Accuracy   : {metrics['keyword_accuracy']}%
Table Coverage     : {metrics['table_coverage']}%

⚡ PERFORMANCE
──────────────
Avg Response Time  : {metrics['avg_response_time_ms']:.0f} ms
Min Response Time  : {metrics['min_response_time_ms']:.0f} ms
Max Response Time  : {metrics['max_response_time_ms']:.0f} ms

🔧 SELF-CORRECTION
──────────────────
Auto-corrected     : {metrics['self_correction_rate']}% of queries

📈 BY COMPLEXITY
──────────────────
Simple queries     : {metrics['accuracy_by_complexity']['simple']}%
Medium queries     : {metrics['accuracy_by_complexity']['medium']}%
Hard queries       : {metrics['accuracy_by_complexity']['hard']}%

📁 BY CATEGORY
──────────────""")

    for cat, acc in metrics['accuracy_by_category'].items():
        print(f"  {cat:<20}: {acc}%")

    print(f"""
❌ FAILED QUERIES   : {metrics['failed_count']}
""")

    if metrics['failed_queries']:
        print("Failed question IDs:", [
            f["id"] for f in metrics['failed_queries']
        ])

    print("=" * 60)
    print("\n📝 RESUME-READY METRICS:")
    print(f"""
• Evaluated on {metrics['total_questions']}-question benchmark dataset
• SQL Execution Success Rate    : {metrics['execution_success_rate']}%
• Keyword Accuracy Score        : {metrics['keyword_accuracy']}%
• Average Response Time         : {metrics['avg_response_time_ms']:.0f}ms
• Self-Correction Success       : {metrics['self_correction_rate']}% queries auto-fixed
• Simple Query Accuracy         : {metrics['accuracy_by_complexity']['simple']}%
• Complex JOIN Query Accuracy   : {metrics['accuracy_by_complexity']['hard']}%
""")
    print("=" * 60)


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("🚀 Starting Text-to-SQL Evaluation")
    print(f"   Total questions: {len(EVAL_DATASET)}")
    print(f"   Started at: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)

    all_results = []

    for item in EVAL_DATASET:
        result = run_single_eval(item)
        all_results.append(result)
        # Small delay to avoid API rate limits
        time.sleep(0.5)

    # Calculate metrics
    metrics = calculate_final_metrics(all_results)

    # Print report
    print_report(metrics)

    # Save detailed results to JSON
    output = {
        "metadata": {
            "timestamp":       datetime.now().isoformat(),
            "total_questions": len(EVAL_DATASET),
            "model":           "llama3-8b-8192",
            "framework":       "Groq + RAG + Self-Correction",
        },
        "metrics":         metrics,
        "detailed_results": all_results,
    }

    with open("evaluation_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n✅ Results saved to: evaluation_results.json")
    print("   Use these numbers on your resume!")