import json
from utils.prompt_loader import load_prompt


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

        prompt = load_prompt(
            self.prompt_path,
            variables=input_data
        )

        return prompt

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
        # 去掉 markdown
        if "```" in response:
            response = response.split("```")[1]
            response = response.replace("json", "").strip()

        try:

            result = json.loads(response)

            print(f"[{self.name}] JSON output parsed.")

            return result

        except:

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

        print(f"===== {self.name} Execution Completed =====\n")

        return result

import json
from utils.prompt_loader import load_prompt


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

        prompt = load_prompt(
            self.prompt_path,
            variables=input_data
        )

        return prompt

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
        # 去掉 markdown
        if "```" in response:
            response = response.split("```")[1]
            response = response.replace("json", "").strip()

        try:

            result = json.loads(response)

            print(f"[{self.name}] JSON output parsed.")

            return result

        except:

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

        # confidence → float
        try:
            result["confidence"] = float(result["confidence"])
        except:
            result["confidence"] = 0.0

        return result