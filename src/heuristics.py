def evaluate_semantic_sanity(sql: str, results: list, question: str) -> dict:
    """
    Evaluates a successful SQL execution result for semantic suspicion.
    
    Checks:
    1. Cartesian Product: Row count > 1000.
    2. Unexpected Empty Results: 0 rows when question implies entities/data.
    3. Single Null Aggregation: 1 row returned where aggregated value(s) are NULL.
    
    Returns:
        dict: {
            "is_suspicious": bool,
            "reason": str or None,
            "failure_type": "semantic" or None
        }
    """
    if results is None:
        results = []

    # Heuristic 1: Cartesian Product (Row count explosion)
    if len(results) > 1000:
        return {
            "is_suspicious": True,
            "reason": "Result set is unusually large. Check for missing JOIN conditions (Cartesian product).",
            "failure_type": "semantic"
        }

    # Heuristic 2: Unexpected Empty Results
    # Questions asking for entities or specific data usually expect at least one result
    entity_keywords = [
        "which", "who", "list", "show", "what", "find", "get", "how many", "top", "calculate",
        "average", "total", "sum", "count", "details", "display", "select"
    ]
    question_lower = question.lower()
    expecting_data = any(kw in question_lower for kw in entity_keywords)
    
    # Exclude questions explicitly asking if something exists or checking for zero/none
    explicit_zero_check = any(phrase in question_lower for phrase in ["are there any", "is there any", "does any", "zero", "none"])

    if len(results) == 0 and expecting_data and not explicit_zero_check:
        return {
            "is_suspicious": True,
            "reason": "Query returned 0 rows, but the question implies entities exist. Check WHERE clause filters (date ranges, exact string matches).",
            "failure_type": "semantic"
        }

    # Heuristic 3: Single NULL Aggregation Value
    if len(results) == 1:
        row = results[0]
        if isinstance(row, dict) and len(row) > 0:
            # Check if all values in the single row are None/NULL
            all_null = all(val is None for val in row.values())
            # Or if common aggregation field names are NULL
            agg_keys = [k for k in row.keys() if any(agg in k.lower() for agg in ["sum", "avg", "total", "count", "min", "max", "amount", "revenue"])]
            agg_null = any(row[k] is None for k in agg_keys) if agg_keys else False

            if all_null or agg_null:
                return {
                    "is_suspicious": True,
                    "reason": "Query returned a single row with a NULL aggregation value. Check WHERE clause filters or NULL handling.",
                    "failure_type": "semantic"
                }

    return {
        "is_suspicious": False,
        "reason": None,
        "failure_type": None
    }
