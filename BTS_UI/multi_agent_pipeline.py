import json
import os
import sys
from typing import Any, Dict, List, Optional

from utils import create_openai_compatible_client, get_required_api_key_env

REQUIRED_OUTPUT_FIELDS = [
    "tumor_location",
    "tumor_analysis",
    "severity_assessment",
    "possible_diagnosis",
    "recommendation",
    "need_doctor_review",
    "confidence",
    "confidence_reason",
    "remarks",
]


def _normalize_output(output_data: Dict[str, Any], raw_response: str, extras: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    normalized = {k: output_data.get(k) for k in REQUIRED_OUTPUT_FIELDS}

    severity = str(normalized.get("severity_assessment", "")).lower().strip()
    if severity not in {"low", "medium", "high"}:
        severity = "medium"
    normalized["severity_assessment"] = severity

    conf_val = normalized.get("confidence", 0.0)
    if isinstance(conf_val, str):
        mapping = {
            "非常不可靠": 0.1,
            "不太可靠": 0.3,
            "比较可靠": 0.55,
            "可靠": 0.75,
            "非常可靠": 0.9,
        }
        conf_val = mapping.get(conf_val.strip(), conf_val)
    try:
        conf = float(conf_val)
    except Exception:
        conf = 0.0
    normalized["confidence"] = max(0.0, min(1.0, conf))

    ndr = normalized.get("need_doctor_review", True)
    normalized["need_doctor_review"] = bool(ndr)

    for key in ["tumor_location", "tumor_analysis", "possible_diagnosis", "recommendation", "confidence_reason", "remarks"]:
        val = normalized.get(key)
        normalized[key] = "" if val is None else str(val)

    if not normalized["remarks"]:
        normalized["remarks"] = (raw_response or "")[:200]

    if extras:
        normalized.update(extras)

    return normalized


def _ensure_multi_agent_path() -> str:
    base_dir = os.path.dirname(__file__)
    multi_dir = os.path.join(base_dir, "Multi-Agent")
    if not os.path.isdir(multi_dir):
        raise FileNotFoundError(f"未找到 Multi-Agent 目录: {multi_dir}")
    if multi_dir not in sys.path:
        sys.path.insert(0, multi_dir)
    return multi_dir


class _LLMClientAdapter:
    def __init__(self, model_info: str):
        self.client, self.model = create_openai_compatible_client(model_info)

    def generate(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content


def _build_multi_agent_input(unified_input: Dict[str, Any]) -> Dict[str, Any]:
    patient = {
        "patient_info": unified_input.get("patient_info") or {},
        "medical_history": unified_input.get("medical_history") or {},
        "symptoms": unified_input.get("symptoms") or {},
        "diagnosis_record": unified_input.get("diagnosis_record") or {},
    }
    tumor = unified_input.get("tumor_segmentation") or {}
    return {"patient": patient, "tumor": tumor}


def run_decision(
    unified_input: Dict[str, Any],
    model_info: str,
    strategy: Optional[str] = None,
    trace: bool = False,
) -> Dict[str, Any]:
    _ensure_multi_agent_path()
    strategy = (strategy or os.environ.get("MULTI_AGENT_STRATEGY") or "debate").strip().lower()

    api_key_env = get_required_api_key_env(model_info)
    if api_key_env not in os.environ or not os.environ.get(api_key_env):
        raise EnvironmentError(f"缺少 {api_key_env} 环境变量。")

    llm_client = _LLMClientAdapter(model_info)

    from agents.clinical_agent import ClinicalAgent
    from agents.radiology_agent import RadiologyAgent
    from agents.risk_agent import RiskAssessmentAgent

    input_data = _build_multi_agent_input(unified_input)

    agents = [
        ClinicalAgent(llm_client),
        RadiologyAgent(llm_client),
        RiskAssessmentAgent(llm_client),
    ]

    raw = ""
    result: Dict[str, Any] = {}

    if strategy in {"single", "clinical"}:
        raw_result = agents[0].run(input_data)
        raw = json.dumps(raw_result, ensure_ascii=False)
        result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
        return _normalize_output(result, raw)

    if strategy in {"voting", "vote"}:
        from architectures.voting_architecture import VotingArchitecture

        arch = VotingArchitecture(agents)
        raw_result = arch.run(input_data)
        raw = json.dumps(raw_result, ensure_ascii=False)
        result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
        return _normalize_output(result, raw)

    if strategy in {"debate", "debate_fusion"}:
        from architectures.debate_fusion_architecture import DebateFusionArchitecture

        arch = DebateFusionArchitecture(agents)
        if trace:
            raw_result, debate_trace = arch.run(input_data, return_trace=True)
            raw = json.dumps(debate_trace, ensure_ascii=False)
            result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
            return _normalize_output(result, raw, extras={"debate_trace": debate_trace})
        raw_result = arch.run(input_data)
        raw = json.dumps(raw_result, ensure_ascii=False)
        result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
        return _normalize_output(result, raw)

    if strategy in {"confidence", "confidence_fusion"}:
        from architectures.confidence_fusion_architecture import ConfidenceFusionArchitecture

        arch = ConfidenceFusionArchitecture(agents)
        raw_result = arch.run(input_data)
        raw = json.dumps(raw_result, ensure_ascii=False)
        result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
        return _normalize_output(result, raw)

    from architectures.voting_architecture import VotingArchitecture

    arch = VotingArchitecture(agents)
    raw_result = arch.run(input_data)
    raw = json.dumps(raw_result, ensure_ascii=False)
    result = raw_result if isinstance(raw_result, dict) else {"remarks": str(raw_result)}
    return _normalize_output(result, raw)
