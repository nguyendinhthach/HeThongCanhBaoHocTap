from lightgbm import LGBMClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"n_estimators": 300, "min_child_samples": 10,
           "is_unbalance": True, "random_state": SEED, "verbose": -1}


def tao_mo_hinh():
    return LGBMClassifier(**THAM_SO)


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "LightGBM")
