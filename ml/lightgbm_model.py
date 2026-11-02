from lightgbm import LGBMClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"n_estimators": 300, "num_leaves": 31, "learning_rate": 0.05,
           "min_child_samples": 10, "is_unbalance": True, "random_state": SEED,
           "verbose": -1, "n_jobs": 1}

# Sáu cấu hình cân bằng; mỗi cấu hình thử đồng thời một bộ 3 tham số.
LUOI_THAM_SO = [
    {"num_leaves": [15], "learning_rate": [0.05], "min_child_samples": [10]},
    {"num_leaves": [15], "learning_rate": [0.1], "min_child_samples": [20]},
    {"num_leaves": [15], "learning_rate": [0.15], "min_child_samples": [30]},
    {"num_leaves": [31], "learning_rate": [0.05], "min_child_samples": [20]},
    {"num_leaves": [31], "learning_rate": [0.1], "min_child_samples": [30]},
    {"num_leaves": [31], "learning_rate": [0.15], "min_child_samples": [10]},
]


def tao_mo_hinh(**tham_so):
    return LGBMClassifier(**{**THAM_SO, **tham_so})


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "LightGBM", LUOI_THAM_SO)
