import re

try:
    import sqlglot
    from sqlglot import parse_one, exp
    from sqlglot.errors import ParseError, SqlglotError
    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False
    sqlglot = None
    exp = None
    ParseError = Exception
    SqlglotError = Exception


def clean_sql_markdown(sql_string: str) -> str:
    """Strips markdown code fences (```sql ... ```) and leading/trailing whitespace."""
    if not sql_string:
        return ""
    cleaned = re.sub(r'```(?:sql)?\s*(.*?)\s*```', r'\1', sql_string, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.strip().strip('`')
    return cleaned


def validate_and_guard_sql(sql_string: str) -> dict:
    """
    Validates that a SQL string is safe and syntactically correct using sqlglot (or fallback guardrails).
    Rejects non-SELECT queries (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE) as syntax guardrail violations.
    """
    cleaned = clean_sql_markdown(sql_string)
    if not cleaned:
        return {
            "is_valid": False,
            "sql": sql_string,
            "error": "Syntax Error: Empty SQL statement provided.",
            "error_type": "syntax"
        }
    
    # Check for obvious destructive statement keywords
    raw_upper = cleaned.upper()
    destructive_keywords = ["DROP ", "DELETE ", "UPDATE ", "INSERT ", "ALTER ", "TRUNCATE "]
    for kw in destructive_keywords:
        if kw in raw_upper:
            return {
                "is_valid": False,
                "sql": cleaned,
                "error": f"Security Guardrail Violation: Destructive command '{kw.strip()}' is strictly prohibited. Only read-only SELECT queries are allowed.",
                "error_type": "syntax"
            }

    if not raw_upper.startswith("SELECT") and not raw_upper.startswith("WITH"):
        return {
            "is_valid": False,
            "sql": cleaned,
            "error": "Security Guardrail Violation: Only SELECT statements are permitted.",
            "error_type": "syntax"
        }

    # Common syntax error pattern checks
    malformed_patterns = [
        r'SELECT\s+FROM',
        r'=\s*;?\s*$',
        r'WHERE\s*;?\s*$'
    ]
    for pattern in malformed_patterns:
        if re.search(pattern, raw_upper):
            return {
                "is_valid": False,
                "sql": cleaned,
                "error": "Syntax Error: Malformed SQL statement.",
                "error_type": "syntax"
            }

    if HAS_SQLGLOT:
        try:
            ast = parse_one(cleaned, read='postgres')
            if ast is None:
                return {
                    "is_valid": False,
                    "sql": cleaned,
                    "error": "Syntax Error: Could not parse SQL statement.",
                    "error_type": "syntax"
                }
            
            is_select = isinstance(ast, (exp.Select, exp.Union))
            forbidden_nodes = tuple(
                fn for fn in [
                    getattr(exp, 'Drop', None),
                    getattr(exp, 'Delete', None),
                    getattr(exp, 'Update', None),
                    getattr(exp, 'Insert', None),
                    getattr(exp, 'Create', None),
                    getattr(exp, 'TruncateTable', None)
                ] if fn is not None
            )
            has_forbidden_nodes = any(ast.find(fn) for fn in forbidden_nodes) if forbidden_nodes else False

            if not is_select or has_forbidden_nodes:
                return {
                    "is_valid": False,
                    "sql": cleaned,
                    "error": "Security Guardrail Violation: Only SELECT statements are permitted.",
                    "error_type": "syntax"
                }

            return {
                "is_valid": True,
                "sql": ast.sql(dialect='postgres'),
                "error": None,
                "error_type": None
            }
        except (ParseError, SqlglotError, Exception) as e:
            return {
                "is_valid": False,
                "sql": cleaned,
                "error": f"Syntax Error: {str(e)}",
                "error_type": "syntax"
            }
    else:
        return {
            "is_valid": True,
            "sql": cleaned,
            "error": None,
            "error_type": None
        }
