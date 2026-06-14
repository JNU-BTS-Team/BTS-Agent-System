import os
import json
import argparse
from typing import Any, Dict, Optional, Tuple

try:
    import pymysql
except Exception:
    pymysql = None

from utils import Agent, get_required_api_key_env

try:
    from config import Config
except Exception:
    Config = None


REQUIRED_INPUT_FIELDS = {
    "patient_info": ["name", "age", "gender"],
    "medical_history": [
        "chief_complaint",
        "present_illness",
        "past_medical_history",
        "family_history",
        "allergy_history",
    ],
    "symptoms": [
        "headache",
        "vomiting",
        "seizure",
        "vision_problem",
        "speech_problem",
        "limb_weakness",
        "specific_remarks",
    ],
    "tumor_segmentation": [
        "labels",
        "shape",
        "ncr_net_voxel_percentage",
        "ed_voxel_percentage",
        "et_voxel_percentage",
    ],
}

REQUIRED_OUTPUT_FIELDS = [
    "tumor_location",
    "tumor_analysis",
    "severity_assessment",
    "possible_diagnosis",
    "recommendation",
    "need_doctor_review",
    "confidence",
    "confidence_reason",
    "remarks",
]


def require_config() -> None:
    if Config is None:
        raise RuntimeError(
            "未找到 config.py。若使用数据库模式，请提供 Config 配置；"
            "若使用 JSON 文件模式，请使用 --input_json（可选 --seg_json）。"
        )

def get_patient_info(patient_id: int) -> Tuple[Dict[str, Any], str]:
    require_config()
    if pymysql is None:
        raise RuntimeError("缺少 pymysql 依赖，无法使用数据库模式。")
    connection = pymysql.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
    )
    with connection.cursor() as cursor:
        sql = "SELECT * FROM patients WHERE id = %s"
        cursor.execute(sql, (patient_id,))
        result = cursor.fetchone()
    connection.close()

    if result is None:
        raise ValueError(f"数据库中未找到 patient_id={patient_id} 的记录。")

    # 将数据库字段映射到你定义的键名（参考你的 input.json）
    patient_info = {
        "patient_info": {
            "name": result["name"],
            "age": result["age"],
            "gender": result["gender"],
        },
        "medical_history": {
            "chief_complaint": result["chief_complaint"],
            "present_illness": result["present_illness"],
            "past_medical_history": result["past_history"],
            "family_history": result["family_history"],
            "allergy_history": result["allergy_history"],
        },
        "symptoms": {
            "headache": bool(result["headache"]),
            "vomiting": bool(result["vomiting"]),
            "seizure": bool(result["seizure"]),
            "vision_problem": bool(result["vision_problem"]),
            "speech_problem": bool(result["speech_problem"]),
            "limb_weakness": bool(result["limb_weakness"]),
            "specific_remarks": result["specific_remarks"],
        },
    }
    # 假设数据库中有 seg_json_path 字段，指向肿瘤分割 JSON 文件路径
    seg_json_path = result["seg_json_path"]
    return patient_info, seg_json_path

def load_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tumor_segmentation(seg_json_path: str) -> Dict[str, Any]:
    seg_data = load_json_file(seg_json_path)
    # 兼容两种输入：1) 顶层就是分割字段 2) 包含 tumor_segmentation 顶层键
    if "tumor_segmentation" in seg_data and isinstance(seg_data["tumor_segmentation"], dict):
        return seg_data["tumor_segmentation"]
    return seg_data

def validate_unified_input(unified_input: Dict[str, Any]) -> None:
    for top_key, sub_keys in REQUIRED_INPUT_FIELDS.items():
        if top_key not in unified_input or not isinstance(unified_input[top_key], dict):
            raise ValueError(f"输入缺少字段 `{top_key}` 或其不是对象。")
        for sub_key in sub_keys:
            if sub_key not in unified_input[top_key]:
                raise ValueError(f"输入缺少字段 `{top_key}.{sub_key}`。")


def build_unified_input_from_db(patient_id: int) -> Dict[str, Any]:
    patient_info, seg_json_path = get_patient_info(patient_id)
    seg_data = load_tumor_segmentation(seg_json_path)
    # 合并：将 seg_data 放入 patient_info 的 tumor_segmentation 字段
    patient_info["tumor_segmentation"] = seg_data
    validate_unified_input(patient_info)
    return patient_info


def build_unified_input_from_json(input_json_path: str, seg_json_path: Optional[str] = None) -> Dict[str, Any]:
    unified_input = load_json_file(input_json_path)

    if seg_json_path:
        unified_input["tumor_segmentation"] = load_tumor_segmentation(seg_json_path)

    validate_unified_input(unified_input)
    return unified_input

def build_prompt(unified_input: Dict[str, Any]) -> str:
    prompt = f"""
请根据以下病人信息和脑肿瘤分割数据，完成诊断分析。你必须输出严格的 JSON 格式，包含以下字段：
- tumor_location: 肿瘤位置描述，结合左右、前后、上下位置（如“左额叶”）。
- tumor_analysis: 对分割结果的整体分析，包括各区域体积意义。
- severity_assessment: 严重程度评估，只能为 "low"、"medium" 或 "high"。
- possible_diagnosis: 可能的诊断或倾向性判断。
- recommendation: 建议，如进一步检查、随访、就诊建议。
- need_doctor_review: 布尔值，是否建议医生进一步复核。
- confidence: 0~1 之间的浮点数，表示你对本次分析的置信度。
- confidence_reason: 置信度依据的简要说明。
- remarks: 其他补充说明。

以下是病例数据（JSON 格式）：
{json.dumps(unified_input, ensure_ascii=False, indent=2)}

请只输出 JSON，不要包含其他解释。
"""
    return prompt

def extract_json_object(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("未在模型输出中找到 JSON 对象。")
    return text[start : end + 1]


def normalize_output(output_data: Dict[str, Any], raw_response: str) -> Dict[str, Any]:
    normalized = {k: output_data.get(k) for k in REQUIRED_OUTPUT_FIELDS}

    severity = str(normalized.get("severity_assessment", "")).lower().strip()
    if severity not in {"low", "medium", "high"}:
        severity = "medium"
    normalized["severity_assessment"] = severity

    try:
        conf = float(normalized.get("confidence", 0.0))
    except Exception:
        conf = 0.0
    normalized["confidence"] = max(0.0, min(1.0, conf))

    normalized["need_doctor_review"] = bool(normalized.get("need_doctor_review", True))

    for key in ["tumor_location", "tumor_analysis", "possible_diagnosis", "recommendation", "confidence_reason", "remarks"]:
        val = normalized.get(key)
        normalized[key] = "" if val is None else str(val)

    if not normalized["remarks"]:
        normalized["remarks"] = raw_response[:200]

    return normalized


def run_decision(unified_input: Dict[str, Any], model_info: str) -> Dict[str, Any]:
    # 2. 初始化智能体
    doctor_agent = Agent(
        instruction="你是一位经验丰富的神经科全科医生，负责根据病人的临床信息和脑肿瘤分割数据，给出专业的诊断分析和建议。",
        role="general_practitioner",
        model_info=model_info,
    )
    doctor_agent.chat("你已就绪，请开始分析病例。")

    # 3. 准备 prompt 并调用
    prompt = build_prompt(unified_input)
    response = doctor_agent.chat(prompt)

    # 4. 解析并保存
    try:
        output_data = json.loads(extract_json_object(response))
        output_data = normalize_output(output_data, response)
    except Exception as e:
        print(f"解析失败: {e}")
        output_data = {
            "tumor_location": "解析失败",
            "tumor_analysis": "LLM 输出格式错误",
            "severity_assessment": "medium",
            "possible_diagnosis": "未知",
            "recommendation": "请人工复核",
            "need_doctor_review": True,
            "confidence": 0.0,
            "confidence_reason": f"LLM 输出无法解析: {response[:100]}",
            "remarks": response[:200],
        }

    return output_data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patient_id", type=int, default=None, help="数据库模式下使用")
    parser.add_argument("--input_json", type=str, default=None, help="统一输入 JSON 文件路径")
    parser.add_argument("--seg_json", type=str, default=None, help="肿瘤分割结果 JSON 文件路径（可选，覆盖 input_json 内的肿瘤字段）")
    parser.add_argument("--output_json", type=str, default=None, help="输出文件路径")
    parser.add_argument("--model", type=str, default="deepseek-chat", help="Agent 模型")
    parser.add_argument("--api_key", type=str, default=None, help="可选：运行时传入 API Key，会按模型写入对应环境变量")
    args = parser.parse_args()

    api_key_env = get_required_api_key_env(args.model)

    if args.api_key:
        os.environ[api_key_env] = args.api_key
        os.environ[api_key_env.upper()] = args.api_key

    if not (os.environ.get(api_key_env) or os.environ.get(api_key_env.upper())):
        raise EnvironmentError(f"缺少 {api_key_env}/{api_key_env.upper()}。请先设置环境变量或使用 --api_key 传入。")

    # 1. 构建输入（优先使用 JSON 文件模式）
    if args.input_json:
        unified_input = build_unified_input_from_json(args.input_json, args.seg_json)
        output_path = args.output_json or "output_from_json.json"
    else:
        if args.patient_id is None:
            raise ValueError("未提供 --input_json 时，必须提供 --patient_id。")
        unified_input = build_unified_input_from_db(args.patient_id)
        output_path = args.output_json or f"output_patient_{args.patient_id}.json"

    output_data = run_decision(unified_input, args.model)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"决策完成，结果已保存至 {output_path}")

if __name__ == "__main__":
    main()
