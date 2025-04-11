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

def calculate_score(participant_metrics: Dict) -> float:
    """
    Calculate score (0-100) by comparing participant metrics with perfect benchmarks.
    Scoring Breakdown:
        - Customers (30 points): ranking, amounts, details
        - Products (30 points): ranking, revenue, details  
        - Shipping (20 points): performance metrics
        - Returns (20 points): analysis accuracy
    """
    start_time = time.time()
    perfect_metrics = load_perfect_metrics()
    score = 0.0

    required_sections = [
        'top_5_customers_by_total_spend',
        'top_5_products_by_revenue',
        'shipping_performance_by_carrier',
        'return_reason_analysis'
    ]
    for section in required_sections:
        if section not in participant_metrics:
            raise ValueError(f"Missing required metrics section: {section}")

    try:
        # Customers (30 points)
        score += score_exact_match_list(
            participant_metrics['top_5_customers_by_total_spend'],
            perfect_metrics['top_5_customers_by_total_spend'],
            ['customer_id', 'total_spent', 'customer_name']
        )

        # Products (30 points)
        score += score_exact_match_list(
            participant_metrics['top_5_products_by_revenue'],
            perfect_metrics['top_5_products_by_revenue'],
            ['product_id', 'total_revenue', 'product_name']
        )

        # Shipping (20 points)
        perfect_shipping = {s['carrier']: s for s in perfect_metrics['shipping_performance_by_carrier']}
        for s in participant_metrics['shipping_performance_by_carrier']:
            perfect = perfect_shipping.get(s['carrier'])
            if not perfect:
                continue
            on_time = s.get('on_time_deliveries', 0) / s['total_shipments'] * 100
            if on_time == perfect['on_time_percentage']:
                score += 10
            if set(s.get('problem_issues', [])) == set(perfect['problem_issues']):
                score += 10

        # Returns (20 points)
        perfect_returns = {r['reason']: r for r in perfect_metrics['return_reason_analysis']}
        for r in participant_metrics['return_reason_analysis']:
            perfect = perfect_returns.get(r['reason'])
            if not perfect:
                continue
            if r['total_returns'] == perfect['return_percentage']:
                score += 10
            if r['total_refund_amount'] == perfect['average_refund_amount']:
                score += 10

    except Exception as e:
        logger.error(f"Error calculating score: {e}")
        raise ValueError("Invalid metrics format") from e

    exec_time = time.time() - start_time
    logger.info(f"Execution Time (not scored): {exec_time:.4f} seconds")

    return min(100.0, round(score, 2))
