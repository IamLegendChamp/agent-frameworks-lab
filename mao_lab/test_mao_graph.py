import asyncio

from mao_lab.graph import FALLBACK, MAX_HOPS
from mao_lab.runner import run_case
from mao_lab.tools import RefundLedger

POLICY = "[C001] Returns window: unused items can be returned within 30 days of delivery.\n[C002] Refunds take 7 business days."


async def fake_lookup(keyword: str) -> str:
    return POLICY


async def empty_lookup(keyword: str) -> str:
    return ""


def run(question, order_id, lookup, decision, ledger=None, max_hops=MAX_HOPS):
    ledger = ledger or RefundLedger()
    outcome = asyncio.run(run_case("test", question, order_id, lookup, ledger, decision, max_hops))
    return outcome, ledger


def test_policy_question_needs_no_approval_and_no_refund():
    outcome, ledger = run("How many days do I have to return an item?", "", fake_lookup, None)
    assert outcome.approval_request is None
    assert outcome.values["status"] == "done"
    assert "30 days" in outcome.values["answer"]
    assert ledger.calls == 0


def test_supervisor_asks_the_policy_worker_before_anything_else():
    outcome, _ = run("Please refund my order.", "T-1", fake_lookup, "approve")
    assert outcome.values["route_log"][:2] == ["supervisor->policy_worker", "policy_worker"]


def test_refund_waits_for_a_human_and_does_nothing_until_then():
    outcome, ledger = run("Please refund my order.", "T-1", fake_lookup, None)
    assert outcome.approval_request["action"] == "issue_refund"
    assert outcome.approval_request["order_id"] == "T-1"
    assert outcome.values["status"] == "running"
    assert ledger.calls == 0


def test_approved_refund_is_issued_exactly_once():
    outcome, ledger = run("Please refund my order.", "T-1", fake_lookup, "approve")
    assert outcome.values["refund_status"] == "issued"
    assert ledger.calls == 1
    assert len(ledger.issued) == 1
    assert outcome.values["receipt"] in outcome.values["answer"]


def test_rejected_refund_moves_no_money():
    outcome, ledger = run("Please refund my order.", "T-1", fake_lookup, "reject")
    assert outcome.values["refund_status"] == "rejected"
    assert ledger.calls == 0
    assert "declined" in outcome.values["answer"]


def test_any_answer_other_than_approve_counts_as_reject():
    outcome, ledger = run("Please refund my order.", "T-1", fake_lookup, "yes please")
    assert outcome.values["refund_status"] == "rejected"
    assert ledger.calls == 0


def test_refund_request_without_an_order_id_is_not_routed_to_refunds():
    outcome, ledger = run("Please refund my order.", "", fake_lookup, None)
    assert outcome.approval_request is None
    assert ledger.calls == 0


def test_a_worker_that_never_makes_progress_is_stopped_by_the_hop_limit():
    outcome, _ = run("How many days do I have to return an item?", "", empty_lookup, None, max_hops=4)
    assert outcome.values["status"] == "hop_limit"
    assert outcome.values["hops"] == 5
    assert outcome.values["answer"] == FALLBACK


def test_the_ledger_ignores_a_repeated_idempotency_key():
    ledger = RefundLedger()
    first = asyncio.run(ledger.issue("T-1", "refund-T-1"))
    second = asyncio.run(ledger.issue("T-1", "refund-T-1"))
    assert first == second
    assert len(ledger.issued) == 1
    assert ledger.calls == 2
