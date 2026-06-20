"""
Retry script — sirf failed questions run karo
Questions 1-6 (HuggingFace download issue) 
Questions 49-50 (API rate limit)
"""

import time
import json
from eval_dataset import EVAL_DATASET
from utils.schema_rag import get_relevant_schema
from utils.llm_helper import generate_sql_with_correction
from utils.guardrails import is_safe_sql
from utils.db_helper import run_query
from datetime import datetime

# Sirf yeh IDs retry karo
RETRY_IDS = [1, 2, 3, 4, 5, 6, 49, 50]

def run_single_eval(item):
    question = item["question"]
    print(f"\n[{item['id']:02d}] {question[:55]}...")

    start_time = time.time()

    try:
        schema = get_relevant_schema(question)
        generated_sql, was_corrected, attempts, error = \
            generate_sql_with_correction(question, schema)

        if generated_sql is None:
            raise Exception(error or "Generation failed")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Failed: {str(e)[:60]}")
        return {
            "id": item["id"],
            "question": question,
            "category": item["category"],
            "complexity": item["complexity"],
            "generated_sql": None,
            "execution_success": False,
            "keyword_score": 0.0,
            "table_score": 0.0,
            "was_corrected": False,
            "attempts": 0,
            "response_time": elapsed,
            "row_count": 0,
            "error": str(e),
            "status": "GENERATION_FAILED"
        }

    elapsed = time.time() - start_time

    # CANNOT_ANSWER check
    is_cannot = "CANNOT_ANSWER" in generated_sql.upper()
    expected_cannot = "CANNOT_ANSWER" in [
        k.upper() for k in item["expected_keywords"]
    ]

    if is_cannot and expected_cannot:
        print(f"   ✅ Correctly refused ({elapsed:.2f}s)")
        return {
            "id": item["id"],
            "question": question,
            "category": item["category"],
            "complexity": item["complexity"],
            "generated_sql": generated_sql,
            "execution_success": True,
            "keyword_score": 1.0,
            "table_score": 1.0,
            "was_corrected": was_corrected,
            "attempts": attempts,
            "response_time": elapsed,
            "row_count": 0,
            "error": None,
            "status": "CORRECTLY_REFUSED"
        }

    # Safety check
    is_safe, reason = is_safe_sql(generated_sql)
    if not is_safe:
        # Security question blocked = correct behavior!
        if item["category"] == "security":
            print(f"   ✅ Correctly blocked by guardrails ({elapsed:.2f}s)")
            return {
                "id": item["id"],
                "question": question,
                "category": item["category"],
                "complexity": item["complexity"],
                "generated_sql": generated_sql,
                "execution_success": True,
                "keyword_score": 1.0,
                "table_score": 1.0,
                "was_corrected": False,
                "attempts": 0,
                "response_time": elapsed,
                "row_count": 0,
                "error": None,
                "status": "CORRECTLY_BLOCKED"
            }

    # Keyword accuracy
    sql_upper = generated_sql.upper()
    matched = [
        kw for kw in item["expected_keywords"]
        if kw.upper() in sql_upper
    ]
    kw_score = len(matched) / len(item["expected_keywords"]) \
        if item["expected_keywords"] else 1.0

    # Table coverage
    sql_lower = generated_sql.lower()
    covered = sum(
        1 for t in item["expected_tables"] if t in sql_lower
    )
    table_score = covered / len(item["expected_tables"]) \
        if item["expected_tables"] else 1.0

    # Execute
    try:
        df = run_query(generated_sql)
        print(f"   ✅ OK | {len(df)} rows | {elapsed:.2f}s | kw:{kw_score:.0%}")
        return {
            "id": item["id"],
            "question": question,
            "category": item["category"],
            "complexity": item["complexity"],
            "generated_sql": generated_sql,
            "execution_success": True,
            "keyword_score": kw_score,
            "table_score": table_score,
            "was_corrected": was_corrected,
            "attempts": attempts,
            "response_time": elapsed,
            "row_count": len(df),
            "error": None,
            "status": "SUCCESS"
        }
    except Exception as e:
        print(f"   ❌ Exec failed: {str(e)[:50]}")
        return {
            "id": item["id"],
            "question": question,
            "category": item["category"],
            "complexity": item["complexity"],
            "generated_sql": generated_sql,
            "execution_success": False,
            "keyword_score": kw_score,
            "table_score": table_score,
            "was_corrected": was_corrected,
            "attempts": attempts,
            "response_time": elapsed,
            "row_count": 0,
            "error": str(e),
            "status": "EXECUTION_FAILED"
        }


if __name__ == "__main__":
    print("🔄 Retrying failed questions...")
    print(f"   IDs: {RETRY_IDS}\n")

    # Load existing results
    with open("evaluation_results.json", "r") as f:
        existing = json.load(f)

    existing_results = existing["detailed_results"]

    # Run only failed ones
    retry_items = [
        item for item in EVAL_DATASET
        if item["id"] in RETRY_IDS
    ]

    new_results = {}
    for item in retry_items:
        # Wait longer between calls to avoid rate limit
        time.sleep(3)
        result = run_single_eval(item)
        new_results[item["id"]] = result

    # Merge with existing results
    merged = []
    for r in existing_results:
        if r["id"] in new_results:
            merged.append(new_results[r["id"]])
        else:
            merged.append(r)

    # Recalculate metrics
    total   = len(merged)
    success = [r for r in merged if r["execution_success"]]
    exec_rate    = len(success) / total * 100
    avg_kw       = sum(r["keyword_score"] for r in merged) / total * 100
    avg_table    = sum(r["table_score"]   for r in merged) / total * 100
    times        = [r["response_time"] for r in merged]
    avg_time     = sum(times) / len(times) * 1000
    corrected    = [r for r in merged if r["was_corrected"]]
    corr_rate    = len(corrected) / total * 100

    # By complexity
    def acc_by(key, val):
        items = [r for r in merged if r[key] == val]
        if not items:
            return 0
        return sum(r["execution_success"] for r in items) / len(items) * 100

    failed = [r for r in merged if not r["execution_success"]]

    print("\n" + "="*60)
    print("   FINAL EVALUATION REPORT (After Retry)")
    print("="*60)
    print(f"""
📊 OVERALL METRICS
──────────────────
Total Questions       : {total}
Execution Success     : {exec_rate:.1f}%
Keyword Accuracy      : {avg_kw:.1f}%
Table Coverage        : {avg_table:.1f}%

⚡ PERFORMANCE  
──────────────
Avg Response Time     : {avg_time:.0f} ms

🔧 SELF-CORRECTION
──────────────────
Auto-corrected        : {corr_rate:.1f}% of queries

📈 BY COMPLEXITY
──────────────────
Simple queries        : {acc_by('complexity','simple'):.1f}%
Medium queries        : {acc_by('complexity','medium'):.1f}%
Hard (JOIN) queries   : {acc_by('complexity','hard'):.1f}%

❌ Still Failed       : {len(failed)}
Failed IDs            : {[r['id'] for r in failed]}
""")

    print("📝 RESUME-READY NUMBERS:")
    print(f"""
• Benchmarked on custom 50-question evaluation dataset
• Overall SQL Execution Accuracy  : {exec_rate:.1f}%
• Keyword Structural Accuracy     : {avg_kw:.1f}%  
• Complex JOIN Query Accuracy     : {acc_by('complexity','hard'):.1f}%
• Average Response Time           : {avg_time:.0f}ms
• Self-Correction Rate            : {corr_rate:.1f}%
""")
    print("="*60)

    # Save updated results
    existing["detailed_results"] = merged
    existing["metrics"]["execution_success_rate"] = round(exec_rate, 1)
    existing["metrics"]["keyword_accuracy"]        = round(avg_kw, 1)
    existing["metadata"]["retry_timestamp"]        = datetime.now().isoformat()

    with open("evaluation_results.json", "w") as f:
        json.dump(existing, f, indent=2)

    print("\n✅ Updated results saved to evaluation_results.json")