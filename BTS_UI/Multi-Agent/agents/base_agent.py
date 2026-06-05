import json
import os


class BaseAgent:
    """
    Base class for all agents.
    """

    def __init__(self, name, prompt_path, llm_client, max_output_chars=2000):
        self.name = name
        self.prompt_path = prompt_path
        self.llm_client = llm_client
        self.max_output_chars = max_output_chars

        print(f"[Agent Init] {self.name} initialized.")

    # ===============================
    # Prompt construction
    # ===============================

    def build_prompt(self, input_data):
        print(f"[{self.name}] Building prompt...")
        prompt_path = self.prompt_path
        if not os.path.isabs(prompt_path):
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            prompt_path = os.path.join(root_dir, prompt_path)
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()
        if input_data:
            prompt_template = prompt_template.format(**input_data)
        return prompt_template

    # ===============================
    # LLM call
    # ===============================

    def call_llm(self, prompt):

        print(f"[{self.name}] Sending prompt to LLM...")

        response = self.llm_client.generate(prompt)

        # 防止输出过长
        if len(response) > self.max_output_chars:

            print(f"[{self.name}] Output truncated.")

            response = response[:self.max_output_chars]

        return response

    # ===============================
    # Output parsing
    # ===============================

    def parse_output(self, response):

        """
        Try to parse JSON output.
        If failed, return raw text.
        """
        if not isinstance(response, str):
            response = str(response)
        response = response.strip()
        if response.startswith("```"):
            response = response.strip("`").strip()
            if response.startswith("json"):
                response = response[4:].strip()
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 2:
                response = parts[1].replace("json", "").strip()

        try:
            result = json.loads(response)
            print(f"[{self.name}] JSON output parsed.")
            return result
        except Exception:
            print(f"[{self.name}] Non-JSON output.")
            return {"text_output": response}

    # ===============================
    # Main agent execution
    # ===============================

    def run(self, input_data):

        print(f"\n===== {self.name} Execution Started =====")

        prompt = self.build_prompt(input_data)

        response = self.call_llm(prompt)

        result = self.parse_output(response)

        result = self.normalize_output(result)

        print(f"===== {self.name} Execution Completed =====\n")

        return result

    def normalize_output(self, result):
        """
        Normalize LLM output to unified schema.
        """

        # 如果不是 dict，直接包装
        if not isinstance(result, dict):
            return {"text_output": str(result)}

        # ===== 统一字段 schema =====
        required_keys = [
            "tumor_location",
            "tumor_analysis",
            "severity_assessment",
            "possible_diagnosis",
            "recommendation",
            "need_doctor_review",
            "confidence",
            "confidence_reason",
            "remarks"
        ]

        for key in required_keys:
            if key not in result:
                result[key] = None

        # ===== 类型标准化 =====

        # possible_diagnosis → string
        if isinstance(result["possible_diagnosis"], list):
            result["possible_diagnosis"] = "\n".join(result["possible_diagnosis"])

        # need_doctor_review → bool
        if not isinstance(result["need_doctor_review"], bool):
            result["need_doctor_review"] = bool(result["need_doctor_review"])

        severity = str(result.get("severity_assessment") or "").lower().strip()
        if severity not in {"low", "medium", "high"}:
            result["severity_assessment"] = "medium"

        try:
            result["confidence"] = float(result["confidence"])
        except Exception:
            result["confidence"] = 0.0
        result["confidence"] = max(0.0, min(1.0, result["confidence"]))

        return result
