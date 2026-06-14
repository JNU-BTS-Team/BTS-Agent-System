"""
Risk Assessment Agent

This agent evaluates the risk level of a suspected tumor
based on clinical and imaging information.
"""

from agents.base_agent import BaseAgent


class RiskAssessmentAgent(BaseAgent):
    """
    Risk evaluation agent.

    Responsible for:
    - malignancy probability
    - patient risk level
    - urgency of treatment
    """

    def __init__(self, llm_client):

        super().__init__(
            name="RiskAssessmentAgent",
            prompt_path="prompts/risk_prompt.txt",
            llm_client=llm_client
        )

    def run(self, input_data):

        print("[RiskAssessmentAgent] Starting risk evaluation...")

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

        print("[RiskAssessmentAgent] Risk evaluation completed.")

        return result