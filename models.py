from pydantic import BaseModel
from typing import List, Dict, Any

class DataQualityReport(BaseModel):
    missing_values: Dict[str, int]
    invalid_records: Dict[str, int]
    schema_violations: Dict[str, int]

class BusinessInsights(BaseModel):
    top_customers: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]] 
    shipping_performance: Dict[str, float] = {}
    return_analysis: Dict[str, int]

class EvaluationResponse(BaseModel):
    status: str
    score: float
    details: Dict[str, Any]
    performance: Dict[str, Any]
