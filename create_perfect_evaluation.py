import json
from collections import defaultdict

# Load all sample data files
with open('sample_data/orders.json') as f:
    orders = json.load(f)
with open('sample_data/customers.json') as f:
    customers = json.load(f)
with open('sample_data/products.json') as f: 
    products = json.load(f)
with open('sample_data/shipments.json') as f:
    shipments = json.load(f)
with open('sample_data/returns.json') as f:
    returns = json.load(f)

# Convert products to dict for easy lookup
product_map = {p['id']: p for p in products}
customer_map = {c['id']: c for c in customers}

# Calculate customer spends
customer_spends = defaultdict(float)
for order in orders:
    customer_id = order['customer_id']
    product_id = order['product_id']
    quantity = order['quantity']
    price = product_map[product_id]['price']
    customer_spends[customer_id] += quantity * price

# Top 5 customers
sorted_customers = sorted(customer_spends.items(), key=lambda x: x[1], reverse=True)[:5]
top_customers = []
for cust_id, spend in sorted_customers:
    top_customers.append({
        'customer_id': cust_id,
        'customer_name': customer_map[cust_id]['name'],
        'total_spent': round(spend, 2)
    })

# Calculate product revenues
product_revenues = defaultdict(float)
for order in orders:
    product_id = order['product_id']
    quantity = order['quantity'] 
    price = product_map[product_id]['price']
    product_revenues[product_id] += quantity * price

# Top 5 products  
sorted_products = sorted(product_revenues.items(), key=lambda x: x[1], reverse=True)[:5]
top_products = []
for prod_id, revenue in sorted_products:
    top_products.append({
        'product_id': prod_id,
        'product_name': product_map[prod_id]['name'],
        'total_revenue': round(revenue, 2)
    })

# Shipping performance
carrier_performance = defaultdict(lambda: {
    'total_shipments': 0,
    'on_time_deliveries': 0,
    'problem_issues': []
})

for shipment in shipments:
    carrier = shipment['carrier']
    carrier_performance[carrier]['total_shipments'] += 1
    if shipment['status'] == 'delivered':
        carrier_performance[carrier]['on_time_deliveries'] += 1
    # In sample data, there are no issue fields - skip problem issues for now

shipping_metrics = []
for carrier, stats in carrier_performance.items():
    shipping_metrics.append({
        'carrier': carrier,
        'total_shipments': stats['total_shipments'],
        'on_time_deliveries': stats['on_time_deliveries'],
        'on_time_percentage': round(stats['on_time_deliveries'] / stats['total_shipments'] * 100, 1),
        'problem_issues': list(set(stats['problem_issues']))  # Dedupe
    })

# Return analysis
return_reasons = defaultdict(lambda: {
    'count': 0,
    'total_refund_amount': 0.0
})

for ret in returns:
    reason = ret['reason']
    return_reasons[reason]['count'] += 1
    return_reasons[reason]['total_refund_amount'] += ret['refund']

return_metrics = []
for reason, stats in return_reasons.items():
    return_metrics.append({
        'reason': reason,
        'total_returns': stats['count'],
        'return_percentage': round(stats['count'] / len(returns) * 100, 1), 
        'average_refund_amount': round(stats['total_refund_amount'] / stats['count'], 2)
    })

# Generate perfect evaluation file
perfect_evaluation = {
    'top_5_customers_by_total_spend': top_customers,
    'top_5_products_by_revenue': top_products,
    'shipping_performance_by_carrier': shipping_metrics,
    'return_reason_analysis': return_metrics
}

with open('hackathon-template/evaluator/perfect_evaluation.json', 'w') as f:
    json.dump(perfect_evaluation, f, indent=2)

print("Generated perfect_evaluation.json from sample data")
