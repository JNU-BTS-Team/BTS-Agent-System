## 对于智能体的输入输出流：
# 输入json格式:
{
  "patient_info": {
    "name": "None",                  // 患者姓名
    "age": 0,                        // 患者年龄
    "gender": "male"                 // 患者性别
  },
  "medical_history": {
    "chief_complaint": "None",       // 主诉：患者最主要的不适，如“头痛2周”
    "present_illness": "None",       // 现病史：本次发病经过
    "past_medical_history": "None",  // 既往病史：如高血压、糖尿病、手术史等
    "family_history": "None",        // 家族史：家族中是否有类似疾病
    "allergy_history": "None"        // 过敏史：是否对药物或食物过敏
  },
  "symptoms": {
    "headache": false,               // 是否头痛
    "vomiting": false,               // 是否呕吐
    "seizure": false,                // 是否有癫痫/抽搐
    "vision_problem": false,         // 是否有视力问题
    "speech_problem": false,         // 是否有语言障碍
    "limb_weakness": false           // 是否有肢体无力
    "specific_remarks": "None"       // 备注患者的其他特殊情况
  },
  "tumor_segmentation": {
    "file_type": "numpy_array",      // 分割结果的数据类型，这里是NumPy数组, 大小为[128, 160, 192]
    "labels": {
      "0"; "normal",                 // 0代表正常区域(背景+脑部影像)
      "1": "NCR/NET",                // 1代表坏死/非增强肿瘤核心
      "2": "ED",                     // 2代表水肿区域
      "4": "ET"                      // 4代表增强肿瘤区域
                                     // PS: 1+2+3构成了脑部肿瘤, 但是论严重程度来说: ET > NCR/NET > ED
    },
    "shape": [128, 160, 192],        // NumPy数组形状
    "ncr_net_voxel_percentage": 0,   // NCR/NET区域体素占整体脑部区域的比例
    "ed_voxel_percentage": 0,        // ED区域体素占整体脑部区域的比例
    "et_voxel_percentage": 0,        // ET区域体素占整体脑部区域的比例
  }
}


# 输出json格式:
{
  "tumor_location": "None",                  // 肿瘤位置描述，如“left frontal lobe”
  "tumor_analysis": "None",                  // 对分割结果的整体分析
  "severity_assessment": "None",             // 严重程度评估，如“low/medium/high”
  "possible_diagnosis": "None",              // 可能的诊断或倾向性判断
  "recommendation": "None",                  // 建议，如进一步检查、随访、就诊建议
  "need_doctor_review": false,               // 是否建议医生进一步复核
  "confidence": 0.0,                         // 智能体对本次分析结果的置信度，范围0~1
  "confidence_reason": "None",               // 置信度依据
  "remarks": "None"                          // 其他补充说明
}