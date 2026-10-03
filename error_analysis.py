import csv
import re


# ============================================================
# 1. LOAD QUESTIONS
# ============================================================

questions = {}

with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        questions[row["question_id"]] = row["question"]


# ============================================================
# 2. LOAD INDEPENDENT ANSWERS
# ============================================================

calculated_answers = {}

with open("calculated_answers.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        calculated_answers[row["question_id"]] = int(
            row["calculated_answer"]
        )


# ============================================================
# 3. EXTRACT OPERANDS
# ============================================================

def extract_operands(question):

    match = re.search(
        r"(\d+)\s*[+×−-]\s*(\d+)",
        question
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        int(match.group(2))
    )


# ============================================================
# 4. EXTRACT ANSWER FROM RESPONSE
# ============================================================

def extract_answer_candidate(response, operands):

    response = response.replace(",", "")

    # Example: 44 × 69 = 3036
    if "=" in response:

        right_side = response.split("=")[-1]

        numbers = re.findall(r"\d+", right_side)

        if numbers:

            candidate = int(numbers[0])

            if candidate not in operands:
                return candidate


    # Example: "answer is 3036"
    # Example: "equals 3036"

    pattern = r"(?:equals|answer\s+is)\s*(?:approximately\s*)?(\d+)"

    match = re.search(
        pattern,
        response,
        re.IGNORECASE
    )

    if match:

        candidate = int(match.group(1))

        if candidate not in operands:
            return candidate


    # Take last valid number
    numbers = re.findall(r"\d+", response)

    for number in reversed(numbers):

        candidate = int(number)

        if candidate not in operands:
            return candidate


    return None


# ============================================================
# 5. FIND WRONG QUESTIONS
# ============================================================

errors = {}


with open("results.csv", newline="", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        model = row["model"]
        run = row["run"]
        question_id = row["question_id"]
        response = row["response"]

        key = (model, run)

        if key not in errors:
            errors[key] = []

        operands = extract_operands(
            questions[question_id]
        )

        candidate = extract_answer_candidate(
            response,
            operands
        )

        correct_answer = calculated_answers[question_id]

        # Only store wrong answers
        if candidate != correct_answer:

            errors[key].append({
                "question_id": question_id,
                "response": response,
                "expected": correct_answer,
                "got": candidate
            })


# ============================================================
# 6. PRINT ERROR ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("QUESTION-WISE ERROR ANALYSIS")
print("=" * 70)


for model in ["model-a", "model-b"]:

    for run in ["1", "2", "3"]:

        key = (model, run)

        print(f"\n{model} - Run {run}")
        print("-" * 50)

        for error in errors[key]:

            print(
                f"{error['question_id']} | "
                f"Expected: {error['expected']} | "
                f"Got: {error['got']} | "
                f"Response: {error['response']!r}"
            )

        print(
            f"\nTotal errors: {len(errors[key])}"
        )


# ============================================================
# 7. CHECK ERROR CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("ERROR CONSISTENCY")
print("=" * 70)


for model in ["model-a", "model-b"]:

    run1 = {
        error["question_id"]
        for error in errors[(model, "1")]
    }

    run2 = {
        error["question_id"]
        for error in errors[(model, "2")]
    }

    run3 = {
        error["question_id"]
        for error in errors[(model, "3")]
    }

    common = run1 & run2 & run3

    print(f"\n{model}")

    print("Wrong in Run 1:", sorted(run1))
    print("Wrong in Run 2:", sorted(run2))
    print("Wrong in Run 3:", sorted(run3))

    print(
        "\nWrong in ALL 3 runs:",
        sorted(common)
    )