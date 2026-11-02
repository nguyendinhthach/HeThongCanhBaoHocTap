from sklearn.ensemble import RandomForestClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"n_estimators": 300, "max_depth": None, "min_samples_leaf": 10,
           "class_weight": "balanced", "random_state": SEED, "n_jobs": 1}

# 2 × 3 = 6 cấu hình, cùng số lượng thử với các phương pháp còn lại.
LUOI_THAM_SO = {"max_depth": [None, 10], "min_samples_leaf": [5, 10, 20]}


def tao_mo_hinh(**tham_so):
    return RandomForestClassifier(**{**THAM_SO, **tham_so})


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "Random Forest", LUOI_THAM_SO)
