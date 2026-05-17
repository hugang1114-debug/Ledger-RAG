import hashlib
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
PROMPT_DIR = ROOT / "prompts" / "gate8" / "main_v1"
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
    assert "prompt_versions_unlocked" not in summary["blockers"]
    assert "generation_config_unlocked" not in summary["blockers"]
    assert "execution_not_authorized" in summary["blockers"]
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]


def test_candidate_prompt_files_exist_for_all_baselines():
    expected_files = {f"{family}.md" for family in EXPECTED_BASELINE_FAMILIES}

    assert {path.name for path in PROMPT_DIR.glob("*.md")} == expected_files


def test_default_summary_reports_candidate_ready_but_final_not_ready():
    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG))

    assert summary["prompt_config_frozen_ready"] is True
    assert summary["prompt_config_ready"] is False
    assert summary["authorized_to_run"] is False
    assert summary["freeze_blockers"] == []
    assert "prompt_registry_not_authorized" in summary["blockers"]
    assert "generation_config_registry_not_authorized" in summary["blockers"]


def test_gate8s_freezes_final_prompt_and_generation_slots_without_authorizing_runs():
    inputs = load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG)
    summary = build_prompt_config_readiness_summary(inputs)

    assert inputs.prompt_registry["stage"] == "gate8s_main_prompt_config_freeze"
    assert inputs.generation_config["stage"] == "gate8s_main_generation_config_freeze"
    assert inputs.prompt_registry["prompt_versions_locked"] is True
    assert inputs.prompt_registry["prompt_text_frozen"] is True
    assert inputs.generation_config["generation_config_locked"] is True
    assert inputs.generation_config["shared_answer_style_locked"] is True
    assert inputs.generation_config["shared_evidence_budget_locked"] is True
    assert {slot["prompt_status"] for slot in inputs.prompt_slots} == {"final_locked"}
    assert {slot["config_status"] for slot in inputs.generation_slots} == {"final_locked"}
    assert {slot["authorized_to_run"] for slot in inputs.prompt_slots} == {False}
    assert {slot["authorized_to_run"] for slot in inputs.generation_slots} == {False}
    assert summary["prompt_config_frozen_ready"] is True
    assert summary["prompt_config_ready"] is False


def test_prompt_hashes_match_registry_entries():
    inputs = load_prompt_config_inputs(PROMPT_REGISTRY, GENERATION_CONFIG)

    for slot in inputs.prompt_slots:
        family = slot.get("baseline_family", "unknown")
        prompt_file = slot.get("prompt_file")
        prompt_sha256 = slot.get("prompt_sha256")

        assert prompt_file, f"missing prompt_file for {family}"
        assert prompt_file != "unset", f"prompt_file unset for {family}"
        assert prompt_sha256, f"missing prompt_sha256 for {family}"

        prompt_path = (ROOT / prompt_file).resolve()
        assert prompt_path.is_relative_to(PROMPT_DIR.resolve()), f"prompt_file outside prompt dir for {family}: {prompt_file}"
        assert prompt_path.name == f"{family}.md", f"prompt_file name mismatch for {family}: {prompt_file}"
        assert prompt_path.exists(), f"missing prompt file for {family}: {prompt_file}"

        digest = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
        assert prompt_sha256 == digest, f"prompt_sha256 mismatch for {family}: {prompt_file}"


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


def test_candidate_readiness_rejects_accidental_top_level_authorization(tmp_path):
    prompt_registry = tmp_path / "prompt.yaml"
    generation_config = tmp_path / "generation.yaml"
    prompt_file = tmp_path / "vanilla_rag.md"
    prompt_file.write_text("Safe prompt text with no unresolved markers.", encoding="utf-8")
    digest = hashlib.sha256(prompt_file.read_bytes()).hexdigest()

    prompt_registry.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8l_prompt_candidate_freeze",
                "authorized_to_run: true",
                "prompt_versions_locked: false",
                "prompt_text_frozen: false",
                "candidate_prompt_versions_locked: true",
                "candidate_prompt_text_frozen: true",
                "baseline_prompt_slots:",
                "  - baseline_family: vanilla_rag",
                "    prompt_version: gate8l_vanilla_rag_v1",
                "    prompt_status: candidate_locked",
                f"    prompt_file: {prompt_file}",
                f"    prompt_sha256: {digest}",
                "    authorized_to_run: false",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )
    generation_config.write_text(
        "\n".join(
            [
                "gate: gate8_main_comparison",
                "stage: gate8l_generation_config_candidate_freeze",
                "authorized_to_run: false",
                "generation_config_locked: false",
                "candidate_generation_config_locked: true",
                "candidate_shared_answer_style_locked: true",
                "candidate_shared_evidence_budget_locked: true",
                "shared_constraints:",
                "  answer_style: global_answer_with_atomic_claims",
                "  citation_granularity: evidence_item_or_ledger_span",
                "  max_evidence_items: 8",
                "  max_atomic_claims: 8",
                "  temperature: 0",
                "  max_output_tokens: 2048",
                "baseline_generation_slots:",
                "  - baseline_family: vanilla_rag",
                "    generation_config_version: gate8l_vanilla_rag_generation_v1",
                "    config_status: candidate_locked",
                "    authorized_to_run: false",
                "blockers:",
            ]
        ),
        encoding="utf-8",
    )

    summary = build_prompt_config_readiness_summary(load_prompt_config_inputs(prompt_registry, generation_config))

    assert summary["prompt_config_candidate_ready"] is False
    assert "prompt_registry_accidentally_authorized" in summary["candidate_blockers"]


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
    assert payload["prompt_config_frozen_ready"] is True
    assert "prompt_versions_unlocked" not in payload["blockers"]
    assert "generation_config_unlocked" not in payload["blockers"]
    assert "execution_not_authorized" in payload["blockers"]
