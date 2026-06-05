from agents.clinical_fusion_agent import ClinicalFusionAgent
from agents.radiology_agent import RadiologyAgent
from agents.risk_agent import RiskAssessmentAgent

from architectures.confidence_fusion_architecture import ConfidenceFusionArchitecture

from llm.llm_client import LLMClient
import json
import os


def main():

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(cur_dir, "data/input")

    # -----------------------------
    # 初始化 LLM
    # -----------------------------
    llm = LLMClient()

    clinical_general = ClinicalFusionAgent(llm, prompt_path="prompts/clinical_general.txt")
    clinical_conservative = ClinicalFusionAgent(llm, prompt_path="prompts/clinical_conservative.txt")
    clinical_aggressive = ClinicalFusionAgent(llm, prompt_path="prompts/clinical_aggressive.txt")

    agents = [
        clinical_general,
        clinical_conservative,
        clinical_aggressive
    ]

    # -----------------------------
    # 融合权重（同步改 key）
    # -----------------------------
    architecture = ConfidenceFusionArchitecture(
        agents,
        weights={
            "clinical_fusion": 1.5,
            "radiology": 1.0,
            "risk": 1.0
        }
    )

    # -----------------------------
    # 读取数据
    # -----------------------------
    with open(os.path.join(input_dir, "patient.json"), "r", encoding="utf-8") as f:
        patient_data = json.load(f)

    with open(os.path.join(input_dir, "tumor.json"), "r", encoding="utf-8") as f:
        tumor_data = json.load(f)

    data = {
        "patient": patient_data,
        "tumor": tumor_data
    }

    # -----------------------------
    # 运行融合
    # -----------------------------
    result = architecture.run(data)

    # -----------------------------
    # 保存
    # -----------------------------
    output_dir = os.path.join(cur_dir, "data/output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "fusion_agent_analysis_result.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"Analysis saved to {output_path}")


if __name__ == "__main__":
    main()