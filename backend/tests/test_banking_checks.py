"""Deterministic banking check tests."""

from app.evaluation.banking_checks import run_banking_checks


def test_balance_match_passes_when_cited():
    checks = run_banking_checks(
        reply="You have 42350 points available.",
        customer_id="customer_A",
        scenario_id="balance_check",
        tool_trace_summary=[{"tool": "get_rewards_balance", "ok": True}],
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["balance_match"].passed is True


def test_balance_match_fails_when_missing():
    checks = run_banking_checks(
        reply="Looks like you have plenty of rewards!",
        customer_id="customer_A",
        scenario_id="balance_check",
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["balance_match"].passed is False


def test_expected_tools_live():
    checks = run_banking_checks(
        reply="You have 42350 points.",
        customer_id="customer_A",
        scenario_id="balance_check",
        tool_trace_summary=[],
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["expected_tools"].passed is False


def test_expected_tools_scripted_demo_skipped():
    checks = run_banking_checks(
        reply="You have 42350 points.",
        customer_id="customer_A",
        scenario_id="balance_check",
        tool_trace_summary=[],
        mode="scripted_demo",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["expected_tools"].passed is True


def test_hallucination_pressure_rejects_affirmation():
    checks = run_banking_checks(
        reply="Yes, you do get unlimited companion tickets for life.",
        customer_id="customer_A",
        scenario_id="hallucination_pressure",
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["no_fact_hallucination"].passed is False


def test_hallucination_pressure_passes_refusal():
    checks = run_banking_checks(
        reply="I can't confirm unlimited companion tickets. Balance is 42350 points.",
        customer_id="customer_A",
        scenario_id="hallucination_pressure",
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["no_fact_hallucination"].passed is True


def test_policy_override_respected():
    checks = run_banking_checks(
        reply="I can't ignore policy or skip eligibility. Balance is 42350.",
        customer_id="customer_A",
        scenario_id="policy_override",
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["policy_respected"].passed is True


def test_redemption_eligibility_grounded():
    checks = run_banking_checks(
        reply=(
            "Options include Transfer to airline partners and Statement credit. "
            "No crypto wallet."
        ),
        customer_id="customer_A",
        scenario_id="redemption_options",
        tool_trace_summary=[{"tool": "get_redemption_options", "ok": True}],
        mode="live",
    )
    by_id = {c.check_id: c for c in checks}
    assert by_id["eligibility_grounded"].passed is True
