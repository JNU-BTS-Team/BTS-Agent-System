import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage.morphology import binary_closing, binary_fill_holes
from sympy import false
import nibabel as nib
from losses import DiceLoss
import os
from medpy import metric
from medpy.metric import hd95

criteria = DiceLoss()


# morph_op图像形态学操作 去除噪声和分离物体
# 在这里的作用: 连接相邻但有小间隙的区域、平滑边界、 填补小裂缝/小空洞
# 论文写法: “We apply slice-wise morphological closing and hole filling with a (j+1)×(j+1) structuring element to reduce spurious predictions.”
def morph_op(msk_pred, j):
    # msk_pred: (H, W, D)
    out = msk_pred.copy()
    se = np.ones((j+1, j+1), dtype=bool)  # 结构元素 (j+1)x(j+1)

    for z in range(out.shape[-1]):  # 沿 D 维逐层处理
        sl = out[..., z].astype(bool)
        sl = binary_closing(sl, structure=se)
        sl = binary_fill_holes(sl, structure=se)
        out[..., z] = sl.astype(out.dtype)

    return out


# ===将输出的mask（numpy格式）保存为.nii.gz格式====
def save_cropped_mask_back_to_full(mask, ref_img_path, save_path, crop_size=(160, 192, 128)):
    ref_img = nib.load(ref_img_path)
    ref_shape = ref_img.shape[:3]   # (240, 240, 155)

    full_mask = np.zeros(ref_shape, dtype=np.uint8)

    H, W, D = ref_shape
    ch, cw, cd = crop_size

    sx = (H - ch - 1) // 2
    sy = (W - cw - 1) // 2
    sz = (D - cd - 1) // 2

    mask = np.asarray(mask).astype(np.uint8)

    if mask.shape != (ch, cw, cd):
        raise ValueError(f"mask.shape={mask.shape}, 但期望裁剪后大小是 {(ch, cw, cd)}")

    full_mask[sx:sx + ch, sy:sy + cw, sz:sz + cd] = mask

    header = ref_img.header.copy()
    header.set_data_dtype(np.uint8)

    out = nib.Nifti1Image(full_mask, affine=ref_img.affine, header=header)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    nib.save(out, save_path)
    print("saved to:", save_path)


# ===将(4 h w d)转换为(h w d)格式, 即将四个维度合并在一个维度用0124区分====
def get_mask(seg_volume, thresh):
    # print(seg_volume.shape) # (b, 4, H, W, D)
    seg_volume = seg_volume.detach().cpu().numpy()
    seg_volume = np.squeeze(seg_volume) # seg_volume对应的mask顺序: 2 1 4 0
    # print(seg_volume.shape) # (4, H, W, D)

    wt_pred = seg_volume[0]
    tc_pred = seg_volume[1]
    et_pred = seg_volume[2]

    mask = np.zeros_like(wt_pred) # numpy (H, W, D)
    mask[wt_pred > thresh[0]] = 2  # ED（肿瘤水肿）
    mask[tc_pred > thresh[1]] = 1  # NCR/NET（坏死 / 非增强肿瘤核心）
    mask[et_pred > thresh[2]] = 4  # ET（增强肿瘤）
    mask = mask.astype("uint8")
    return mask   # numpy (H, W, D)，标签值 {0,1,2,4}


# ===计算区域重合度差距====
def eval_dice_metrics(gt, pred, wt_j, ct_j, et_j):
    wt_pred = np.where(pred > 0, 1, 0) # WT (Whole Tumor) = 1 + 2 + 4 (三个区域取并集)
    if (np.sum(wt_pred) > 20) and (wt_j is not None):
        wt_pred = morph_op(wt_pred, wt_j)
    loss_wt = criteria(np.where(gt > 0, 1, 0), wt_pred)

    ct_pred = np.where(pred == 1, 1, 0) + np.where(pred == 4, 1, 0) # TC = 1 + 4
    if (np.sum(ct_pred) > 20) and (ct_j is not None):
        ct_pred = morph_op(ct_pred, ct_j)
    loss_ct = criteria(np.where(gt == 1, 1, 0) + np.where(gt == 4, 1, 0), ct_pred)

    et_pred = np.where(pred == 4, 1, 0)  # ET = 4
    if (np.sum(et_pred) > 20) and (et_j is not None):
        et_pred = morph_op(et_pred, et_j)
    loss_et = criteria(np.where(gt == 4, 1, 0), et_pred)

    return loss_wt, loss_et, loss_ct


# 选择切片
def _pick_best_slice(mask_3d):
    # mask_3d: (H,W,D)
    areas = [(mask_3d[..., z] > 0).sum() for z in range(mask_3d.shape[-1])]
    return int(np.argmax(areas)) if max(areas) > 0 else mask_3d.shape[-1] // 2


# 测量dice值并画分割结果图
def measure_dice_score(batch_pred, batch_y, thresh, wt_j=None, ct_j=None, et_j=None,
                       slice_idx=None, save_path=None, save_path_gt=None, base_volume=None, alpha=0.85):
    pred = get_mask(batch_pred,  thresh=thresh)                # (H,W,D)
    gt   = get_mask(batch_y,     thresh=[0.5, 0.5, 0.5])       # (H,W,D)

    loss_wt, loss_et, loss_ct = eval_dice_metrics(gt, pred, wt_j, ct_j, et_j)
    score = (loss_wt + loss_et + loss_ct) / 3.0 # 计算dice值


    # 选择切片（沿 D 维）
    z = _pick_best_slice(pred) if slice_idx is None else int(slice_idx)
    m2d_pred = pred[..., z].astype(np.uint8)
    m2d_gt   = gt[...,   z].astype(np.uint8)

    # 分割时候是否需要灰度底图（可选）
    if base_volume is not None:
        if hasattr(base_volume, "detach"):
            base_volume = base_volume.detach().cpu().numpy()
        img2d = base_volume[..., z].astype(np.float32)
        vmin, vmax = np.percentile(img2d, 1), np.percentile(img2d, 99)
        img2d = np.clip(img2d, vmin, vmax)
        img2d = (img2d - img2d.min()) / (img2d.max() - img2d.min() + 1e-8)
    else:
        img2d = np.zeros_like(m2d_pred, dtype=np.float32)

    def make_overlay(m2d):
        H, W = m2d.shape
        ov = np.zeros((H, W, 4), dtype=np.float32)  # RGBA

        for cls, rgb in [(2,(0,0,1)), (4,(1,0,0)), (1,(0,1,0))]:
            mask = (m2d == cls)
            ov[mask, :3] = rgb
            ov[mask, 3]  = 1.0

        return ov

    # ===== 保存预测图 =====
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.figure(figsize=(5,6))
        plt.imshow(img2d, cmap="gray", interpolation='nearest')
        plt.imshow(make_overlay(m2d_pred), alpha=alpha, interpolation='nearest')
        for cls, color in [(2,'blue'), (4,'red'), (1,'green')]:
            plt.contour((m2d_pred==cls).astype(np.uint8), levels=[0.5], colors=[color], linewidths=1.5)
        plt.axis('off')
        plt.savefig(save_path, dpi=220, bbox_inches='tight', pad_inches=0)
        plt.close()

    # ===== 保存 GT 图（ground truth） =====
    if save_path_gt is not None:
        os.makedirs(os.path.dirname(save_path_gt), exist_ok=True)
        plt.figure(figsize=(5,6))
        plt.imshow(img2d, cmap="gray", interpolation='nearest')
        plt.imshow(make_overlay(m2d_gt), alpha=alpha, interpolation='nearest')

        for cls, color in [(2,'blue'), (4,'red'), (1,'green')]:
            plt.contour((m2d_gt==cls).astype(np.uint8), levels=[0.5], colors=[color], linewidths=1.5)
        plt.axis('off')
        plt.savefig(save_path_gt, dpi=220, bbox_inches='tight', pad_inches=0)
        plt.close()

    return score, loss_wt, loss_et, loss_ct


# 保存原始四个模态灰度图片
def save_modal_slices(batch_x, z, save_dir="./"):
    """
    从 batch_x [1,4,128,160,192] 里，取最后一维 (width=192) 的第 z 层，
    分别保存 4 个模态的二维切片图像为 init1.png, init2.png, init3.png, init4.png。
    """
    os.makedirs(save_dir, exist_ok=True)

    for c in range(batch_x.shape[1]):  # 遍历四个模态
        img2d = batch_x[0, c, :, :, z]   # 取最后一维 z 层, shape [128,160]
        img2d = img2d.detach().cpu().numpy()  # 转 numpy 方便保存

        plt.figure(figsize=(6.4, 5.12), dpi=220)
        plt.imshow(img2d, cmap="gray")
        plt.axis("off")
        save_path = os.path.join(save_dir, f"init{c+1}.png")
        plt.savefig(save_path, dpi=220, bbox_inches="tight", pad_inches=0)
        plt.close()
        # print(f"Saved {save_path}")


# -------------------- 计算HD95 (follow MF2TRANS) --------------------
def eval_hd95_metrics(gt, pred, wt_j, ct_j, et_j):
    wt_pred = np.where(pred > 0, 1, 0) # WT (Whole Tumor) = 1 + 2 + 4 (三个区域取并集)
    #if (np.sum(wt_pred) > 20) and (wt_j is not None): # 如果WT区域大小超过20并且有wt_j(用于限制形态学操作阈值)
    wt_pred = morph_op(wt_pred, wt_j)
    hd95_WT = compute_BraTS_HD95(np.where(gt > 0, 1, 0), wt_pred)

    tc_pred = np.where(pred == 1, 1, 0) + np.where(pred == 4, 1, 0) # TC = 1 + 4
    #if (np.sum(tc_pred) > 20) and (ct_j is not None):
    tc_pred = morph_op(tc_pred, ct_j)
    hd95_TC = compute_BraTS_HD95(np.where(gt == 1, 1, 0) + np.where(gt == 4, 1, 0), tc_pred)

    et_pred = np.where(pred == 4, 1, 0)  # ET = 4
    if (np.sum(et_pred) > 20) and (et_j is not None): # et_j=None保持原始预测
        et_pred = morph_op(et_pred, et_j)
    hd95_ET = compute_BraTS_HD95(np.where(gt == 4, 1, 0), et_pred)

    return hd95_WT, hd95_TC, hd95_ET


def compute_BraTS_HD95(ref, pred):
    """
    ref and gt are binary integer numpy.ndarray s
    spacing is assumed to be (1, 1, 1)
    :param ref:  h w d
    :param pred: h w d
    :return:
    """
    num_ref = np.sum(ref)
    num_pred = np.sum(pred)
    if num_ref == 0:
        if num_pred == 0:
            return 0
        else:
            print("373")
            # return 1.0
            # follow ACN and SMU-Net
            return 373.12866
            # follow nnUNet
    elif num_pred == 0 and num_ref != 0:
        # return 1.0
        # follow ACN and SMU-Net
        return 373.12866
        # follow in nnUNet
    else:
        return hd95(pred, ref, (1, 1, 1))


def cal_hd95(batch_pred, batch_y, thresh, wt_j=None, ct_j=None, et_j=None, slice_idx=None):
    """"
    batch_pred: [b 4 H W D] 第2个维度: ED NET ET BK (mask:2 1 4 0)
    batch_y:    [b 4 H W D] 第2个维度: ED NET ET BK (mask:2 1 4 0)
    WT = 1 + 2 + 4,  TC = 1 + 4,  ET = 4
    """
    pred = get_mask(batch_pred, thresh=thresh)        # numpy (H, W, D)，标签值 {0,1,2,4} --- ED-2 NET-1 ET-4 BK-0
    gt   = get_mask(batch_y, thresh=[0.5, 0.5, 0.5])  # numpy (H, W, D)，标签值 {0,1,2,4} --- ED-2 NET-1 ET-4 BK-0
    #print("mask shape:", pred.shape)  # h w d
    #print("unique pred:", np.unique(pred))
    #print("unique gt:", np.unique(gt))

    hd95_WT, hd95_TC, hd95_ET = eval_hd95_metrics(gt=gt, pred=pred, wt_j=wt_j, ct_j=ct_j, et_j=et_j)
    avg_hd95 = (hd95_WT + hd95_TC + hd95_ET) / 3


    return avg_hd95, hd95_WT, hd95_TC, hd95_ET

