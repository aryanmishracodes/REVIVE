"""
Deterministic Fintech Policy & Guardrail Engine.
Guarantees financial compliance, controls autonomy, and enforces human-in-the-loop approvals.
"""
from typing import Dict, Any, Tuple
from backend.core.config import settings


class PolicyEngine:
    @staticmethod
    def evaluate(
        tx_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        recommended_strategy: str,
        recovery_prob: float
    ) -> Tuple[str, str, str]:
        """
        Evaluates strict guardrails against the AI recommendation.
        Returns:
            policy_status: 'APPROVED' | 'REQUIRES_APPROVAL' | 'BLOCKED'
            rule_triggered: Human-readable policy rule code
            explanation: Plain-language compliance rationale
        """
        amount = float(tx_data.get("amount", 0.0))
        retry_count = int(tx_data.get("retry_count", 0))
        failure_reason = tx_data.get("failure_reason", "UNKNOWN")
        opted_out = customer_data.get("opted_out", False) if customer_data else False

        # Guardrail 1a: Communication Opt-Out Compliance (DND / Privacy)
        if opted_out and recommended_strategy in ["CUSTOMER_NUDGE", "PAYMENT_UPDATE"]:
            return (
                "BLOCKED",
                "RULE-01-DND-COMMUNICATION-BLOCKED",
                "Customer has explicitly opted out of marketing & automated messaging. Outbound communications are blocked by DND compliance policy."
            )

        # Guardrail 1b: DND Policy Permitted Silent Gateway Recovery
        if opted_out and recommended_strategy == "INTELLIGENT_RETRY":
            if amount < settings.HIGH_VALUE_THRESHOLD and retry_count < settings.MAX_RETRY_COUNT:
                return (
                    "APPROVED",
                    "RULE-01-SILENT-RETRY-DND-COMPLIANT",
                    "Customer is on DND. Direct communications are blocked, but backend silent payment retry is permitted without customer disruption."
                )

        # Guardrail 2: Hard Ceiling on Exhausted Retries (Anti-Spam / Gateway penalty)
        if retry_count >= settings.MAX_RETRY_COUNT and recommended_strategy == "INTELLIGENT_RETRY":
            return (
                "BLOCKED",
                "RULE-02-MAX-RETRIES-EXCEEDED",
                f"Maximum automated retries ({settings.MAX_RETRY_COUNT}) already reached. Additional gateway retries are blocked to prevent interchange fee waste."
            )

        # Guardrail 3: High-Value Transaction Human Approval Gate
        if amount >= settings.HIGH_VALUE_THRESHOLD:
            return (
                "REQUIRES_APPROVAL",
                "RULE-03-HIGH-VALUE-GATE",
                f"Transaction value (₹{amount:,.2f}) exceeds autonomous threshold (₹{settings.HIGH_VALUE_THRESHOLD:,.2f}). Requires merchant ops human sign-off."
            )

        # Guardrail 4: Expired Card Retry Prohibition
        if failure_reason == "CARD_EXPIRED" and recommended_strategy == "INTELLIGENT_RETRY":
            return (
                "BLOCKED",
                "RULE-04-INVALID-RETRY-ON-EXPIRED-CARD",
                "Blind retries on expired payment credentials have 0% mathematical probability of success. Blocked in favor of payment method update."
            )

        # Guardrail 5: Low Recovery Probability Cost-Capping
        if recovery_prob < settings.LOW_RECOVERY_PROB_THRESHOLD and retry_count >= 2:
            return (
                "APPROVED",
                "RULE-05-COST-CAP-STOP",
                f"Predicted recovery probability ({recovery_prob*100:.1f}%) is below economic viable threshold ({settings.LOW_RECOVERY_PROB_THRESHOLD*100:.0f}%). Stopping recovery."
            )

        # Default: All policy checks passed
        return (
            "APPROVED",
            "RULE-00-AUTO-APPROVED",
            "All compliance checks passed (within retry limits, under high-value threshold, compliant with communication preferences)."
        )


policy_engine = PolicyEngine()
