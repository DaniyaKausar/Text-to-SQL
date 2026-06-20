import streamlit as st
import pandas as pd
import plotly.express as px
import time
import numpy as np
from datetime import datetime
from setup_db import setup
setup()

from utils.llm_helper import generate_sql_with_correction, generate_explanation, generate_summary
from utils.db_helper import (
    run_query, get_table_names, get_sample_rows,
    save_query_to_history, get_schema
)
from utils.guardrails import is_safe_sql, get_query_type
from utils.schema_rag import get_relevant_schema

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Text-to-SQL App",
    page_icon="🔍",
    layout="wide"
)

# ── CACHED FUNCTIONS ──────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cached_schema():
    return get_schema()

@st.cache_data(ttl=300)
def cached_table_names():
    return get_table_names()

@st.cache_data(ttl=300)
def cached_sample_rows(table_name: str):
    return get_sample_rows(table_name, limit=2)

# ── SESSION STATE ─────────────────────────────────────────────────────────────

# ✅ Pending question buffer — widget set hone se pehle inject karna padta hai
if "_pending_question" not in st.session_state:
    st.session_state["_pending_question"] = ""

# ✅ Transfer pending question BEFORE text_input widget is created
if st.session_state["_pending_question"]:
    st.session_state["input_question"] = st.session_state["_pending_question"]
    st.session_state["_pending_question"] = ""

defaults = {
    "input_question":           "",
    "run_query_flag":           False,
    "query_history":            [],
    "total_queries":            0,
    "successful_queries":       0,
    "total_response_time":      0.0,
    "last_sql":                 None,
    "last_results":             None,
    "last_question":            None,
    "last_query_type":          None,
    "last_elapsed":             None,
    "last_was_corrected":       False,
    "last_correction_attempts": 0,
    "conversation_history":     [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("📊 Analytics")

    total        = st.session_state.total_queries
    success      = st.session_state.successful_queries
    failed       = total - success
    avg_time     = st.session_state.total_response_time / total if total > 0 else 0
    success_rate = (success / total * 100) if total > 0 else 0

    c1, c2 = st.columns(2)
    c1.metric("Total",     total)
    c2.metric("✅ OK",     success)
    c3, c4 = st.columns(2)
    c3.metric("❌ Failed", failed)
    c4.metric("⚡ Avg",    f"{avg_time:.1f}s")

    if total > 0:
        st.progress(success_rate / 100,
                    text=f"Success: {success_rate:.0f}%")

    st.divider()

    st.header("🗄️ Schema")
    for table in cached_table_names():
        with st.expander(f"📋 {table}"):
            st.dataframe(cached_sample_rows(table),
                         use_container_width=True)

    st.divider()

    st.header("🧠 Conversation Memory")
    if st.session_state.conversation_history:
        for i, item in enumerate(
            st.session_state.conversation_history
        ):
            with st.expander(
                f"#{i+1} — {item['question'][:30]}..."
            ):
                st.code(item["sql"], language="sql")
                st.caption(
                    f"✅ {item['rows']} rows | "
                    f"⏱ {item['elapsed']:.2f}s | "
                    f"🕐 {item['timestamp']}"
                )
    else:
        st.info("No history yet.")

# ══════════════════════════════════════════════════════════════════════════════
# MAIN UI
# ══════════════════════════════════════════════════════════════════════════════
st.title("🔍 Text-to-SQL Assistant")
st.markdown("Plain English → SQL → Results | **Groq ⚡ Llama 3 + RAG + Self-Correction**")
st.divider()

# ── EXAMPLE BUTTONS ───────────────────────────────────────────────────────────
st.subheader("💡 Try these:")
examples = [
    "Show all employees in Engineering",
    "Which department has the highest budget?",
    "Top 5 sales by amount",
    "How many employees per department?",
    "Average salary by department",
    "Products with stock less than 100",
]
cols = st.columns(3)
for i, ex in enumerate(examples):
    if cols[i % 3].button(ex, key=f"ex_{i}", use_container_width=True):
        st.session_state.input_question = ex
        st.session_state.run_query_flag = True

st.divider()

# ── INPUT ─────────────────────────────────────────────────────────────────────
st.text_input(
    "🧠 Your question:",
    placeholder="e.g. Show employees with salary above 80000",
    key="input_question",
)

btn1, btn2 = st.columns([3, 1])
with btn1:
    if st.button("🚀 Run Query", type="primary",
                 use_container_width=True):
        st.session_state.run_query_flag = True
with btn2:
    follow_up_clicked = st.button(
        "🔁 Follow-up",
        use_container_width=True,
        help="Ask a follow-up about the last result",
        disabled=(st.session_state.last_sql is None)
    )

# ══════════════════════════════════════════════════════════════════════════════
# QUERY EXECUTION
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.run_query_flag or follow_up_clicked:

    st.session_state.run_query_flag = False

    question = st.session_state.input_question.strip()

    if not question:
        st.warning("⚠️ Please enter a question first.")
        st.stop()

    # ✅ Always defined first — fixes the 'not defined' error
    question_for_llm = question

    # Build follow-up context if needed
    if follow_up_clicked and st.session_state.conversation_history:
        context_parts = []
        for item in st.session_state.conversation_history[-3:]:
            context_parts.append(
                f"Previous Q: {item['question']}\n"
                f"Previous SQL: {item['sql']}"
            )
        context = "\n\n".join(context_parts)
        question_for_llm = (
            f"CONVERSATION CONTEXT:\n{context}\n\n"
            f"NEW QUESTION (follow-up): {question}"
        )

    st.session_state.total_queries += 1
    start_time = time.time()

    # ── RAG: Get only relevant schema ────────────────────────────────────
    with st.spinner("⚡ Generating SQL with RAG + Self-Correction..."):
        try:
            rag_schema = get_relevant_schema(question)

            generated_sql, was_corrected, attempts, gen_error = \
                generate_sql_with_correction(
                    question_for_llm, rag_schema
                )

            if generated_sql is None:
                raise Exception(gen_error or "Unknown LLM error")

        except Exception as e:
            elapsed = time.time() - start_time
            st.error(f"❌ LLM Error: {str(e)}")
            save_query_to_history(
                question, "LLM Error", False, 0, elapsed
            )
            st.session_state.query_history.append({
                "question":  question,
                "sql":       "LLM Error",
                "success":   False,
                "time":      elapsed,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            })
            st.stop()

    # ── CANNOT_ANSWER ─────────────────────────────────────────────────────
    if "CANNOT_ANSWER" in generated_sql.upper():
        st.warning("⚠️ Can't answer from available data.")
        st.info("Try: employees, departments, sales, products.")
        st.stop()

    # ── Safety guardrail ─────────────────────────────────────────────────
    is_safe, reason = is_safe_sql(generated_sql)
    if not is_safe:
        elapsed = time.time() - start_time
        st.error(f"🚫 Blocked: {reason}")
        save_query_to_history(
            question, generated_sql, False, 0, elapsed
        )
        st.stop()

    # ── Execute ───────────────────────────────────────────────────────────
    try:
        results_df = run_query(generated_sql)
    except Exception as e:
        elapsed = time.time() - start_time
        st.error(f"❌ DB Error: {str(e)}")
        save_query_to_history(
            question, generated_sql, False, 0, elapsed
        )
        st.stop()

    elapsed    = time.time() - start_time
    query_type = get_query_type(generated_sql)

    # ── Empty results ─────────────────────────────────────────────────────
    if results_df.empty:
        st.warning("📭 No results found.")
        save_query_to_history(
            question, generated_sql, True, 0, elapsed
        )
        st.stop()

    # ── Store in session state ────────────────────────────────────────────
    st.session_state.last_sql               = generated_sql
    st.session_state.last_results           = results_df
    st.session_state.last_question          = question
    st.session_state.last_query_type        = query_type
    st.session_state.last_elapsed           = elapsed
    st.session_state.last_was_corrected     = was_corrected
    st.session_state.last_correction_attempts = attempts
    st.session_state.successful_queries    += 1
    st.session_state.total_response_time   += elapsed

    # Save to conversation memory
    st.session_state.conversation_history.append({
        "question":  question,
        "sql":       generated_sql,
        "rows":      len(results_df),
        "elapsed":   elapsed,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })

    save_query_to_history(
        question, generated_sql, True, len(results_df), elapsed
    )
    st.session_state.query_history.append({
        "question":  question,
        "sql":       generated_sql,
        "success":   True,
        "time":      elapsed,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    })

# ══════════════════════════════════════════════════════════════════════════════
# RESULTS DISPLAY — reads from session state, chart won't re-run query
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.last_results is not None:

    results_df    = st.session_state.last_results
    generated_sql = st.session_state.last_sql
    question      = st.session_state.last_question
    query_type    = st.session_state.last_query_type
    elapsed       = st.session_state.last_elapsed
    was_corrected = st.session_state.last_was_corrected
    attempts      = st.session_state.last_correction_attempts

    # Self-correction banner
    if was_corrected:
        st.info(
            f"🔧 SQL auto-corrected in {attempts} attempt(s) "
            f"— self-healing pipeline active"
        )

    # ── SQL box ───────────────────────────────────────────────────────────
    badges = {
        "SELECT_SIMPLE":    "🔵 Simple",
        "SELECT_JOIN":      "🟣 JOIN",
        "SELECT_AGGREGATE": "🟠 Aggregate",
    }
    with st.expander("🔧 Generated SQL", expanded=True):
        st.caption(badges.get(query_type, "🔵"))
        st.code(generated_sql, language="sql")

    # ── Metrics ───────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("Rows",  len(results_df))
    m2.metric("Time",  f"{elapsed:.2f}s")
    m3.metric("Type",  query_type.replace("SELECT_", ""))

    # ── Table ─────────────────────────────────────────────────────────────
    st.subheader("📊 Results")
    st.dataframe(results_df, use_container_width=True)

    st.download_button(
        "⬇️ Download CSV",
        data=results_df.to_csv(index=False),
        file_name=f"results_{datetime.now().strftime('%H%M%S')}.csv",
        mime="text/csv"
    )

    # ── Smart Chart ───────────────────────────────────────────────────────
    skip_cols    = {"id", "employee_id", "index"}
    numeric_cols = [
        c for c in results_df.select_dtypes(
            include=["int64", "float64"]
        ).columns
        if c.lower() not in skip_cols
    ]
    text_cols = results_df.select_dtypes(
        include=["object"]
    ).columns.tolist()

    if numeric_cols and text_cols and len(results_df) > 1:
        st.subheader("📈 Chart")
        cc1, cc2 = st.columns([1, 3])
        with cc1:
            chart_type = st.radio(
                "Type:", ["Bar", "Line", "Pie"],
                key="chart_radio"
            )
            x_col = st.selectbox(
                "X axis:", text_cols, key="x_col"
            )
            y_col = st.selectbox(
                "Y axis:", numeric_cols, key="y_col"
            )
        with cc2:
            try:
                if chart_type == "Bar":
                    fig = px.bar(
                        results_df, x=x_col, y=y_col,
                        color=y_col,
                        color_continuous_scale="blues",
                        title=f"{y_col} by {x_col}"
                    )
                elif chart_type == "Line":
                    fig = px.line(
                        results_df, x=x_col, y=y_col,
                        markers=True,
                        title=f"{y_col} over {x_col}"
                    )
                else:
                    fig = px.pie(
                        results_df, names=x_col, values=y_col,
                        title=f"{y_col} distribution"
                    )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.info("Chart not available for this data.")

    # ── SQL Confidence Score ──────────────────────────────────────────────
    st.subheader("🎯 SQL Confidence Score")
    score  = 100
    issues = []
    if "LIMIT" not in generated_sql.upper():
        score -= 10
        issues.append("No LIMIT clause")
    if "JOIN" in generated_sql.upper():
        score += 5
    if elapsed < 3:
        score += 5
    if was_corrected:
        score -= 10
        issues.append(f"Needed {attempts} auto-correction(s)")
    score = min(score, 100)

    color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
    st.metric(f"{color} Confidence", f"{score}/100")
    for issue in issues:
        st.caption(f"⚠️ {issue}")

    # ── Explanation + Summary ─────────────────────────────────────────────
    ec, sc = st.columns(2)
    with ec:
        with st.expander("💬 What does this query do?"):
            with st.spinner("Loading..."):
                try:
                    st.info(
                        generate_explanation(generated_sql, question)
                    )
                except Exception:
                    st.info("Not available.")
    with sc:
        with st.expander("🧠 Business Insight"):
            with st.spinner("Analyzing..."):
                try:
                    st.success(
                        generate_summary(
                            question,
                            results_df.head(5).to_string()
                        )
                    )
                except Exception:
                    st.success("Not available.")

    # ── Follow-up Suggestions ─────────────────────────────────────────────
    st.divider()
    st.subheader("🔁 Follow-up Questions")

    follow_ups = []
    sql_lower  = generated_sql.lower()
    if "employees" in sql_lower:
        follow_ups = [
            "What is their average salary?",
            "Who joined most recently?",
            "Show only those earning above 90000",
        ]
    elif "department" in sql_lower:
        follow_ups = [
            "Which has the most employees?",
            "Compare their budgets",
            "Show departments in New York only",
        ]
    elif "sales" in sql_lower:
        follow_ups = [
            "Which region had highest sales?",
            "Who made the most sales?",
            "Show sales above 1000",
        ]
    elif "product" in sql_lower:
        follow_ups = [
            "Which category has most products?",
            "Show products with price above 200",
            "Which product has lowest stock?",
        ]

    if follow_ups:
        fu1, fu2, fu3 = st.columns(3)
        fu_cols = [fu1, fu2, fu3]
        for i, fu in enumerate(follow_ups):
            if fu_cols[i].button(
                fu, key=f"fu_{i}", use_container_width=True
            ):
                st.session_state["_pending_question"] = fu
                st.session_state.run_query_flag  = True
                st.rerun()

    # ── Full Conversation History ─────────────────────────────────────────
    if len(st.session_state.conversation_history) > 1:
        st.divider()
        st.subheader("📜 Full Conversation History")
        for i, item in enumerate(
            st.session_state.conversation_history
        ):
            with st.expander(
                f"#{i+1} — {item['question'][:50]}"
            ):
                st.code(item["sql"], language="sql")
                st.caption(
                    f"✅ {item['rows']} rows | "
                    f"⏱ {item['elapsed']:.2f}s | "
                    f"🕐 {item['timestamp']}"
                )