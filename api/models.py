from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class PerformanceMetrics(BaseModel):
    duration_sec: float = Field(..., gt=0, description="Execution duration in seconds")
    cpu_avg: float = Field(..., ge=0, le=100, description="Average CPU usage %")
    memory_avg: float = Field(..., ge=0, description="Average memory usage MB")
    sample_count: int = Field(..., gt=0)
    status: str = Field(..., pattern="^(success|failed|running)$")
    timestamp: Optional[datetime] = None
    additional_metrics: Optional[Dict[str, Any]] = None

    @validator('timestamp', pre=True, always=True)
    def set_default_timestamp(cls, v):
        return v or datetime.utcnow()

class CustomerMetric(BaseModel):
    customer_id: str
    customer_name: str 
    total_spent: float

class ProductMetric(BaseModel):
    product_id: str
    product_name: str
    total_revenue: float

class ShippingMetric(BaseModel):
    carrier: str
    total_shipments: int
    on_time_deliveries: int
    delayed_shipments: int
    undelivered_shipments: int

class ReturnMetric(BaseModel):
    reason: str
    total_returns: int
    total_refund_amount: float

class MetricsPayload(BaseModel):
    top_5_customers_by_total_spend: List[CustomerMetric]
    top_5_products_by_revenue: List[ProductMetric]
    shipping_performance_by_carrier: List[ShippingMetric] 
    return_reason_analysis: List[ReturnMetric]

class ValidName(BaseModel):
    uuid: str
    name: str

class DataQualityMetrics(BaseModel):
    invalid_customers_records: int = Field(..., ge=0)
    invalid_products_records: int = Field(..., ge=0)
    invalid_shipment_records: int = Field(..., ge=0)
    invalid_return_records: int = Field(..., ge=0)
    invalid_order_records: int = Field(..., ge=0)

class BusinessMetrics(MetricsPayload):
    pass  # Inherits all fields from MetricsPayload

class NewEvaluationPayload(BaseModel):
    valid_names: List[ValidName]
    data_quality_metrics: DataQualityMetrics
    business_metrics: BusinessMetrics
    performance_metrics: PerformanceMetrics

class CombinedMetricsPayload(BaseModel):
    business_metrics: MetricsPayload
    performance_metrics: PerformanceMetrics
