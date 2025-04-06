from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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

class PerformanceMetrics(BaseModel):
    duration_sec: float
    cpu_avg: float
    memory_avg: float
    sample_count: int
    status: str
    timestamp: Optional[datetime] = None

class MetricsPayload(BaseModel):
    top_5_customers_by_total_spend: List[CustomerMetric]
    top_5_products_by_revenue: List[ProductMetric]
    shipping_performance_by_carrier: List[ShippingMetric] 
    return_reason_analysis: List[ReturnMetric]

class CombinedMetricsPayload(BaseModel):
    business_metrics: MetricsPayload
    performance_metrics: PerformanceMetrics
