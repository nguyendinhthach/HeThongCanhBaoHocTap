from sklearn.ensemble import RandomForestClassifier

from danh_gia import SEED, chay_thu


THAM_SO = {"n_estimators": 300, "min_samples_leaf": 10,
           "class_weight": "balanced", "random_state": SEED}


def tao_mo_hinh():
    return RandomForestClassifier(**THAM_SO)


if __name__ == "__main__":
    chay_thu(tao_mo_hinh, "Random Forest")
