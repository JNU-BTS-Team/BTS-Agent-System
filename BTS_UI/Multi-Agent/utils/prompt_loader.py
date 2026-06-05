import os


def load_prompt(file_path, variables=None):
    """
    Load a prompt template and optionally replace variables.

    Args:
        file_path (str): Path to prompt template file.
        variables (dict, optional): Variables to replace in the template.

    Returns:
        str: Final prompt string.
    """

    print(f"[Prompt Loader] Attempting to load prompt file: {file_path}")

    # Check file existence
    if not os.path.exists(file_path):
        print("[Prompt Loader ERROR] Prompt file does not exist.")
        raise FileNotFoundError(f"Prompt file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        print("[Prompt Loader] Prompt file loaded successfully.")

    except Exception as e:
        print("[Prompt Loader ERROR] Failed to read prompt file.")
        raise e

    # Replace variables if provided
    if variables:
        print("[Prompt Loader] Replacing prompt variables...")

        try:
            prompt_template = prompt_template.format(**variables)
            print("[Prompt Loader] Variables replaced successfully.")

        except KeyError as e:
            print("[Prompt Loader ERROR] Missing variable in prompt template.")
            raise e

        except Exception as e:
            print("[Prompt Loader ERROR] Unexpected error during variable replacement.")
            raise e

    print("[Prompt Loader] Prompt preparation complete.")

    return prompt_template