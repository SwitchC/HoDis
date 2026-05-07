def calculate_score(correct, total):
    """Вираховує відсоток правильних відповідей."""
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

def check_pass_status(score):
    """Перевіряє, чи подолано прохідний бар'єр."""
    threshold = 60 
    return score >= threshold