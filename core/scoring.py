import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def load_perfect_metrics() -> Dict:
    """Load the perfect evaluation metrics from JSON"""
    try:
        with open(Path(__file__).parent.parent / 'perfect_evaluation.json') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading perfect metrics: {str(e)}")
        raise ValueError("Could not load evaluation benchmarks")

def calculate_score(participant_metrics: Dict) -> float:
    """
    Calculate score (0-100) by comparing participant metrics with perfect benchmarks
    
    Scoring Breakdown:
    - Customers (30 points): ranking, amounts, details
    - Products (30 points): ranking, revenue, details  
    - Shipping (20 points): performance metrics
    - Returns (20 points): analysis accuracy
    
    Returns:
        float: Score between 0-100
    """
    perfect_metrics = load_perfect_metrics()
    score = 0.0
    
    # Validate input metrics
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
        # Customer scoring (30 points)
        perfect_customers = {c['customer_id']:c for c in perfect_metrics['top_5_customers_by_total_spend']}
        for i, cust in enumerate(participant_metrics['top_5_customers_by_total_spend'][:5]):
            if cust['customer_id'] in perfect_customers:
                perfect = perfect_customers[cust['customer_id']]
                # Position match (6 points per correct position)
                if i == list(perfect_customers.keys()).index(cust['customer_id']):
                    score += 6
                # Spend accuracy (3 points if within 10%)
                if abs(cust['total_spent'] - perfect['total_spent'])/perfect['total_spent'] <= 0.1:
                    score += 3
                # Name match (1 point)
                if cust.get('customer_name') == perfect['customer_name']:
                    score += 1

        # Product scoring (30 points)
        perfect_products = {p['product_id']:p for p in perfect_metrics['top_5_products_by_revenue']}
        for i, prod in enumerate(participant_metrics['top_5_products_by_revenue'][:5]):
            if prod['product_id'] in perfect_products:
                perfect = perfect_products[prod['product_id']]
                # Position match (6 points)
                if i == list(perfect_products.keys()).index(prod['product_id']):
                    score += 6  
                # Revenue accuracy (3 points)
                if abs(prod['total_revenue'] - perfect['total_revenue'])/perfect['total_revenue'] <= 0.1:
                    score += 3
                # Name match (1 point)
                if prod.get('product_name') == perfect['product_name']:
                    score += 1

        # Shipping scoring (20 points)
        perfect_shipping = {s['carrier']:s for s in perfect_metrics['shipping_performance_by_carrier']}
        for ship in participant_metrics['shipping_performance_by_carrier']:
            if ship['carrier'] in perfect_shipping:
                perfect = perfect_shipping[ship['carrier']]
                # On-time percentage (10 points if within 5%)
                on_time_rate = ship.get('on_time_deliveries', 0) / ship['total_shipments'] * 100
                if abs(on_time_rate - perfect['on_time_percentage']) <= 5:
                    score += 10
                # Problem issues (10 points)
                if set(ship.get('problem_issues', [])) == set(perfect['problem_issues']):
                    score += 10

        # Return analysis (20 points)
        perfect_returns = {r['reason']:r for r in perfect_metrics['return_reason_analysis']}
        for ret in participant_metrics['return_reason_analysis']:
            if ret['reason'] in perfect_returns:
                perfect = perfect_returns[ret['reason']]
                # Return percentage (10 points if within 1%)
                if abs(ret['total_returns'] - perfect['return_percentage']) <= 1:
                    score += 10
                # Refund amount (10 points if within 10%)
                if abs(ret['total_refund_amount'] - perfect['average_refund_amount'])/perfect['average_refund_amount'] <= 0.1:
                    score += 10

    except Exception as e:
        logger.error(f"Error calculating score: {str(e)}")
        raise ValueError("Invalid metrics format") from e

    return min(100.0, round(score, 2))
