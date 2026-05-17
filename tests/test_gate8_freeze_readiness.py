import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.freeze_readiness import (
    REQUIRED_FREEZE_FIELDS,
    build_freeze_readiness_summary,
    load_freeze_inputs,
    load_simple_yaml,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZE_CONFIG = ROOT / "configs" / "gate8" / "freeze_readiness.yaml"
RUN_MATRIX = ROOT / "configs" / "gate8" / "main_v1_run_matrix.yaml"
PROVIDER_DECISION = ROOT / "configs" / "gate8" / "provider_decision.yaml"
CLI = ROOT / "scripts" / "check_gate8_freeze_readiness.py"


def test_freeze_config_has_required_fields():
    config = load_simple_yaml(FREEZE_CONFIG)

    assert REQUIRED_FREEZE_FIELDS <= set(config)
    assert config["authorized_to_run"] is False
    assert config["provider_freeze_selected"] is True
    assert config["prompt_versions_locked"] is True
    assert config["generation_config_locked"] is True
    assert config["cost_budget_approved"] is False
    assert config["execution_authorized"] is False


def test_load_freeze_inputs_uses_config_references():
    inputs = load_freeze_inputs(FREEZE_CONFIG)

    assert inputs.freeze_config["run_matrix"] == "configs/gate8/main_v1_run_matrix.yaml"
    assert inputs.freeze_config["provider_decision"] == "configs/gate8/provider_decision.yaml"
    assert inputs.freeze_config["provider_evidence_registry"] == "configs/gate8/provider_evidence_registry.yaml"
    assert inputs.freeze_config["prompt_registry"] == "configs/gate8/prompt_registry.yaml"
    assert inputs.freeze_config["generation_config_registry"] == "configs/gate8/generation_config_registry.yaml"
    assert inputs.run_matrix["authorized_to_run"] is False
    assert inputs.provider_decision["selected"] is True
    assert inputs.provider_decision["provider"] == "deepseek"
    assert inputs.provider_decision["model"] == "deepseek-v4-pro"
    assert inputs.provider_decision["run_authorized"] is False
    assert inputs.provider_evidence_registry["authorized_to_run"] is False
    assert inputs.provider_evidence_registry["provider_evidence_locked"] is True
    assert inputs.provider_evidence_registry["provider_selected"] is True
    assert inputs.provider_evidence_registry["provider"] == "deepseek"
    assert inputs.provider_evidence_registry["model"] == "deepseek-v4-pro"
    assert inputs.prompt_registry["authorized_to_run"] is False
    assert inputs.generation_config_registry["authorized_to_run"] is False


def test_default_summary_is_valid_but_not_ready():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["stage"] == "gate8g_freeze_readiness"
    assert summary["freeze_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["validation_errors"] == []
    assert "provider_decision_unselected" not in summary["blockers"]
    assert "provider_freeze_unselected" not in summary["blockers"]
    assert "api_key_or_runtime_unverified" not in summary["blockers"]
    assert "prompt_versions_unlocked" not in summary["blockers"]
    assert "generation_config_unlocked" not in summary["blockers"]
    assert "prompt_config_not_frozen" not in summary["blockers"]
    assert "prompt_registry_not_locked" not in summary["blockers"]
    assert "generation_config_registry_not_locked" not in summary["blockers"]
    assert "cost_budget_unapproved" in summary["blockers"]
    assert "run_matrix_not_authorized" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]
    assert "provider_evidence_not_locked" not in summary["blockers"]
    assert "provider_evidence_provider_unselected" not in summary["blockers"]
    assert "provider_evidence_registry_not_authorized" in summary["blockers"]
    assert "provider_evidence_registry_has_blockers" in summary["blockers"]
    assert "prompt_registry_has_blockers" in summary["blockers"]
    assert "generation_config_registry_has_blockers" in summary["blockers"]
    assert "source_snapshots_not_promoted" not in summary["blockers"]


def test_summary_reports_checked_config_paths():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["checked_configs"]["freeze_config"].endswith("configs/gate8/freeze_readiness.yaml")
    assert summary["checked_configs"]["run_matrix"].endswith("configs/gate8/main_v1_run_matrix.yaml")
    assert summary["checked_configs"]["provider_decision"].endswith("configs/gate8/provider_decision.yaml")
    assert summary["checked_configs"]["provider_evidence_registry"].endswith("configs/gate8/provider_evidence_registry.yaml")
    assert summary["checked_configs"]["prompt_registry"].endswith("configs/gate8/prompt_registry.yaml")
    assert summary["checked_configs"]["generation_config_registry"].endswith("configs/gate8/generation_config_registry.yaml")


def test_referenced_metadata_lists_keep_strict_readiness_blocked(tmp_path):
    freeze_config = tmp_path / "freeze.yaml"
    run_matrix = tmp_path / "run_matrix.yaml"
    provider_decision = tmp_path / "provider.yaml"

    freeze_config.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "stage: gate8g_freeze_readiness",
                "status: readiness_in_progress",
                "authorized_to_run: true",
                f"run_matrix: {run_matrix}",
                f"provider_decision: {provider_decision}",
                "provider_freeze_selected: true",
                "provider_pricing_checked_on_run_date: true",
                "provider_docs_checked_on_run_date: true",
                "terms_checked_on_run_date: true",
                "api_key_or_runtime_available: true",
                "prompt_versions_locked: true",
                "generation_config_locked: true",
                "cost_budget_approved: true",
                "execution_card: experiments/cards/future.md",
                "reproducibility_review_complete: true",
                "execution_authorized: true",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    run_matrix.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8f_run_config_readiness",
                "authorized_to_run: true",
                "blocked_reasons:",
                "  - provider_unselected",
            ]
        ),
        encoding="utf-8",
    )
    provider_decision.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8f_provider_readiness",
                "selected: true",
                "provider: example",
                "model: example-model",
                "run_authorized: true",
                "required_future_evidence:",
                "  - official_pricing_url_checked_on_run_date",
                "disallowed_evidence:",
                "  - stale_prices_from_reports_or_old_notes",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_freeze_readiness_summary(load_freeze_inputs(freeze_config))

    assert summary["freeze_ready"] is False
    assert "run_matrix_has_blocked_reasons" in summary["blockers"]
    assert "provider_decision_has_required_future_evidence" in summary["blockers"]
    assert "provider_decision_has_disallowed_evidence" in summary["blockers"]


def test_missing_provider_evidence_slots_block_freeze_readiness(tmp_path):
    freeze_config = tmp_path / "freeze.yaml"
    run_matrix = tmp_path / "run_matrix.yaml"
    provider_decision = tmp_path / "provider.yaml"
    provider_evidence_registry = tmp_path / "provider_evidence.yaml"
    prompt_registry = tmp_path / "prompt_registry.yaml"
    generation_config_registry = tmp_path / "generation_config.yaml"

    freeze_config.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "stage: gate8g_freeze_readiness",
                "status: ready",
                "authorized_to_run: true",
                f"run_matrix: {run_matrix}",
                f"provider_decision: {provider_decision}",
                f"provider_evidence_registry: {provider_evidence_registry}",
                f"prompt_registry: {prompt_registry}",
                f"generation_config_registry: {generation_config_registry}",
                "provider_freeze_selected: true",
                "provider_pricing_checked_on_run_date: true",
                "provider_docs_checked_on_run_date: true",
                "terms_checked_on_run_date: true",
                "api_key_or_runtime_available: true",
                "prompt_versions_locked: true",
                "generation_config_locked: true",
                "cost_budget_approved: true",
                "execution_card: experiments/cards/future.md",
                "reproducibility_review_complete: true",
                "execution_authorized: true",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    run_matrix.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8f_run_config_readiness",
                "authorized_to_run: true",
                "blocked_reasons:",
            ]
        ),
        encoding="utf-8",
    )
    provider_decision.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8i_provider_decision",
                "selected: true",
                "provider: example_provider",
                "model: example_model",
                "run_authorized: true",
                "required_future_evidence:",
                "disallowed_evidence:",
            ]
        ),
        encoding="utf-8",
    )
    provider_evidence_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8i_provider_evidence_readiness",
                "authorized_to_run: true",
                "provider_evidence_locked: true",
                "provider_selected: true",
                "provider: example_provider",
                "model: example_model",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    prompt_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_prompt_config_readiness",
                "authorized_to_run: true",
                "prompt_versions_locked: true",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    generation_config_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_generation_config_readiness",
                "authorized_to_run: true",
                "generation_config_locked: true",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_freeze_readiness_summary(load_freeze_inputs(freeze_config))

    assert summary["freeze_ready"] is False
    assert "provider_evidence_not_ready" in summary["blockers"]
    assert (
        "provider_evidence_missing_slots" in summary["blockers"]
        or "provider_evidence_missing_sources" in summary["blockers"]
    )


def test_missing_reference_paths_report_validation_errors(tmp_path):
    freeze_config = tmp_path / "freeze.yaml"
    freeze_config.write_text(
        "\n".join(
            [
                "version: 1",
                "gate: gate8_main_comparison",
                "stage: gate8g_freeze_readiness",
                "status: readiness_in_progress",
                "authorized_to_run: false",
                "provider_freeze_selected: false",
                "provider_pricing_checked_on_run_date: false",
                "provider_docs_checked_on_run_date: false",
                "terms_checked_on_run_date: false",
                "api_key_or_runtime_available: false",
                "prompt_versions_locked: false",
                "generation_config_locked: false",
                "cost_budget_approved: false",
                "execution_card: unset",
                "reproducibility_review_complete: false",
                "execution_authorized: false",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_freeze_readiness_summary(load_freeze_inputs(freeze_config))

    assert summary["freeze_ready"] is False
    assert {error["field"] for error in summary["validation_errors"]} >= {
        "run_matrix",
        "provider_decision",
        "provider_evidence_registry",
        "prompt_registry",
        "generation_config_registry",
    }


def test_simple_yaml_parser_reads_top_level_scalars_and_lists(tmp_path):
    config = tmp_path / "sample.yaml"
    config.write_text(
        "\n".join(
            [
                "enabled: false",
                "name: unset",
                "count: 3",
                "blockers:",
                "  - first_blocker",
                "  - second_blocker",
                "nested:",
                "  child: ignored",
            ]
        ),
        encoding="utf-8",
    )

    parsed = load_simple_yaml(config)

    assert parsed["enabled"] is False
    assert parsed["name"] == "unset"
    assert parsed["count"] == 3
    assert parsed["blockers"] == ["first_blocker", "second_blocker"]
    assert parsed["nested"] == []


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [sys.executable, str(CLI), "--freeze-config", str(FREEZE_CONFIG)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["freeze_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["validation_errors"] == []
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [sys.executable, str(CLI), "--freeze-config", str(FREEZE_CONFIG), "--require-ready"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["freeze_ready"] is False
    assert "provider_unselected" not in payload["blockers"]
    assert "provider_evidence_not_locked" not in payload["blockers"]
    assert "cost_budget_unapproved" in payload["blockers"]
    assert "prompt_versions_unlocked" not in payload["blockers"]
    assert "generation_config_unlocked" not in payload["blockers"]
    assert "prompt_config_not_frozen" not in payload["blockers"]
    assert "main_execution_not_authorized" in payload["blockers"]
