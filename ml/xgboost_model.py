"""
XGBoost cho 3 mục tiêu cảnh báo (theo mẫu decision_tree.py).

XGBoost nhận NaN trực tiếp (tự học nhánh đi cho ô trống) nên không cần điền.
Mất cân bằng xử lý bằng scale_pos_weight = số ca âm / số ca dương; tỉ lệ này
khác nhau giữa các mục tiêu (cảnh báo ~6% dương, thôi học ~1,2%) nên tính lại
từ y mỗi lần fit thay vì đặt cứng một số.

Chạy:  python ml/xgboost_model.py
"""

from xgboost import XGBClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05,
           "subsample": 0.8, "colsample_bytree": 0.8, "eval_metric": "aucpr",
           "random_state": SEED, "n_jobs": -1}


class XGBCanBang(XGBClassifier):
    """XGBClassifier tự đặt scale_pos_weight theo tỉ lệ nhãn của dữ liệu train."""

    def fit(self, X, y, **kwargs):
        so_duong = int(y.sum())
        self.set_params(scale_pos_weight=(len(y) - so_duong) / max(so_duong, 1))
        return super().fit(X, y, **kwargs)


def tao_mo_hinh():
    return XGBCanBang(**THAM_SO)


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "XGBoost")
