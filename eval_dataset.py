"""
Evaluation Dataset
==================
50 real questions with expected SQL patterns.
Yeh questions different complexity levels cover karte hain.
"""

EVAL_DATASET = [
    # ── SIMPLE SELECT (10 questions) ─────────────────────────────
    {
        "id": 1,
        "question": "Show all employees",
        "expected_keywords": ["SELECT", "employees"],
        "expected_tables": ["employees"],
        "complexity": "simple",
        "category": "basic_select"
    },
    {
        "id": 2,
        "question": "List all departments",
        "expected_keywords": ["SELECT", "departments"],
        "expected_tables": ["departments"],
        "complexity": "simple",
        "category": "basic_select"
    },
    {
        "id": 3,
        "question": "Show all products",
        "expected_keywords": ["SELECT", "products"],
        "expected_tables": ["products"],
        "complexity": "simple",
        "category": "basic_select"
    },
    {
        "id": 4,
        "question": "List all sales",
        "expected_keywords": ["SELECT", "sales"],
        "expected_tables": ["sales"],
        "complexity": "simple",
        "category": "basic_select"
    },
    {
        "id": 5,
        "question": "Show all employees in Engineering department",
        "expected_keywords": ["SELECT", "employees", "Engineering"],
        "expected_tables": ["employees"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "id": 6,
        "question": "Show employees with salary above 90000",
        "expected_keywords": ["SELECT", "salary", "90000"],
        "expected_tables": ["employees"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "id": 7,
        "question": "Show products with stock less than 100",
        "expected_keywords": ["SELECT", "stock", "100"],
        "expected_tables": ["products"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "id": 8,
        "question": "Show employees hired after 2021-01-01",
        "expected_keywords": ["SELECT", "hire_date", "2021"],
        "expected_tables": ["employees"],
        "complexity": "simple",
        "category": "filter"
    },
    {
        "id": 9,
        "question": "Show top 5 most expensive products",
        "expected_keywords": ["SELECT", "price", "LIMIT"],
        "expected_tables": ["products"],
        "complexity": "simple",
        "category": "order_limit"
    },
    {
        "id": 10,
        "question": "Show top 5 sales by amount",
        "expected_keywords": ["SELECT", "amount", "LIMIT"],
        "expected_tables": ["sales"],
        "complexity": "simple",
        "category": "order_limit"
    },

    # ── AGGREGATION (15 questions) ────────────────────────────────
    {
        "id": 11,
        "question": "How many employees are there in total?",
        "expected_keywords": ["COUNT", "employees"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 12,
        "question": "How many employees are in each department?",
        "expected_keywords": ["COUNT", "department", "GROUP BY"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 13,
        "question": "What is the average salary of all employees?",
        "expected_keywords": ["AVG", "salary"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 14,
        "question": "What is the average salary by department?",
        "expected_keywords": ["AVG", "salary", "GROUP BY", "department"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 15,
        "question": "What is the total budget across all departments?",
        "expected_keywords": ["SUM", "budget"],
        "expected_tables": ["departments"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 16,
        "question": "Which department has the highest budget?",
        "expected_keywords": ["budget", "MAX", "ORDER BY"],
        "expected_tables": ["departments"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 17,
        "question": "What is the total sales amount?",
        "expected_keywords": ["SUM", "amount", "sales"],
        "expected_tables": ["sales"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 18,
        "question": "What is the total sales amount by region?",
        "expected_keywords": ["SUM", "amount", "region", "GROUP BY"],
        "expected_tables": ["sales"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 19,
        "question": "What is the maximum salary in the company?",
        "expected_keywords": ["MAX", "salary"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 20,
        "question": "What is the minimum salary in the company?",
        "expected_keywords": ["MIN", "salary"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 21,
        "question": "How many products are in each category?",
        "expected_keywords": ["COUNT", "category", "GROUP BY"],
        "expected_tables": ["products"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 22,
        "question": "What is the average product price?",
        "expected_keywords": ["AVG", "price"],
        "expected_tables": ["products"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 23,
        "question": "What is the highest sale amount ever made?",
        "expected_keywords": ["MAX", "amount"],
        "expected_tables": ["sales"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 24,
        "question": "How many sales were made in each region?",
        "expected_keywords": ["COUNT", "region", "GROUP BY"],
        "expected_tables": ["sales"],
        "complexity": "medium",
        "category": "aggregation"
    },
    {
        "id": 25,
        "question": "What is the total stock across all products?",
        "expected_keywords": ["SUM", "stock"],
        "expected_tables": ["products"],
        "complexity": "medium",
        "category": "aggregation"
    },

    # ── FILTER + SORT (10 questions) ──────────────────────────────
    {
        "id": 26,
        "question": "Show employees sorted by salary highest to lowest",
        "expected_keywords": ["ORDER BY", "salary", "DESC"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 27,
        "question": "Show the 3 highest paid employees",
        "expected_keywords": ["salary", "ORDER BY", "LIMIT", "3"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 28,
        "question": "Show sales made in North region",
        "expected_keywords": ["region", "North"],
        "expected_tables": ["sales"],
        "complexity": "simple",
        "category": "sort_filter"
    },
    {
        "id": 29,
        "question": "Show products in Electronics category",
        "expected_keywords": ["category", "Electronics"],
        "expected_tables": ["products"],
        "complexity": "simple",
        "category": "sort_filter"
    },
    {
        "id": 30,
        "question": "Show employees in HR or Marketing department",
        "expected_keywords": ["department", "HR", "Marketing"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 31,
        "question": "Show products with price between 50 and 500",
        "expected_keywords": ["price", "50", "500"],
        "expected_tables": ["products"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 32,
        "question": "Show sales made after 2024-06-01",
        "expected_keywords": ["sale_date", "2024-06"],
        "expected_tables": ["sales"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 33,
        "question": "Show employees whose name starts with A",
        "expected_keywords": ["name", "LIKE", "A%"],
        "expected_tables": ["employees"],
        "complexity": "medium",
        "category": "sort_filter"
    },
    {
        "id": 34,
        "question": "Show departments with budget greater than 500000",
        "expected_keywords": ["budget", "500000"],
        "expected_tables": ["departments"],
        "complexity": "simple",
        "category": "sort_filter"
    },
    {
        "id": 35,
        "question": "Show the cheapest 3 products",
        "expected_keywords": ["price", "ORDER BY", "LIMIT", "3"],
        "expected_tables": ["products"],
        "complexity": "medium",
        "category": "sort_filter"
    },

    # ── MULTI-TABLE JOIN (10 questions) ───────────────────────────
    {
        "id": 36,
        "question": "Show employee names with their total sales amount",
        "expected_keywords": ["JOIN", "employees", "sales", "SUM"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 37,
        "question": "Which employee made the most sales?",
        "expected_keywords": ["JOIN", "employees", "sales", "COUNT"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 38,
        "question": "Show all sales with the employee name who made them",
        "expected_keywords": ["JOIN", "employees", "sales"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 39,
        "question": "Show employees and their department budget",
        "expected_keywords": ["JOIN", "employees", "departments"],
        "expected_tables": ["employees", "departments"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 40,
        "question": "Show total sales amount by employee name",
        "expected_keywords": ["JOIN", "SUM", "amount", "name"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 41,
        "question": "Which department's employees made the most total sales?",
        "expected_keywords": ["JOIN", "department", "SUM", "sales"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 42,
        "question": "Show sales made by Engineering employees",
        "expected_keywords": ["JOIN", "Engineering", "sales"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 43,
        "question": "Show the top salesperson by revenue with their department",
        "expected_keywords": ["JOIN", "SUM", "amount", "department"],
        "expected_tables": ["employees", "sales", "departments"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 44,
        "question": "Show average sale amount per employee",
        "expected_keywords": ["JOIN", "AVG", "amount"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },
    {
        "id": 45,
        "question": "How many sales did each employee make?",
        "expected_keywords": ["JOIN", "COUNT", "employees", "sales"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "join"
    },

    # ── EDGE CASES (5 questions) ──────────────────────────────────
    {
        "id": 46,
        "question": "Show employees with no sales",
        "expected_keywords": ["LEFT JOIN", "NULL", "sales"],
        "expected_tables": ["employees", "sales"],
        "complexity": "hard",
        "category": "edge_case"
    },
    {
        "id": 47,
        "question": "Show the second highest salary",
        "expected_keywords": ["salary", "LIMIT", "OFFSET"],
        "expected_tables": ["employees"],
        "complexity": "hard",
        "category": "edge_case"
    },
    {
        "id": 48,
        "question": "Show departments that have more than 2 employees",
        "expected_keywords": ["GROUP BY", "HAVING", "COUNT"],
        "expected_tables": ["employees"],
        "complexity": "hard",
        "category": "edge_case"
    },
    {
        "id": 49,
        "question": "What is the weather like today?",
        "expected_keywords": ["CANNOT_ANSWER"],
        "expected_tables": [],
        "complexity": "simple",
        "category": "out_of_scope"
    },
    {
        "id": 50,
        "question": "Delete all employees",
        "expected_keywords": ["CANNOT_ANSWER", "SELECT"],
        "expected_tables": [],
        "complexity": "simple",
        "category": "security"
    },
]