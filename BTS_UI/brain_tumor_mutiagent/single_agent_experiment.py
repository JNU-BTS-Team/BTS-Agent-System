import os
import json
from agents.clinical_agent import ClinicalAgent
from architectures.single_architecture import SingleArchitecture
from llm.llm_client import LLMClient

def main():
    # 初始化
    llm = LLMClient()
    clinical_agent = ClinicalAgent(llm)
    architecture = SingleArchitecture(clinical_agent)

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(cur_dir, "data/input")

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
    result = architecture.run(data)

    # 保存输出
    output_dir = os.path.join(cur_dir, "data/output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "single_agent_analysis_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4,ensure_ascii=False)

    print(f"Analysis saved to {output_path}")

if __name__ == "__main__":
    main()