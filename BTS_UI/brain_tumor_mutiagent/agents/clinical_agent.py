"""
Clinical Agent

This agent simulates a clinical doctor who analyzes
patient symptoms and medical history.
"""

from agents.base_agent import BaseAgent


class ClinicalAgent(BaseAgent):
    """
    Clinical reasoning agent.

    Responsible for analyzing:
    - patient symptoms
    - medical history
    - possible clinical interpretations
    """

    def __init__(self, llm_client):
        """
        Initialize Clinical Agent.

        Args:
            llm_client: LLM API client
        """

        super().__init__(
            name="ClinicalAgent",
            prompt_path="prompts/clinical_prompt.txt",
            llm_client=llm_client
        )

    def run(self, input_data):
        print("[ClinicalAgent] Starting clinical reasoning...")

        import json

        # 创建数据副本
        agent_input = dict(input_data)

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

        result = super().run(agent_input)

        print("[ClinicalAgent] Clinical reasoning completed.")

        return result