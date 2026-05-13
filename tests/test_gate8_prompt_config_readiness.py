import json
import subprocess
import sys
from pathlib import Path

from ledger_rag_gate8.prompt_config_readiness import (
    EXPECTED_BASELINE_FAMILIES,
    build_prompt_config_readiness_summary,
    load_prompt_config_inputs,
    parse_slot_section,
)


ROOT = Path(__file__).resolve().parents[1]
PROMPT_REGISTRY = ROOT / "configs" / "gate8" / "prompt_registry.yaml"
GENERATION_CONFIG = ROOT / "configs" / "gate8" / "generation_config_registry.yaml"
CLI = ROOT / "scripts" / "check_gate8_prompt_config_readiness.py"


def test_registries_cover_all_gate5_baselines():
    inputs = load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG)

    assert {slot["baseline_family"] for slot in inputs.prompt_slots} == EXPECTED_BASELINE_FAMILIES
    assert {slot["baseline_family"] for slot in inputs.generation_slots} == EXPECTED_BASELINE_FAMILIES


def test_default_summary_is_valid_but_not_ready():
    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG))

    assert summary["gate"] == "gate8_main_comparison"
    assert summary["prompt_config_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["missing_prompt_families"] == []
    assert summary["missing_generation_families"] == []
    assert summary["validation_errors"] == []
    assert "prompt_versions_unlocked" in summary["blockers"]
    assert "generation_config_unlocked" in summary["blockers"]
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]


def test_parse_slot_section_reads_list_of_maps(tmp_path):
    registry = tmp_path / "registry.yaml"
    registry.write_text(
        "\n".join(
            [
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "  - baseline_family: ledger_validator",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "blockers:",
                "  - prompt_versions_unlocked",
            ]
        ),
        encoding="utf-8",
    )

    slots = parse_slot_section(registry, "baseline_prompt_slots")

    assert slots == [
        {
            "baseline_family": "vanilla_rag",
            "prompt_version": "unset",
            "prompt_status": "slot_reserved",
        },
        {
            "baseline_family": "ledger_validator",
            "prompt_version": "unset",
            "prompt_status": "slot_reserved",
        },
    ]


def test_missing_baseline_family_is_reported(tmp_path):
    prompt_registry = tmp_path / "prompt.yaml"
    generation_config = tmp_path / "generation.yaml"
    prompt_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_prompt_registry_readiness",
                "authorized_to_run: false",
                "prompt_versions_locked: false",
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: unset",
                "    prompt_status: slot_reserved",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    generation_config.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8h_generation_config_readiness",
                "authorized_to_run: false",
                "generation_config_locked: false",
                "baseline_generation_slots:",
                "  - baseline_family: vanilla_rag",
                "    generation_config_version: unset",
                "    config_status: slot_reserved",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(prompt_registry, generation_config))

    assert "hybrid_rag" in summary["missing_prompt_families"]
    assert "hybrid_rag" in summary["missing_generation_families"]
    assert "prompt_registry_missing_baselines" in summary["blockers"]
    assert "generation_config_missing_baselines" in summary["blockers"]


def test_cli_default_mode_exits_zero_and_reports_not_ready():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--prompt-registry",
            str(PROMPT_REGISTRY),
            "--generation-config",
            str(GENERATION_CONFIG),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)

    assert payload["prompt_config_ready"] is False
    assert payload["authorized_to_run"] is False
    assert payload["missing_prompt_families"] == []
    assert payload["missing_generation_families"] == []
    assert payload["blockers"]


def test_cli_require_ready_exits_nonzero_while_blockers_remain():
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--prompt-registry",
            str(PROMPT_REGISTRY),
            "--generation-config",
            str(GENERATION_CONFIG),
            "--require-ready",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["prompt_config_ready"] is False
    assert "prompt_versions_unlocked" in payload["blockers"]
