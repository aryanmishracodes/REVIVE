"""
Deterministic Expert System Fallback Engine.
Produces high-quality, explainable, context-aware recovery decisions without external LLM latency or downtime.
"""
from typing import Dict, Any, Tuple


class FallbackEngine:
    @staticmethod
    def generate_strategy_and_reasoning(
        tx_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        recovery_prob: float,
        breakdown: list
    ) -> Tuple[str, str, float]:
        """
        Determines the optimal recovery strategy and plain-language explanation.
        Strategies:
        - INTELLIGENT_RETRY
        - CUSTOMER_NUDGE
        - PAYMENT_UPDATE
        - ESCALATION
        - STOP_RECOVERY
        """
        failure_reason = tx_data.get("failure_reason", "UNKNOWN")
        amount = float(tx_data.get("amount", 0.0))
        retry_count = int(tx_data.get("retry_count", 0))
        prev_pay_rate = float(tx_data.get("prev_payment_success_rate", 0.85))
        churn_prob = float(tx_data.get("churn_probability", 0.15))
        cust_name = customer_data.get("name", "Customer") if customer_data else "Customer"
        avg_hour = customer_data.get("avg_payment_hour", 18) if customer_data else 18
        opted_out = customer_data.get("opted_out", False) if customer_data else False

        # Format hour nicely
        time_str = f"{avg_hour % 12 or 12}:00 {'PM' if avg_hour >= 12 else 'AM'}"

        # Strategy 1: Permanent Card Expired -> PAYMENT_UPDATE
        if failure_reason == "CARD_EXPIRED":
            strategy = "PAYMENT_UPDATE"
            confidence = 0.95
            reason = (
                f"The transaction failed due to an expired card. Blind retries would fail 100% of the time and cause unnecessary gateway fees. "
                f"REVIVE selected a payment update flow to request updated card details from {cust_name}, while preserving subscriber goodwill."
            )

        # Strategy 2: Low probability + exhausted attempts -> STOP_RECOVERY
        elif retry_count >= 3 or (recovery_prob < 0.15 and retry_count >= 2):
            strategy = "STOP_RECOVERY"
            confidence = 0.92
            reason = (
                f"Customer has exhausted {retry_count} prior retries with a low predicted recovery likelihood ({recovery_prob*100:.1f}%) "
                f"and high churn risk ({churn_prob*100:.0f}%). Continued attempts would incur interchange penalties. Halting further automated attempts to protect merchant margins."
            )

        # Strategy 3: High Value + Bank Decline / Limit Exceeded -> ESCALATION
        elif amount >= 10000.0 and failure_reason in ["BANK_DECLINED", "LIMIT_EXCEEDED"]:
            strategy = "ESCALATION"
            confidence = 0.90
            reason = (
                f"High-value payment of ₹{amount:,.2f} failed due to {failure_reason.replace('_', ' ').title()}. "
                f"Given the account CLV and bank risk classification, a direct merchant ops touchpoint is prioritized over passive retries."
            )

        # Strategy 4: High past success + Network Timeout / Insufficient funds -> INTELLIGENT_RETRY
        elif failure_reason in ["NETWORK_TIMEOUT", "AUTHENTICATION_FAILURE"] or (failure_reason == "INSUFFICIENT_FUNDS" and prev_pay_rate > 0.85):
            strategy = "INTELLIGENT_RETRY"
            confidence = 0.88
            reason = (
                f"Customer has an established payment track record ({prev_pay_rate*100:.0f}% success rate). "
                f"The failure was classified as temporary ({failure_reason.replace('_', ' ').title()}). "
                f"REVIVE scheduled an intelligent retry during the customer's historical success window at approximately {time_str} to maximize auto-capture."
            )

        # Strategy 5: Customer Nudge for Abandoned / General Insufficient Funds
        else:
            if opted_out:
                strategy = "INTELLIGENT_RETRY"
                confidence = 0.82
                reason = (
                    f"Customer has opted out of communication channels. REVIVE reverted from a nudge to a low-frequency silent retry at optimal time ({time_str})."
                )
            else:
                strategy = "CUSTOMER_NUDGE"
                confidence = 0.86
                reason = (
                    f"Transaction failed due to {failure_reason.replace('_', ' ').title()}. A personalized recovery message with a 1-click payment link "
                    f"was selected to resolve friction without waiting for automated batch retries."
                )

        return strategy, reason, confidence


fallback_engine = FallbackEngine()
