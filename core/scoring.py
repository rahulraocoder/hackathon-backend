import json
import time
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def load_perfect_metrics() -> Dict:
    """Load the perfect evaluation metrics from JSON"""
    try:
        with open(Path(__file__).parent.parent / 'perfect_evaluation.json') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading perfect metrics: {e}")
        raise ValueError("Could not load evaluation benchmarks")

def is_match(a: Dict, b: Dict, keys: list) -> bool:
    """Check if specified keys match between two dicts"""
    return all(a.get(k) == b.get(k) for k in keys)

def score_exact_match_list(participant_list, perfect_list, keys) -> float:
    """Score exact match on list elements with corresponding position"""
    score = 0
    for p, perfect in zip(participant_list, perfect_list):
        if p.get(keys[0]) == perfect.get(keys[0]):  # Position match
            score += 6
        if p.get(keys[1]) == perfect.get(keys[1]):  # Value match
            score += 3
        if p.get(keys[2]) == perfect.get(keys[2]):  # Name match
            score += 1
    return score

def validate_names(participant_names: list, perfect_names: list) -> float:
    """Validate name mappings (30 points)"""
    valid_names_count = len(perfect_names)
    score_per_name = 30 / valid_names_count if valid_names_count > 0 else 0
    score = 0.0

    valid_uuid_name_map = {n['uuid']: n['name'].lower() for n in perfect_names}
    valid_uuid_set = set(valid_uuid_name_map.keys())

    for p_name in participant_names:
        uuid = p_name['uuid']
        name = p_name['name'].lower()
        if uuid in valid_uuid_set and name == valid_uuid_name_map[uuid]:
            score += score_per_name

    return min(30, score)

def score_data_quality(participant_metrics: Dict, perfect_metrics: Dict) -> float:
    """Score data quality metrics (25 points)"""
    score = 0
    perfect = perfect_metrics['data_quality_metrics']
    participant = participant_metrics.get('data_quality_metrics', {})
    
    # Each invalid record type is worth 5 points (5 types x 5 points = 25)
    for key in ['customers', 'products', 'shipments', 'returns', 'orders']:
        perfect_key = f'invalid_{key}_records'
        if perfect_key in participant:
            diff = abs(perfect[perfect_key] - participant[perfect_key])
            score += max(0, 5 - diff)  # Lose 1 point per invalid record difference
    
    return min(25, score)

def calculate_score(participant_metrics: Dict) -> float:
    """
    Calculate score (0-75) using new scoring system:
    - Name matching: 30 points
    - Data quality: 25 points
    - Business metrics: 20 points
    """
    start_time = time.time()
    perfect_metrics = load_perfect_metrics()
    score = 0.0

    # Validate required sections
    required = ['valid_names', 'data_quality_metrics', 'business_metrics']
    for section in required:
        if section not in participant_metrics:
            raise ValueError(f"Missing required section: {section}")

    try:
        # Name matching (30 points)
        score += validate_names(
            participant_metrics['valid_names'],
            perfect_metrics['valid_names']
        )

        # Data quality (25 points)
        score += score_data_quality(participant_metrics, perfect_metrics)

        # Business metrics (20 points)
        business_score = 0
        perfect_biz = perfect_metrics['business_metrics']
        participant_biz = participant_metrics['business_metrics']
        
        # Customers (5 points)
        if is_match(participant_biz['top_5_customers_by_total_spend'][0],
                   perfect_biz['top_5_customers_by_total_spend'][0],
                   ['customer_id', 'total_spent']):
            business_score += 5

        # Products (5 points)
        if is_match(participant_biz['top_5_products_by_revenue'][0],
                   perfect_biz['top_5_products_by_revenue'][0],
                   ['product_id', 'total_revenue']):
            business_score += 5

        # Shipping (5 points)
        if (participant_biz['shipping_performance_by_carrier'][0]['on_time_deliveries'] == 
            perfect_biz['shipping_performance_by_carrier'][0]['on_time_deliveries']):
            business_score += 5

        # Returns (5 points)
        if (participant_biz['return_reason_analysis'][0]['total_returns'] == 
            perfect_biz['return_reason_analysis'][0]['total_returns']):
            business_score += 5

        score += min(20, business_score)

    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        raise ValueError("Invalid metrics format") from e

    exec_time = time.time() - start_time
    logger.info(f"Execution Time: {exec_time:.4f} seconds")

    return min(75.0, round(score, 2))
