from fastapi import FastAPI, Header
from pydantic import BaseModel
import random
import uuid
from datetime import datetime

app = FastAPI(
    title="ATLAS-OPS",
    description="Autonomous AI Payment Operations Platform",
    version="1.0.0"
)

# ----------------------------
# Fake In-Memory Storage
# ----------------------------
transactions = {}
gateway_health = {
    "stripe": {"status": "healthy", "failure_rate": 0.1},
    "razorpay": {"status": "healthy", "failure_rate": 0.05}
}

# ----------------------------
# Request Schema
# ----------------------------
class TransactionRequest(BaseModel):
    amount: float
    email_domain: str = "gmail.com"
    device_type: str = "desktop"


# ----------------------------
# Core Logic (Fake but Smart)
# ----------------------------
def fraud_score(txn: TransactionRequest):
    score = random.uniform(0, 1)
    if txn.amount > 1000:
        score += 0.2
    return round(min(score, 1.0), 3)


def select_gateway():
    # choose healthiest gateway
    return min(gateway_health, key=lambda g: gateway_health[g]["failure_rate"])


def simulate_gateway(gateway):
    fail_chance = gateway_health[gateway]["failure_rate"]
    return random.random() > fail_chance


# ----------------------------
# Routes
# ----------------------------
@app.get("/")
def root():
    return {
        "system": "ATLAS-OPS",
        "status": "running",
        "timestamp": datetime.utcnow()
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "services": {
            "api": "up",
            "ml": "active",
            "routing": "active"
        }
    }


@app.post("/v1/transaction/process")
def process_transaction(
    txn: TransactionRequest,
    idempotency_key: str = Header(default=None)
):
    txn_id = str(uuid.uuid4())

    score = fraud_score(txn)

    # Fraud check
    if score > 0.75:
        result = {
            "transaction_id": txn_id,
            "status": "REJECTED",
            "fraud_score": score,
            "reason": "High fraud risk detected"
        }
        transactions[txn_id] = result
        return result

    # Routing
    gateway = select_gateway()

    # Execute
    success = simulate_gateway(gateway)

    if success:
        result = {
            "transaction_id": txn_id,
            "status": "APPROVED",
            "gateway": gateway,
            "fraud_score": score,
            "amount": txn.amount,
            "timestamp": datetime.utcnow()
        }
    else:
        result = {
            "transaction_id": txn_id,
            "status": "FAILED",
            "gateway": gateway,
            "fraud_score": score,
            "reason": "Gateway failure",
            "retry_suggested": True
        }

    transactions[txn_id] = result
    return result


@app.get("/v1/transaction/{txn_id}")
def get_transaction(txn_id: str):
    return transactions.get(txn_id, {"error": "Transaction not found"})


@app.get("/v1/gateways/health")
def gateways():
    return gateway_health


@app.post("/v1/simulate/outage")
def simulate_outage(gateway: str, failure_rate: float):
    if gateway in gateway_health:
        gateway_health[gateway]["failure_rate"] = failure_rate
        gateway_health[gateway]["status"] = "degraded" if failure_rate > 0.5 else "healthy"
        return {"message": f"{gateway} updated", "failure_rate": failure_rate}
    return {"error": "Invalid gateway"}


@app.get("/v1/transaction/{txn_id}/explain")
def explain(txn_id: str):
    txn = transactions.get(txn_id)
    if not txn:
        return {"error": "Transaction not found"}

    if txn["status"] == "FAILED":
        return {
            "transaction_id": txn_id,
            "explanation": "Transaction failed due to gateway instability. Retry recommended."
        }

    if txn["status"] == "REJECTED":
        return {
            "transaction_id": txn_id,
            "explanation": "Transaction blocked due to high fraud probability."
        }

    return {
        "transaction_id": txn_id,
        "explanation": "Transaction processed successfully with low risk."
    }