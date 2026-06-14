import json
import os


def load_json(file_path):
    """
    Load JSON file from disk.

    Args:
        file_path (str): Path to JSON file.

    Returns:
        dict: Parsed JSON data.
    """

    print(f"[JSON Parser] Attempting to load JSON file: {file_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        print("[JSON Parser ERROR] File does not exist.")
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("[JSON Parser] JSON loaded successfully.")
        return data

    except json.JSONDecodeError as e:
        print("[JSON Parser ERROR] Invalid JSON format.")
        raise e

    except Exception as e:
        print("[JSON Parser ERROR] Unexpected error while loading JSON.")
        raise e


def save_json(data, file_path):
    """
    Save dictionary to JSON file.

    Args:
        data (dict): Data to save.
        file_path (str): Output JSON path.
    """

    print(f"[JSON Parser] Attempting to save JSON to: {file_path}")

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print("[JSON Parser] JSON saved successfully.")

    except Exception as e:
        print("[JSON Parser ERROR] Failed to save JSON.")
        raise e