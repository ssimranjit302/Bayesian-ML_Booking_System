def detect_full_slot(prob, threshold=0.65):
    return int(prob >= threshold)

