def calculate_score(correct, total):
    if total == 0:
        return 0
    return round((correct / total) * 100, 2)

def check_pass_status(score):
    threshold = 60 
    return score >= threshold

def analyze_student_weaknesses(detailed_results):
    mistakes = [item for item in detailed_results if not item['is_correct']]
    return mistakes