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
    assert config["provider_freeze_selected"] is False
    assert config["prompt_versions_locked"] is False
    assert config["cost_budget_approved"] is False
    assert config["execution_authorized"] is False


def test_load_freeze_inputs_uses_config_references():
    inputs = load_freeze_inputs(FREEZE_CONFIG)

    assert inputs.freeze_config["run_matrix"] == "configs/gate8/main_v1_run_matrix.yaml"
    assert inputs.freeze_config["provider_decision"] == "configs/gate8/provider_decision.yaml"
    assert inputs.run_matrix["authorized_to_run"] is False
    assert inputs.provider_decision["selected"] is False
    assert inputs.provider_decision["run_authorized"] is False


def test_default_summary_is_valid_but_not_ready():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["stage"] == "gate8g_freeze_readiness"
    assert summary["freeze_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["validation_errors"] == []
    assert "provider_unselected" in summary["blockers"]
    assert "prompt_versions_unlocked" in summary["blockers"]
    assert "cost_budget_unapproved" in summary["blockers"]
    assert "run_matrix_not_authorized" in summary["blockers"]
    assert "provider_decision_not_authorized" in summary["blockers"]


def test_summary_reports_checked_config_paths():
    inputs = load_freeze_inputs(FREEZE_CONFIG)
    summary = build_freeze_readiness_summary(inputs)

    assert summary["checked_configs"]["freeze_config"].endswith("configs/gate8/freeze_readiness.yaml")
    assert summary["checked_configs"]["run_matrix"].endswith("configs/gate8/main_v1_run_matrix.yaml")
    assert summary["checked_configs"]["provider_decision"].endswith("configs/gate8/provider_decision.yaml")


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
    assert "provider_unselected" in payload["blockers"]
