import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.provider_budget_preflight import (
    EXPECTED_PROVIDER_IDS,
    build_provider_budget_preflight_summary,
    load_provider_budget_preflight_inputs,
    parse_budget_lists,
    parse_provider_candidates,
)


ROOT = Path(__file__).resolve().parents[1]
PROVIDER_CANDIDATES = ROOT / "configs" / "gate8" / "provider_candidates.yaml"
BUDGET_PREFLIGHT = ROOT / "configs" / "gate8" / "budget_preflight.yaml"
CLI = ROOT / "scripts" / "check_gate8_provider_budget_preflight.py"


def test_provider_candidates_contain_expected_models():
    inputs = load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)

    assert {candidate["id"] for candidate in inputs.provider_candidates} == EXPECTED_PROVIDER_IDS
    assert all(candidate["candidate_locked"] is True for candidate in inputs.provider_candidates)
    selected = [candidate for candidate in inputs.provider_candidates if candidate["final_selected"] is True]
    assert [candidate["id"] for candidate in selected] == ["deepseek_v4_pro"]
    assert all(candidate["authorized_to_run"] is False for candidate in inputs.provider_candidates)


def test_default_summary_reports_preflight_ready_but_execution_blocked():
    summary = build_provider_budget_preflight_summary(
        load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)
    )

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["provider_budget_preflight_ready"] is True
    assert summary["execution_authorized"] is False
    assert summary["selected_provider"] == "deepseek_v4_pro"
    assert summary["selected_candidate_id"] == "deepseek_v4_pro"
    assert summary["candidate_ids"] == ["deepseek_v4_pro", "openai_gpt_5_4"]
    assert summary["candidate_blockers"] == []
    assert summary["smoke_run_authorized"] is True
    assert summary["smoke_authorization_blockers"] == []
    assert "execution_not_authorized" in summary["execution_blockers"]
    assert "smoke_run_not_authorized" not in summary["execution_blockers"]


def test_budget_preflight_has_smoke_budget_and_deferred_main_budget():
    inputs = load_provider_budget_preflight_inputs(PROVIDER_CANDIDATES, BUDGET_PREFLIGHT)

    assert inputs.budget_preflight["smoke_run_budget_usd"] == 10
    assert inputs.budget_preflight["smoke_run_authorized"] is True
    assert inputs.budget_preflight["smoke_budget_owner_approval"] == "approved_for_smoke_run"
    assert inputs.budget_preflight["main_run_budget_usd"] == "unset_requires_later_approval"
    assert inputs.budget_preflight["retry_buffer_fraction"] == "0.30"
    assert inputs.budget_includes
    assert inputs.budget_excludes


def test_parse_provider_candidates_reads_list_of_maps(tmp_path):
    path = tmp_path / "provider_candidates.yaml"
    path.write_text(
        "\n".join(
            [
                "provider_candidates:",
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: false",
                "  - id: deepseek_v4_pro",
                "    provider: deepseek",
                "    model: deepseek-v4-pro",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: false",
            ]
        ),
        encoding="utf-8",
    )

    candidates = parse_provider_candidates(path)

    assert candidates == [
        {
            "id": "openai_gpt_5_4",
            "provider": "openai",
            "model": "gpt-5.4",
            "candidate_locked": True,
            "final_selected": False,
            "authorized_to_run": False,
        },
        {
            "id": "deepseek_v4_pro",
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
            "candidate_locked": True,
            "final_selected": False,
            "authorized_to_run": False,
        },
    ]


def test_parse_budget_lists_reads_include_exclude_sections(tmp_path):
    path = tmp_path / "budget_preflight.yaml"
    path.write_text(
        "\n".join(
            [
                "budget_includes:",
                "  - generator_input_tokens",
                "  - verifier_output_tokens",
                "budget_excludes:",
                "  - local_lexical_index_construction",
            ]
        ),
        encoding="utf-8",
    )

    includes, excludes = parse_budget_lists(path)

    assert includes == ["generator_input_tokens", "verifier_output_tokens"]
    assert excludes == ["local_lexical_index_construction"]


def test_accidental_candidate_authorization_blocks_preflight(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    candidate_text = PROVIDER_CANDIDATES.read_text(encoding="utf-8")
    candidate_text = candidate_text.replace(
        "\n".join(
            [
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: false",
            ]
        ),
        "\n".join(
            [
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: false",
                "    authorized_to_run: true",
            ]
        ),
    )
    candidates.write_text(
        candidate_text,
        encoding="utf-8",
    )
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "candidate_authorized_openai_gpt_5_4" in summary["candidate_blockers"]


def test_selected_provider_must_match_final_selected_candidate(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    text = PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace(
        "selected_provider: deepseek_v4_pro",
        "selected_provider: openai_gpt_5_4",
    )
    candidates.write_text(text, encoding="utf-8")
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "selected_provider_final_selected_mismatch" in summary["candidate_blockers"]


def test_multiple_final_selected_candidates_block_preflight(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    text = PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace(
        "\n".join(
            [
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: false",
            ]
        ),
        "\n".join(
            [
                "  - id: openai_gpt_5_4",
                "    provider: openai",
                "    model: gpt-5.4",
                "    candidate_locked: true",
                "    final_selected: true",
            ]
        ),
    )
    candidates.write_text(text, encoding="utf-8")
    budget.write_text(BUDGET_PREFLIGHT.read_text(encoding="utf-8"), encoding="utf-8")

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["provider_budget_preflight_ready"] is False
    assert "multiple_provider_candidates_final_selected" in summary["candidate_blockers"]


def test_cli_default_mode_exits_zero_and_reports_preflight_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--provider-candidates",
            str(PROVIDER_CANDIDATES),
            "--budget-preflight",
            str(BUDGET_PREFLIGHT),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["provider_budget_preflight_ready"] is True
    assert payload["execution_authorized"] is False
    assert payload["selected_provider"] == "deepseek_v4_pro"
    assert payload["selected_candidate_id"] == "deepseek_v4_pro"


def test_cli_require_ready_exits_nonzero_while_execution_is_blocked():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--provider-candidates",
            str(PROVIDER_CANDIDATES),
            "--budget-preflight",
            str(BUDGET_PREFLIGHT),
            "--require-ready",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["provider_budget_preflight_ready"] is True
    assert payload["execution_authorized"] is False


def test_cli_require_smoke_authorized_exits_zero_after_gate8o_authorization():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--provider-candidates",
            str(PROVIDER_CANDIDATES),
            "--budget-preflight",
            str(BUDGET_PREFLIGHT),
            "--require-smoke-authorized",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["provider_budget_preflight_ready"] is True
    assert payload["smoke_run_authorized"] is True
    assert payload["execution_authorized"] is False


def test_smoke_authorization_requires_deepseek_selection_and_budget_approval(tmp_path):
    candidates = tmp_path / "provider_candidates.yaml"
    budget = tmp_path / "budget_preflight.yaml"
    candidates.write_text(
        PROVIDER_CANDIDATES.read_text(encoding="utf-8").replace(
            "selected_provider: deepseek_v4_pro",
            "selected_provider: openai_gpt_5_4",
        ),
        encoding="utf-8",
    )
    budget.write_text(
        BUDGET_PREFLIGHT.read_text(encoding="utf-8").replace(
            "smoke_budget_owner_approval: approved_for_smoke_run",
            "smoke_budget_owner_approval: pending",
        ),
        encoding="utf-8",
    )

    summary = build_provider_budget_preflight_summary(load_provider_budget_preflight_inputs(candidates, budget))

    assert summary["smoke_run_authorized"] is False
    assert "smoke_selected_provider_not_deepseek_v4_pro" in summary["smoke_authorization_blockers"]
    assert "smoke_budget_owner_approval_missing" in summary["smoke_authorization_blockers"]
