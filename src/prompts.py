SYSTEM_PROMPT = """You are an expert PostgreSQL database administrator and SQL developer.
Your goal is to translate Natural Language questions into precise, valid, read-only PostgreSQL SELECT queries.

Database Schema DDL:
{schema_ddl}

Strict Guidelines:
1. Generate ONLY SELECT statements. Never output DROP, DELETE, UPDATE, INSERT, ALTER, or TRUNCATE.
2. Pay close attention to table schema details:
   - Primary key of `customers` is `customer_id` (NOT `id`).
   - Foreign key in `orders` referencing `customers` is `cust_id`.
   - `customers.region` can be NULL.
   - `orders.total_amount` is denormalized total order value.
   - `line_items` contains granular product lines (`qty`, `unit_price`).
3. Output ONLY raw PostgreSQL query syntax. Do NOT wrap the query in markdown backticks (```sql), and do NOT add conversational text.
""".strip()


def build_initial_prompt(question: str) -> str:
    return f"""User Question: "{question}"

Write a valid PostgreSQL SELECT query to answer this question. Respond with ONLY the SQL statement."""


def format_history(history: list) -> str:
    """Formats prior attempt history so the LLM does not repeat past mistakes."""
    if not history:
        return ""
    
    lines = ["\nPrior Failed Attempts:"]
    for item in history:
        lines.append(f"- Attempt {item['attempt']}: SQL: `{item.get('sql', '')}`")
        lines.append(f"  Failure Type: {item.get('failure_type')}")
        lines.append(f"  Error Detail: {item.get('error_message')}")
    lines.append("\nDo NOT repeat any of the SQL queries or mistakes listed above.")
    return "\n".join(lines)


def build_syntax_repair_prompt(question: str, invalid_sql: str, error_msg: str, history: list = None) -> str:
    """Prompt template for Syntax Errors and AST Guardrail violations."""
    history_text = format_history(history)
    return f"""User Question: "{question}"

Your previously generated SQL query failed AST Parsing / Security Guardrail checks:

Failed SQL:
{invalid_sql}

Parser Diagnostic / Guardrail Error:
{error_msg}
{history_text}

Repair Instructions:
1. Fix all SQL syntax errors for standard PostgreSQL dialect.
2. Ensure the query is strictly a read-only SELECT statement.
3. Respond ONLY with the corrected raw PostgreSQL SQL query."""


def build_schema_repair_prompt(question: str, invalid_sql: str, error_msg: str, schema_ddl: str, history: list = None) -> str:
    """Prompt template for Database Catalog / Schema Mismatch Errors."""
    history_text = format_history(history)
    return f"""User Question: "{question}"

Your previously generated SQL query produced a Database Engine Schema Error during execution:

Failed SQL:
{invalid_sql}

Database Engine Error:
{error_msg}

Database Catalog DDL:
{schema_ddl}
{history_text}

Repair Instructions:
1. Inspect the Database Catalog DDL carefully to find the correct table and column names.
2. Note key foreign relationships (e.g. `orders.cust_id` joins with `customers.customer_id`).
3. Fix the missing/invalid column or table references.
4. Respond ONLY with the corrected raw PostgreSQL SQL query."""


def build_semantic_repair_prompt(question: str, sql: str, reason: str, results: list, history: list = None) -> str:
    """Prompt template for Semantic Suspicion Failures (e.g. Cartesian products, unexpected 0 rows, NULL aggregations)."""
    sample_rows = results[:3] if results else []
    sample_text = str(sample_rows) if sample_rows else "[] (0 rows returned)"
    history_text = format_history(history)

    return f"""User Question: "{question}"

Your SQL query executed without syntax or schema errors, but failed a Semantic Sanity Check:

Executed SQL:
{sql}

Sample Result Output (First 3 rows):
{sample_text}

Semantic Suspicion Reason:
{reason}
{history_text}

Repair Instructions:
1. Analyze why the result set is semantically suspicious for the question asked.
2. Check for missing/incorrect JOIN conditions (e.g. to prevent Cartesian products).
3. Check for overly restrictive WHERE clause filters or improper date/string comparisons.
4. Fix the aggregation or filtering logic so it returns accurate data.
5. Respond ONLY with the corrected raw PostgreSQL SQL query."""
