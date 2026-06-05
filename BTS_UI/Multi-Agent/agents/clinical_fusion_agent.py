"""
Clinical Fusion Agent

This agent is designed for structured output + confidence fusion.
"""

from agents.base_agent import BaseAgent


class ClinicalFusionAgent(BaseAgent):
    """
    Clinical reasoning agent for fusion architecture.
    """

    def __init__(self, llm_client, prompt_path):
        super().__init__(
            name="ClinicalFusionAgent",
            prompt_path=prompt_path,
            llm_client=llm_client
        )

        # ✅ 用于 fusion 权重识别
        self.name = prompt_path.split("/")[-1].replace(".txt", "")

    def run(self, input_data):
        print("[ClinicalFusionAgent] Starting clinical reasoning...")

        import json
        import re

        # -----------------------------
        # 构建输入
        # -----------------------------
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

        # -----------------------------
        # 调用 LLM
        # -----------------------------
        raw_result = super().run(agent_input)

        print("[ClinicalFusionAgent] Raw output:", raw_result)

        # =============================
        # ✅ 新增：类型判断（关键修复）
        # =============================
        if isinstance(raw_result, dict):
            parsed = raw_result
        else:
            # -----------------------------
            # 提取 JSON（仅当是字符串时）
            # -----------------------------
            def extract_json(text):
                match = re.search(r"\{.*\}", text, re.DOTALL)
                return match.group() if match else None

            parsed = None

            try:
                json_str = extract_json(raw_result)
                if json_str:
                    parsed = json.loads(json_str)
            except Exception:
                pass

            # -----------------------------
            # fallback（防止解析失败）
            # -----------------------------
            if not parsed:
                parsed = {
                    "possible_diagnosis": str(raw_result),
                    "confidence": "一般"
                }

        # -----------------------------
        # ✅ 置信度映射（保持不变）
        # -----------------------------
        confidence_map = {
            "非常可靠": 0.9,
            "较可靠": 0.7,
            "一般": 0.5,
            "较不可靠": 0.3,
            "非常不可靠": 0.1
        }

        conf_text = parsed.get("confidence", "一般")
        parsed["confidence_score"] = confidence_map.get(conf_text, 0.5)

        print("[ClinicalFusionAgent] Clinical reasoning completed.")

        return parsed