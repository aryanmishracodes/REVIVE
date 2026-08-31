"""
Synthetic dataset generator for REVIVE.
Generates 6,000 realistic fintech transactions with realistic correlations
and 6 pinned demo transactions for the panel presentation.
"""
import random
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Supported failure reasons
FAILURE_REASONS = [
    "INSUFFICIENT_FUNDS",
    "NETWORK_TIMEOUT",
    "AUTHENTICATION_FAILURE",
    "CARD_EXPIRED",
    "BANK_DECLINED",
    "LIMIT_EXCEEDED",
    "PAYMENT_ABANDONED",
    "UNKNOWN",
]

FAILURE_PROBABILITIES = [0.25, 0.18, 0.15, 0.12, 0.14, 0.08, 0.05, 0.03]
PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]
SEGMENTS = ["SMB", "Growth", "Enterprise", "Consumer"]


def generate_synthetic_data(num_records: int = 6000, seed: int = 42) -> Tuple[List[Dict], List[Dict]]:
    """
    Generates realistic customer and transaction datasets.
    Correlations:
    - Higher past payment success rate -> higher recovery probability
    - Higher retry_count -> lower recovery probability
    - Temporary failures (NETWORK_TIMEOUT, AUTHENTICATION_FAILURE) -> high baseline recovery
    - Permanent failures (CARD_EXPIRED) -> zero recovery on retry, recoverable via card update
    - INSUFFICIENT_FUNDS -> recoverable if near customer's usual payment hour
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1. Generate ~1,500 unique customers
    num_customers = num_records // 4
    customers = []
    customer_ids = [f"CUST-{1000 + i}" for i in range(num_customers)]

    first_names = ["Aarav", "Priya", "Rahul", "Ananya", "Rohan", "Sneha", "Aditya", "Pooja", "Vikram", "Neha",
                   "Arjun", "Divya", "Karan", "Tanvi", "Siddharth", "Meera", "Varun", "Rhea", "Nikhil", "Ishita"]
    last_names = ["Sharma", "Verma", "Patel", "Gupta", "Mehta", "Iyer", "Nair", "Reddy", "Rao", "Joshi",
                  "Malhotra", "Kapoor", "Chopra", "Bhatia", "Saxena", "Deshmukh", "Singhal", "Kulkarni"]

    for c_id in customer_ids:
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        segment = random.choices(SEGMENTS, weights=[0.45, 0.30, 0.10, 0.15])[0]
        
        # CLV based on segment
        if segment == "Enterprise":
            clv = round(random.uniform(50000, 350000), 2)
            age = random.randint(6, 48)
        elif segment == "Growth":
            clv = round(random.uniform(15000, 75000), 2)
            age = random.randint(3, 24)
        elif segment == "SMB":
            clv = round(random.uniform(3000, 25000), 2)
            age = random.randint(1, 18)
        else:
            clv = round(random.uniform(500, 8000), 2)
            age = random.randint(1, 12)

        # Historical affinity
        avg_payment_hour = random.choice([10, 11, 14, 15, 18, 19, 20, 21])
        opted_out = random.random() < 0.04  # 4% opted out of notifications

        customers.append({
            "customer_id": c_id,
            "name": f"{fname} {lname}",
            "email": f"{fname.lower()}.{lname.lower()}{random.randint(10,99)}@example.com",
            "phone": f"+9198{random.randint(10000000, 99999999)}",
            "clv": clv,
            "segment": segment,
            "subscription_age_months": age,
            "avg_payment_hour": avg_payment_hour,
            "opted_out": opted_out,
            "created_at": datetime.utcnow() - timedelta(days=age * 30),
        })

    # 2. Generate transactions
    transactions = []
    base_time = datetime.utcnow() - timedelta(days=30)

    for i in range(num_records):
        tx_id = f"TX-{100000 + i}"
        customer = random.choice(customers)
        cust_id = customer["customer_id"]

        # Failure category
        failure_reason = random.choices(FAILURE_REASONS, weights=FAILURE_PROBABILITIES)[0]
        
        # Payment method
        if failure_reason == "CARD_EXPIRED":
            payment_method = "CARD"
        else:
            payment_method = random.choices(PAYMENT_METHODS, weights=[0.55, 0.25, 0.15, 0.05])[0]

        # Transaction Amount distribution
        if customer["segment"] == "Enterprise":
            amount = round(random.uniform(8000, 45000), 2)
        elif customer["segment"] == "Growth":
            amount = round(random.uniform(2500, 12000), 2)
        elif customer["segment"] == "SMB":
            amount = round(random.uniform(800, 4500), 2)
        else:
            amount = round(random.uniform(199, 1999), 2)

        # Retry count (0 to max ceiling of 3 attempts)
        retry_count = random.choices([0, 1, 2, 3], weights=[0.48, 0.30, 0.14, 0.08])[0]

        # History metrics
        prev_payment_success_rate = round(random.uniform(0.60, 0.99), 2)
        if retry_count >= 3:
            prev_payment_success_rate = max(0.20, prev_payment_success_rate - 0.35)

        prev_recovery_success_rate = round(random.uniform(0.30, 0.85), 2)
        churn_probability = round(random.uniform(0.05, 0.60), 2)
        if retry_count >= 2:
            churn_probability = min(0.95, churn_probability + 0.25)

        tx_time = base_time + timedelta(minutes=random.randint(1, 43200))

        # Ground truth recovery simulation for training
        # Calculation of recovery outcome based on realistic probabilistic logit mechanics
        time_affinity_match = 1.0 if abs(tx_time.hour - customer["avg_payment_hour"]) <= 2 else 0.4
        
        # Continuous logit formulation
        z = -0.5
        z += (prev_payment_success_rate - 0.75) * 4.0
        z += (prev_recovery_success_rate - 0.50) * 2.5
        z += (time_affinity_match - 0.60) * 1.2
        z -= retry_count * 0.90
        z -= (churn_probability - 0.30) * 3.0
        
        # Category-specific baseline logit adjustments
        if failure_reason == "NETWORK_TIMEOUT":
            z += 1.8
        elif failure_reason == "AUTHENTICATION_FAILURE":
            z += 1.2
        elif failure_reason == "INSUFFICIENT_FUNDS":
            z += 0.4
        elif failure_reason == "CARD_EXPIRED":
            z -= 2.2
        elif failure_reason == "BANK_DECLINED":
            z -= 0.8
        elif failure_reason == "LIMIT_EXCEEDED":
            z -= 1.4
        elif failure_reason == "PAYMENT_ABANDONED":
            z -= 0.2

        import math
        recovery_prob = 1.0 / (1.0 + math.exp(-max(-6.0, min(6.0, z))))
        actual_recovered = 1 if random.random() < recovery_prob else 0
        recovered_amount = amount if actual_recovered else 0.0
        status = "RECOVERED" if actual_recovered else "FAILED"
        recovered_at = tx_time + timedelta(hours=random.randint(1, 48)) if actual_recovered else None

        transactions.append({
            "transaction_id": tx_id,
            "customer_id": cust_id,
            "amount": amount,
            "currency": "INR",
            "timestamp": tx_time,
            "payment_method": payment_method,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "status": status,
            "recovered_amount": recovered_amount,
            "recovered_at": recovered_at,
            "prev_payment_success_rate": prev_payment_success_rate,
            "prev_recovery_success_rate": prev_recovery_success_rate,
            "churn_probability": churn_probability,
            "actual_recovered": actual_recovered,  # target variable for training
        })

    # 3. Inject the 6 Pinned Demo Transactions
    demo_customers, demo_transactions = generate_demo_fixtures()
    
    # Prepend demo fixtures
    customers = demo_customers + customers
    transactions = demo_transactions + transactions

    return customers, transactions


def generate_demo_fixtures() -> Tuple[List[Dict], List[Dict]]:
    """
    Fixed demo fixtures matching the pitch narrative:
    1. TX-DEMO-001: High-Value Recoverable (>10k, requires human approval)
    2. TX-DEMO-002: Temporary Bank Failure (Network timeout, intelligent retry)
    3. TX-DEMO-003: Card Expiration (Policy blocks blind retry, sends update link)
    4. TX-DEMO-004: Low Probability Drop (3 retries, high churn, stops recovery)
    5. TX-DEMO-005: Opted-Out Customer (Policy blocks communications)
    6. TX-DEMO-006: Already Recovered (Clean success audit trail)
    """
    demo_custs = [
        {
            "customer_id": "CUST-DEMO-ENTERPRISE",
            "name": "Arunachalam Muruganantham",
            "email": "a.muruga@enterprisesolutions.in",
            "phone": "+919845012345",
            "clv": 245000.0,
            "segment": "Enterprise",
            "subscription_age_months": 36,
            "avg_payment_hour": 20,
            "opted_out": False,
            "created_at": datetime.utcnow() - timedelta(days=1095),
        },
        {
            "customer_id": "CUST-DEMO-GROWTH",
            "name": "Meera Swaminathan",
            "email": "meera.swami@fintechgrowth.io",
            "phone": "+919876543210",
            "clv": 62000.0,
            "segment": "Growth",
            "subscription_age_months": 14,
            "avg_payment_hour": 14,
            "opted_out": False,
            "created_at": datetime.utcnow() - timedelta(days=420),
        },
        {
            "customer_id": "CUST-DEMO-SMB",
            "name": "Kavita Ramachandran",
            "email": "kavita@ramachandrantraders.com",
            "phone": "+919811223344",
            "clv": 18500.0,
            "segment": "SMB",
            "subscription_age_months": 8,
            "avg_payment_hour": 19,
            "opted_out": False,
            "created_at": datetime.utcnow() - timedelta(days=240),
        },
        {
            "customer_id": "CUST-DEMO-CHURN",
            "name": "Vikramaditya Oberoi",
            "email": "v.oberoi@globalconsult.org",
            "phone": "+919944556677",
            "clv": 4500.0,
            "segment": "SMB",
            "subscription_age_months": 2,
            "avg_payment_hour": 11,
            "opted_out": False,
            "created_at": datetime.utcnow() - timedelta(days=60),
        },
        {
            "customer_id": "CUST-DEMO-OPTOUT",
            "name": "Siddharth Sengupta",
            "email": "siddharth.s@privatemail.org",
            "phone": "+919711002288",
            "clv": 32000.0,
            "segment": "Growth",
            "subscription_age_months": 18,
            "avg_payment_hour": 16,
            "opted_out": True,  # Opted out
            "created_at": datetime.utcnow() - timedelta(days=540),
        },
        {
            "customer_id": "CUST-DEMO-RECOVERED",
            "name": "Sunita Agarwal",
            "email": "sunita.agarwal@agarwaltextiles.in",
            "phone": "+919833445566",
            "clv": 84000.0,
            "segment": "Enterprise",
            "subscription_age_months": 24,
            "avg_payment_hour": 18,
            "opted_out": False,
            "created_at": datetime.utcnow() - timedelta(days=720),
        }
    ]

    now = datetime.utcnow()
    demo_txs = [
        {
            "transaction_id": "TX-DEMO-001",
            "customer_id": "CUST-DEMO-ENTERPRISE",
            "amount": 18500.0,
            "currency": "INR",
            "timestamp": now - timedelta(hours=2),
            "payment_method": "UPI",
            "failure_reason": "INSUFFICIENT_FUNDS",
            "retry_count": 0,
            "status": "FAILED",
            "recovered_amount": 0.0,
            "recovered_at": None,
            "prev_payment_success_rate": 0.96,
            "prev_recovery_success_rate": 0.88,
            "churn_probability": 0.08,
            "actual_recovered": 1,
        },
        {
            "transaction_id": "TX-DEMO-002",
            "customer_id": "CUST-DEMO-GROWTH",
            "amount": 2400.0,
            "currency": "INR",
            "timestamp": now - timedelta(hours=4),
            "payment_method": "NETBANKING",
            "failure_reason": "NETWORK_TIMEOUT",
            "retry_count": 0,
            "status": "FAILED",
            "recovered_amount": 0.0,
            "recovered_at": None,
            "prev_payment_success_rate": 0.92,
            "prev_recovery_success_rate": 0.80,
            "churn_probability": 0.12,
            "actual_recovered": 1,
        },
        {
            "transaction_id": "TX-DEMO-003",
            "customer_id": "CUST-DEMO-SMB",
            "amount": 4999.0,
            "currency": "INR",
            "timestamp": now - timedelta(hours=6),
            "payment_method": "CARD",
            "failure_reason": "CARD_EXPIRED",
            "retry_count": 1,
            "status": "FAILED",
            "recovered_amount": 0.0,
            "recovered_at": None,
            "prev_payment_success_rate": 0.85,
            "prev_recovery_success_rate": 0.70,
            "churn_probability": 0.25,
            "actual_recovered": 1,
        },
        {
            "transaction_id": "TX-DEMO-004",
            "customer_id": "CUST-DEMO-CHURN",
            "amount": 890.0,
            "currency": "INR",
            "timestamp": now - timedelta(hours=12),
            "payment_method": "UPI",
            "failure_reason": "BANK_DECLINED",
            "retry_count": 3,
            "status": "FAILED",
            "recovered_amount": 0.0,
            "recovered_at": None,
            "prev_payment_success_rate": 0.22,
            "prev_recovery_success_rate": 0.15,
            "churn_probability": 0.88,
            "actual_recovered": 0,
        },
        {
            "transaction_id": "TX-DEMO-005",
            "customer_id": "CUST-DEMO-OPTOUT",
            "amount": 1200.0,
            "currency": "INR",
            "timestamp": now - timedelta(hours=8),
            "payment_method": "CARD",
            "failure_reason": "AUTHENTICATION_FAILURE",
            "retry_count": 0,
            "status": "FAILED",
            "recovered_amount": 0.0,
            "recovered_at": None,
            "prev_payment_success_rate": 0.89,
            "prev_recovery_success_rate": 0.75,
            "churn_probability": 0.18,
            "actual_recovered": 1,
        },
        {
            "transaction_id": "TX-DEMO-006",
            "customer_id": "CUST-DEMO-RECOVERED",
            "amount": 6500.0,
            "currency": "INR",
            "timestamp": now - timedelta(days=1),
            "payment_method": "UPI",
            "failure_reason": "INSUFFICIENT_FUNDS",
            "retry_count": 1,
            "status": "RECOVERED",
            "recovered_amount": 6500.0,
            "recovered_at": now - timedelta(hours=5),
            "prev_payment_success_rate": 0.94,
            "prev_recovery_success_rate": 0.82,
            "churn_probability": 0.10,
            "actual_recovered": 1,
        }
    ]

    return demo_custs, demo_txs
