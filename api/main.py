import os
import sys
from typing import List, Dict, Any, Optional

try:
    from fastapi import FastAPI, HTTPException, status
    from pydantic import BaseModel, Field
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = None
    HTTPException = Exception
    status = None
    BaseModel = object
    Field = lambda *args, **kwargs: None

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agent import TextToSQLAgent

if HAS_FASTAPI:
    app = FastAPI(
        title="Self-Correcting Text-to-SQL API",
        description="Production-grade Text-to-SQL engine with AST guardrails and Typed Repair Policy (Syntax, Schema, Semantic)",
        version="1.0.0"
    )

    agent = TextToSQLAgent(max_iterations=3)

    class QueryRequest(BaseModel):
        question: str = Field(..., example="Show me all customers in New York")
        mode: Optional[str] = Field("full_pipeline", example="full_pipeline")

    class RepairHistoryItem(BaseModel):
        attempt: int
        failure_type: str
        error_message: str

    class QueryResponse(BaseModel):
        status: str
        final_sql: str
        results: List[Dict[str, Any]]
        iterations: int
        repair_history: List[RepairHistoryItem]

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.post("/api/query", response_model=QueryResponse)
    def run_query(request: QueryRequest):
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question string cannot be empty."
            )
        
        mode = request.mode if request.mode in ["full_pipeline", "syntax_schema_repair_only", "zero_shot"] else "full_pipeline"
        result = agent.run(question=request.question, mode=mode)
        
        formatted_history = [
            RepairHistoryItem(
                attempt=item["attempt"],
                failure_type=item["failure_type"],
                error_message=item["error_message"]
            )
            for item in result.get("repair_history", [])
        ]

        return QueryResponse(
            status=result["status"],
            final_sql=result.get("final_sql", ""),
            results=result.get("results", []),
            iterations=result.get("iterations", 1),
            repair_history=formatted_history
        )
else:
    app = None
