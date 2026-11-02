"""
So sánh 5 phương pháp học máy (và baseline luật) trên 3 mục tiêu cảnh báo.

Mọi phương pháp chạy trên CÙNG các fold (cùng seed) bằng cross-validation
lồng nhau của danh_gia.py: mỗi fold ngoài tự chọn cấu hình tham số (PR-AUC) và
ngưỡng (F2) chỉ từ phần train. Lặp lại với nhiều seed (--so-lan-lap) để biết
chênh lệch giữa hai phương pháp là thật hay chỉ do cách chia fold.

Mục tiêu "thoi_hoc_suy_ra" là cách chính cho buộc thôi học: suy từ nguy cơ
cảnh báo của chính phương pháp đó (dac_trung.nguy_co_thoi_hoc), không train thêm.

Kết quả ghi vào results/:
- so_sanh_chi_tiet.csv: mỗi (mục tiêu, phương pháp, seed, fold) một dòng,
  kèm cấu hình được chọn và thời gian chạy.
- so_sanh_tom_tat.csv:  trung bình và độ lệch chuẩn qua mọi fold, mọi seed.
- so_sanh.png:          biểu đồ PR-AUC, recall, F2.

Chạy:  python ml/so_sanh.py                    # 1 lần (5 fold)
       python ml/so_sanh.py --so-lan-lap 3     # 3 seed × 5 fold
       python ml/so_sanh.py --phuong-phap "Decision Tree" XGBoost
"""

import argparse
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")   # chỉ lưu ảnh ra file, không mở cửa sổ
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import dac_trung
import danh_gia
from mo_hinh_cuoi import PHUONG_PHAP   # thứ tự cố định, quyết định cả màu trên biểu đồ


THU_MUC_GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_KET_QUA = os.path.join(THU_MUC_GOC, "results")

TEN_BASELINE = "Baseline luật"
TEN_MUC_TIEU = {
    "canh_bao": "Cảnh báo kỳ sau",
    "thoi_hoc_suy_ra": "Thôi học\n(suy từ cảnh báo)",
    "thoi_hoc": "Thôi học\n(train riêng)",
    "truot_mon": "Trượt môn",
}
CHI_SO_VE = {"pr_auc": "PR-AUC (so sánh mô hình)", "recall": "Recall tại ngưỡng F2",
             "f2": "F2 tại ngưỡng F2"}

# Bảng màu phân loại đã kiểm tra mù màu (dataviz skill, theme mặc định); baseline xám
MAU = {TEN_BASELINE: "#8a8984", "Decision Tree": "#2a78d6", "SVM": "#eb6834",
       "XGBoost": "#1baf7a", "Random Forest": "#eda100", "LightGBM": "#e87ba4"}
MAU_CHU, MAU_CHU_PHU, MAU_LUOI = "#1f1f1e", "#5f5e5a", "#e4e3df"


def _cac_phuong_phap(ten_chon):
    """[(tên, tao_mo_hinh, lưới)] theo thứ tự cố định, baseline luôn đứng đầu."""
    ds = [(ten, mod.tao_mo_hinh, getattr(mod, "LUOI_THAM_SO", None))
          for ten, mod in PHUONG_PHAP.items() if not ten_chon or ten in ten_chon]
    return ds


def so_sanh(ten_chon=None, so_lan_lap=1, duong_dan=None, in_tien_do=True):
    """Chạy so sánh, trả về bảng chi tiết (mỗi fold một dòng)."""
    cac_dong = []
    du_lieu = {m: dac_trung.tao_du_lieu(m, duong_dan) for m in dac_trung.MUC_TIEU}
    y_thoi_hoc = du_lieu["thoi_hoc"][1]

    for lan in range(so_lan_lap):
        seed = danh_gia.SEED + lan
        for muc_tieu, (X, y, nhom) in du_lieu.items():
            fold = danh_gia.chia_fold(y, nhom, seed=seed)
            cac_pp = [(TEN_BASELINE, danh_gia.tao_baseline(muc_tieu), None)] + _cac_phuong_phap(ten_chon)
            for ten, tao, luoi in cac_pp:
                bat_dau = time.perf_counter()
                bang, xac_suat, nguong = danh_gia.danh_gia_cheo(tao, X, y, nhom, luoi, seed=seed)
                giay = time.perf_counter() - bat_dau
                if in_tien_do:
                    print(f"  seed {seed} | {muc_tieu:9} | {ten:13} | PR-AUC "
                          f"{bang['pr_auc'].mean():.3f} | {giay:5.1f} s", flush=True)
                ket_qua = [(muc_tieu, bang)]
                if muc_tieu == "canh_bao":
                    suy_ra = danh_gia.danh_gia_thoi_hoc_suy_ra(xac_suat, nguong, X, y_thoi_hoc, fold)
                    suy_ra["cau_hinh"] = bang["cau_hinh"]
                    ket_qua.append(("thoi_hoc_suy_ra", suy_ra))
                for mt, b in ket_qua:
                    b = b.assign(muc_tieu=mt, phuong_phap=ten, seed=seed,
                                 fold=range(len(b)), giay=giay / len(b))
                    cac_dong.append(b)
    cot = ["muc_tieu", "phuong_phap", "seed", "fold", *danh_gia.CAC_CHI_SO, "cau_hinh", "giay"]
    return pd.concat(cac_dong, ignore_index=True)[cot]


def tom_tat(chi_tiet):
    """Trung bình / độ lệch chuẩn mỗi chỉ số theo (mục tiêu, phương pháp)."""
    nhom = chi_tiet.groupby(["muc_tieu", "phuong_phap"], sort=False)
    tb = nhom[danh_gia.CAC_CHI_SO].mean().add_suffix("_tb")
    lc = nhom[danh_gia.CAC_CHI_SO].std().add_suffix("_lc")
    giay = nhom["giay"].sum().rename("tong_giay")
    xen = [c for pair in zip(tb.columns, lc.columns) for c in pair]
    return pd.concat([tb, lc], axis=1)[xen].join(giay).reset_index()


def bang_chi_so(tom, chi_so):
    """Bảng 'tb ± lc' của một chỉ số: dòng = phương pháp, cột = mục tiêu."""
    o = tom.assign(gt=tom[f"{chi_so}_tb"].map("{:.3f}".format) + " ± "
                   + tom[f"{chi_so}_lc"].map("{:.3f}".format))
    bang = o.pivot(index="phuong_phap", columns="muc_tieu", values="gt")
    thu_tu = [p for p in [TEN_BASELINE, *PHUONG_PHAP] if p in bang.index]
    return bang.loc[thu_tu, [m for m in TEN_MUC_TIEU if m in bang.columns]]


def ve_bieu_do(tom, duong_dan):
    """3 biểu đồ cột nhóm (PR-AUC, recall, F2): nhóm = mục tiêu, cột = phương pháp."""
    cac_muc_tieu = [m for m in TEN_MUC_TIEU if m in set(tom["muc_tieu"])]
    cac_pp = [p for p in [TEN_BASELINE, *PHUONG_PHAP] if p in set(tom["phuong_phap"])]
    rong = 0.8 / len(cac_pp)
    x = np.arange(len(cac_muc_tieu))

    fig, cac_truc = plt.subplots(len(CHI_SO_VE), 1, figsize=(11, 4.2 * len(CHI_SO_VE)))
    for truc, (chi_so, tieu_de) in zip(cac_truc, CHI_SO_VE.items()):
        for j, pp in enumerate(cac_pp):
            dong = tom[tom["phuong_phap"] == pp].set_index("muc_tieu").reindex(cac_muc_tieu)
            vi_tri = x - 0.4 + rong * (j + 0.5)
            cot = truc.bar(vi_tri, dong[f"{chi_so}_tb"], rong * 0.92, yerr=dong[f"{chi_so}_lc"],
                           color=MAU[pp], label=pp, error_kw={"elinewidth": 1, "ecolor": MAU_CHU_PHU},
                           hatch="///" if pp == TEN_BASELINE else None, edgecolor="white", linewidth=0)
            truc.bar_label(cot, labels=[f"{v:.2f}" for v in dong[f"{chi_so}_tb"]],
                           fontsize=7, color=MAU_CHU_PHU, padding=2)
        truc.set_title(tieu_de, loc="left", fontsize=11, color=MAU_CHU)
        truc.set_xticks(x, [TEN_MUC_TIEU[m] for m in cac_muc_tieu], fontsize=9, color=MAU_CHU)
        truc.set_ylim(0, 1.12)
        truc.yaxis.grid(True, color=MAU_LUOI, linewidth=0.8)
        truc.set_axisbelow(True)
        for canh in ["top", "right", "left"]:
            truc.spines[canh].set_visible(False)
        truc.spines["bottom"].set_color(MAU_LUOI)
        truc.tick_params(axis="y", colors=MAU_CHU_PHU, labelsize=8, length=0)
        truc.tick_params(axis="x", length=0)
    cac_truc[0].legend(ncol=len(cac_pp), loc="upper left", bbox_to_anchor=(0, 1.22),
                       frameon=False, fontsize=9)
    fig.suptitle("So sánh 5 phương pháp trên dữ liệu mô phỏng (trung bình ± độ lệch chuẩn qua các fold)",
                 x=0.01, ha="left", fontsize=12, color=MAU_CHU)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(duong_dan, dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pd.set_option("display.width", 220)

    tham_so = argparse.ArgumentParser(description="So sánh 5 phương pháp trên 3 mục tiêu")
    tham_so.add_argument("--so-lan-lap", type=int, default=1, help="số seed (mỗi seed 5 fold)")
    tham_so.add_argument("--phuong-phap", nargs="*", choices=list(PHUONG_PHAP),
                         help="chỉ chạy các phương pháp này (mặc định: cả 5)")
    tham_so.add_argument("--du-lieu", default=None, help="file xlsx (mặc định data/mo_phong.xlsx)")
    a = tham_so.parse_args()

    bat_dau = time.perf_counter()
    chi_tiet = so_sanh(a.phuong_phap, a.so_lan_lap, a.du_lieu)
    tom = tom_tat(chi_tiet)

    os.makedirs(THU_MUC_KET_QUA, exist_ok=True)
    chi_tiet.to_csv(os.path.join(THU_MUC_KET_QUA, "so_sanh_chi_tiet.csv"), index=False, encoding="utf-8-sig")
    tom.to_csv(os.path.join(THU_MUC_KET_QUA, "so_sanh_tom_tat.csv"), index=False, encoding="utf-8-sig")
    ve_bieu_do(tom, os.path.join(THU_MUC_KET_QUA, "so_sanh.png"))

    for chi_so in ["pr_auc", "recall", "precision", "f2"]:
        print(f"\n{chi_so.upper()} (trung bình ± độ lệch chuẩn, {a.so_lan_lap} seed × {danh_gia.SO_FOLD} fold)")
        print(bang_chi_so(tom, chi_so).to_string())
    print(f"\nĐã ghi results/ ({time.perf_counter() - bat_dau:.0f} s)")
