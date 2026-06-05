from agents.clinical_agent import ClinicalAgent
from agents.radiology_agent import RadiologyAgent
from agents.risk_agent import RiskAssessmentAgent
from architectures.debate_fusion_architecture import DebateFusionArchitecture

from llm.llm_client import LLMClient
import json
import os

def main():

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(cur_dir, "data/input")

    # 初始化 LLM
    llm = LLMClient()

    # 创建 agents
    clinical = ClinicalAgent(llm)
    radiology = RadiologyAgent(llm)
    risk = RiskAssessmentAgent(llm)

    agents = [clinical, radiology, risk]

    # 创建 architecture
    architecture = DebateFusionArchitecture(agents)

    # 读取两个文件
    with open(os.path.join(input_dir, "patient.json"), "r", encoding="utf-8") as f:
        patient_data = json.load(f)
    with open(os.path.join(input_dir, "tumor.json"), "r", encoding="utf-8") as f:
        tumor_data = json.load(f)

    # 构建统一 input_data，并生成字符串供模板使用
    data = {
        "patient": patient_data,
        "tumor": tumor_data
    }

    # 运行
    # 在运行 architecture.run(data) 后处理 result
    result = architecture.run(data)

    # --- 选出投票最高的诊断 ---
    agent_votes = result.get("agent_votes", {})
    if agent_votes:
        # 找到票数最高的诊断文本
        final_diagnosis = max(agent_votes.items(), key=lambda x: x[1])[0]
        # 如果你想保留置信度，可以用 votes / 总数估算
        total_votes = sum(agent_votes.values())
        final_confidence = agent_votes[final_diagnosis] / total_votes if total_votes > 0 else 1.0

        # 构建简化结果
        result = {
            "final_diagnosis": final_diagnosis,
            "final_confidence": final_confidence
        }

    # 保存文件
    output_dir = os.path.join(cur_dir, "data/output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "debate_fusion_analysis_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"Analysis saved to {output_path}")



if __name__ == "__main__":
    main()