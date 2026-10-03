import csv
import re
from collections import defaultdict


# --------------------------------------------------
# 1. Load questions
# --------------------------------------------------

questions = {}

with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        questions[row["question_id"]] = row["question"]


# --------------------------------------------------
# 2. Keep only the FIRST occurrence of each
#    unique question text
# --------------------------------------------------

seen_questions = set()
unique_question_ids = []

for question_id, question in questions.items():

    if question not in seen_questions:
        seen_questions.add(question)
        unique_question_ids.append(question_id)


print("=" * 60)
print("UNIQUE QUESTION BENCHMARK")
print("=" * 60)

print(f"Original questions : {len(questions)}")
print(f"Unique questions   : {len(unique_question_ids)}")
print(f"Removed duplicates : {len(questions) - len(unique_question_ids)}")


# --------------------------------------------------
# 3. Calculate correct answer independently
# --------------------------------------------------

def calculate_answer(question):

    match = re.search(
        r"(\d+)\s*([+×−-])\s*(\d+)",
        question
    )

    if not match:
        raise ValueError(f"Cannot parse: {question}")

    a = int(match.group(1))
    operator = match.group(2)
    b = int(match.group(3))

    if operator == "+":
        return a + b

    elif operator in ("-", "−"):
        return a - b

    elif operator == "×":
        return a * b

    raise ValueError(f"Unknown operator: {operator}")


# --------------------------------------------------
# 4. Extract model answer
# --------------------------------------------------

def extract_answer(response, question):

    response = response.replace(",", "")

    match = re.search(
        r"(\d+)\s*[+×−-]\s*(\d+)",
        question
    )

    if not match:
        return None

    operands = {
        int(match.group(1)),
        int(match.group(2))
    }

    # Example:
    # 44 × 69 = 3036
    if "=" in response:

        right_side = response.split("=")[-1]

        numbers = re.findall(r"\d+", right_side)

        if numbers:
            candidate = int(numbers[0])

            if candidate not in operands:
                return candidate

    # Example:
    # The answer is 3036
    # equals 3036
    match = re.search(
        r"(?:equals|answer\s+is)"
        r"\s*(?:approximately\s*)?"
        r"(\d+)",
        response,
        re.IGNORECASE
    )

    if match:

        candidate = int(match.group(1))

        if candidate not in operands:
            return candidate

    # Example:
    # 3036
    # **3036**
    numbers = re.findall(r"\d+", response)

    for number in reversed(numbers):

        candidate = int(number)

        if candidate not in operands:
            return candidate

    return None


# --------------------------------------------------
# 5. Build unique-question benchmark
# --------------------------------------------------

unique_ids = set(unique_question_ids)

scores = defaultdict(lambda: {
    "correct": 0,
    "total": 0
})


with open("results.csv", newline="", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        question_id = row["question_id"]

        # Ignore duplicate question IDs
        if question_id not in unique_ids:
            continue

        question = questions[question_id]

        correct_answer = calculate_answer(question)

        model_answer = extract_answer(
            row["response"],
            question
        )

        model = row["model"]

        scores[model]["total"] += 1

        if model_answer == correct_answer:
            scores[model]["correct"] += 1


# --------------------------------------------------
# 6. Print results
# --------------------------------------------------

print()
print("=" * 60)
print("RESULTS ON 50 UNIQUE QUESTIONS")
print("=" * 60)

for model in sorted(scores):

    correct = scores[model]["correct"]
    total = scores[model]["total"]

    accuracy = correct / total * 100

    print(
        f"{model}: "
        f"{correct}/{total} = "
        f"{accuracy:.2f}%"
    )