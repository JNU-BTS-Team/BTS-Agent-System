"""
Radiology Agent

This agent simulates a neuroradiologist who analyzes
brain MRI/CT imaging results.
"""

from agents.base_agent import BaseAgent


class RadiologyAgent(BaseAgent):
    """
    Radiology reasoning agent.

    Responsible for analyzing:
    - MRI findings
    - CT findings
    - tumor location and characteristics
    """

    def __init__(self, llm_client):

        super().__init__(
            name="RadiologyAgent",
            prompt_path="prompts/radiology_prompt.txt",
            llm_client=llm_client
        )

    def run(self, input_data):

        print("[RadiologyAgent] Starting radiology analysis...")

        import json

        # 创建输入数据副本，避免修改原始 input_data
        agent_input = dict(input_data)

        # 转换 JSON 字符串
        agent_input["patient_json"] = json.dumps(
            input_data["patient"],
            indent=2,
            ensure_ascii=False
        )

        agent_input["tumor_json"] = json.dumps(
            input_data["tumor"],
            indent=2,
            ensure_ascii=False
        )

        # 调用 BaseAgent
        result = super().run(agent_input)

        print("[RadiologyAgent] Radiology analysis completed.")

        return result