"""
LLM Client Module

This module provides a unified interface for calling large language models.
Currently uses an OpenAI-style API as placeholder.

IMPORTANT:
Replace the API_KEY and BASE_URL with real values later.
"""

from openai import OpenAI


class LLMClient:
    """
    Wrapper class for LLM API calls.
    """

    def __init__(self, model="deepseek-chat"):
        """
        Initialize LLM client.

        Args:
            model (str): Model name
        """

        print("[LLM Client] Initializing LLM client...")

        # ================================
        # API CONFIGURATION (PLACEHOLDER)
        # ================================

        self.API_KEY = "sk-320701ae1aef4b5f963cb9bf479ce253"
        # TODO: Replace with real API key

        self.BASE_URL = "https://api.deepseek.com"
        # TODO: Replace if using another provider

        self.model = model

        # Initialize client
        self.client = OpenAI(
            api_key=self.API_KEY,
            base_url=self.BASE_URL
        )

        print(f"[LLM Client] Model set to: {self.model}")
        print("[LLM Client] Initialization complete.")

    def generate(self, prompt):
        """
        Send prompt to LLM and return response.

        Args:
            prompt (str): Input prompt

        Returns:
            str: Model response
        """

        print("[LLM Client] Sending prompt to model...")

        try:

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            result = response.choices[0].message.content

            print("[LLM Client] Response received successfully.")

            return result

        except Exception as e:

            print("[LLM Client ERROR] Failed to call LLM API.")
            print(str(e))

            raise e