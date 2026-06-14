import json
import numpy as np
import nibabel as nib


def extract_tumor_segmentation_info(mask_path):
    """
    从本地 .nii / .nii.gz 分割文件中提取脑肿瘤分割信息
    标签定义:
        0 -> background
        1 -> NCR/NET
        2 -> ED
        4 -> ET
    """

    # 读取 nii 文件
    nii = nib.load(mask_path)
    data = nii.get_fdata().astype(np.uint8)

    # 基础信息
    shape = list(data.shape)
    affine = nii.affine
    header = nii.header

    # 体素间距（mm）
    voxel_spacing = header.get_zooms()[:3]
    voxel_volume_mm3 = float(voxel_spacing[0] * voxel_spacing[1] * voxel_spacing[2])

    # 各类体素数量
    ncr_net_voxel_count = int(np.sum(data == 1))
    ed_voxel_count = int(np.sum(data == 2))
    et_voxel_count = int(np.sum(data == 4))
    tumor_voxel_count = ncr_net_voxel_count + ed_voxel_count + et_voxel_count

    # 百分比（按整个 3D 体积算）
    total_voxel_count = int(data.size)
    ncr_net_voxel_percentage = ncr_net_voxel_count / total_voxel_count
    ed_voxel_percentage = ed_voxel_count / total_voxel_count
    et_voxel_percentage = et_voxel_count / total_voxel_count
    tumor_voxel_percentage = tumor_voxel_count / total_voxel_count

    # 肿瘤内部组成比例（按肿瘤总体积算）
    if tumor_voxel_count > 0:
        ncr_net_ratio_in_tumor = ncr_net_voxel_count / tumor_voxel_count
        ed_ratio_in_tumor = ed_voxel_count / tumor_voxel_count
        et_ratio_in_tumor = et_voxel_count / tumor_voxel_count
    else:
        ncr_net_ratio_in_tumor = 0.0
        ed_ratio_in_tumor = 0.0
        et_ratio_in_tumor = 0.0

    has_ncr_net = ncr_net_voxel_count > 0
    has_ed = ed_voxel_count > 0
    has_et = et_voxel_count > 0

    # 7. 肿瘤整体区域（1/2/4）
    tumor_mask = np.isin(data, [1, 2, 4])

    if np.any(tumor_mask):
        coords = np.argwhere(tumor_mask)  # shape: (N, 3)

        # bounding box
        min_coords = coords.min(axis=0).tolist()
        max_coords = coords.max(axis=0).tolist()

        # 中心点（体素坐标）
        center_voxel = coords.mean(axis=0).tolist()

        # 归一化中心点
        center_normalized = [
            float(center_voxel[0] / (shape[0] - 1)) if shape[0] > 1 else 0.0,
            float(center_voxel[1] / (shape[1] - 1)) if shape[1] > 1 else 0.0,
            float(center_voxel[2] / (shape[2] - 1)) if shape[2] > 1 else 0.0
        ]

        x_norm, y_norm, z_norm = center_normalized

        # 左右
        if x_norm < 0.45:
            left_right = "left"
        elif x_norm > 0.55:
            left_right = "right"
        else:
            left_right = "midline"

        # 前后
        if y_norm < 0.33:
            anterior_posterior = "anterior"
        elif y_norm > 0.66:
            anterior_posterior = "posterior"
        else:
            anterior_posterior = "central"

        # 上下
        if z_norm < 0.33:
            superior_inferior = "inferior"
        elif z_norm > 0.66:
            superior_inferior = "superior"
        else:
            superior_inferior = "middle"

        # 是否跨中线（粗略）
        x_coords = coords[:, 0]
        x_mid = (shape[0] - 1) / 2.0
        crosses_midline = bool((x_coords.min() < x_mid) and (x_coords.max() > x_mid))

        # 肿瘤真实体积
        tumor_volume_mm3 = tumor_voxel_count * voxel_volume_mm3
        tumor_volume_cm3 = tumor_volume_mm3 / 1000.0

        ncr_net_volume_mm3 = ncr_net_voxel_count * voxel_volume_mm3
        ed_volume_mm3 = ed_voxel_count * voxel_volume_mm3
        et_volume_mm3 = et_voxel_count * voxel_volume_mm3

        # 粗略位置描述
        location_description = f"{left_right} {anterior_posterior} {superior_inferior}"

    else:
        min_coords = [0, 0, 0]
        max_coords = [0, 0, 0]
        center_voxel = [0, 0, 0]
        center_normalized = [0.0, 0.0, 0.0]
        left_right = "unknown"
        anterior_posterior = "unknown"
        superior_inferior = "unknown"
        crosses_midline = False
        tumor_volume_mm3 = 0.0
        tumor_volume_cm3 = 0.0
        ncr_net_volume_mm3 = 0.0
        ed_volume_mm3 = 0.0
        et_volume_mm3 = 0.0
        location_description = "unknown"

    # 简单严重程度提示（只是辅助，不是临床诊断）
    if tumor_voxel_count == 0:
        severity_hint = "none"
    else:
        if et_ratio_in_tumor > 0.25 or tumor_volume_cm3 > 50:
            severity_hint = "high"
        elif et_ratio_in_tumor > 0.10 or tumor_volume_cm3 > 20:
            severity_hint = "medium"
        else:
            severity_hint = "low"

    # 组织成结果字典
    result = {
        "tumor_segmentation": {
            "file_type": "nii",
            "shape": shape,
            "voxel_spacing_mm": [round(float(v), 3) for v in voxel_spacing],
            "voxel_volume_mm3": round(float(voxel_volume_mm3), 3),

            "labels": {
                "0": "background",
                "1": "NCR/NET",
                "2": "ED",
                "4": "ET"
            },

            "ncr_net_voxel_count": ncr_net_voxel_count,
            "ed_voxel_count": ed_voxel_count,
            "et_voxel_count": et_voxel_count,
            "tumor_voxel_count": tumor_voxel_count,

            "ncr_net_voxel_percentage": round(float(ncr_net_voxel_percentage), 6),
            "ed_voxel_percentage": round(float(ed_voxel_percentage), 6),
            "et_voxel_percentage": round(float(et_voxel_percentage), 6),
            "tumor_voxel_percentage": round(float(tumor_voxel_percentage), 6),

            "ncr_net_ratio_in_tumor": round(float(ncr_net_ratio_in_tumor), 6),
            "ed_ratio_in_tumor": round(float(ed_ratio_in_tumor), 6),
            "et_ratio_in_tumor": round(float(et_ratio_in_tumor), 6),

            "ncr_net_volume_mm3": round(float(ncr_net_volume_mm3), 3),
            "ed_volume_mm3": round(float(ed_volume_mm3), 3),
            "et_volume_mm3": round(float(et_volume_mm3), 3),
            "tumor_volume_mm3": round(float(tumor_volume_mm3), 3),

            "has_ncr_net": has_ncr_net,
            "has_ed": has_ed,
            "has_et": has_et,

            "bounding_box": {
                "min": min_coords,
                "max": max_coords
            },

            "tumor_relative_position": {
                "center_voxel": [round(float(x), 3) for x in center_voxel],
                "center_normalized": [round(float(x), 3) for x in center_normalized],
                "left_right": left_right,
                "anterior_posterior": anterior_posterior,
                "superior_inferior": superior_inferior,
                "crosses_midline": crosses_midline,
                "location_description": location_description
            },

            "severity_hint": severity_hint
        }
    }

    return result


def save_tumor_info_to_json(mask_path, save_json_path):
    info = extract_tumor_segmentation_info(mask_path)
    with open(save_json_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    return info


if __name__ == "__main__":
    mask_path = r"F:\Undergraduate_Competitions\Computer_Design_Competition\code\BTS_Agent_System\downloads_seg_images\tumor_mask.nii"

    result = extract_tumor_segmentation_info(mask_path)

    # 打印结果
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 保存为 json 文件
    #save_json_path = r"F:\Undergraduate_Competitions\Computer_Design_Competition\code\BTS_Agent_System\downloads_seg_images\tumor_mask_info.json"
    #with open(save_json_path, "w", encoding="utf-8") as f:
        #json.dump(result, f, indent=2, ensure_ascii=False)

    #print(f"\n已保存到: {save_json_path}")
    
