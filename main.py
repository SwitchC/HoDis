def calculate_score(correct, total):
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)