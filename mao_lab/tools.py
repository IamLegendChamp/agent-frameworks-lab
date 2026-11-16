import logging

logger = logging.getLogger(__name__)


class RefundLedger:
    """Stand-in for a payments API. Enterprise version: a real payments service that honours idempotency keys."""

    def __init__(self) -> None:
        self.issued: dict[str, str] = {}
        self.calls = 0

    async def issue(self, order_id: str, idempotency_key: str) -> str:
        """Issue a refund once per key. A repeated key returns the same receipt and moves no money."""
        self.calls += 1
        if idempotency_key not in self.issued:
            self.issued[idempotency_key] = f"RCPT-{len(self.issued) + 1:04d}"
            logger.info("refund issued")
            logger.info("  order_id=%s", order_id)
            logger.info("  receipt=%s", self.issued[idempotency_key])
        else:
            logger.info("refund repeat ignored")
            logger.info("  idempotency_key=%s", idempotency_key)
        return self.issued[idempotency_key]
