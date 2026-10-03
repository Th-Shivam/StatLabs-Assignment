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
# 2. LOAD INDEPENDENTLY CALCULATED ANSWERS
# ============================================================

calculated_answers = {}

with open("calculated_answers.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        calculated_answers[row["question_id"]] = int(
            row["calculated_answer"]
        )


# ============================================================
# 3. EXTRACT OPERANDS FROM QUESTION
# ============================================================

def extract_operands(question):

    match = re.search(
        r"(\d+)\s*[+×−-]\s*(\d+)",
        question
    )

    if not match:
        return None

    first_number = int(match.group(1))
    second_number = int(match.group(2))

    return first_number, second_number


# ============================================================
# 4. EXTRACT ANSWER FROM MODEL RESPONSE
# ============================================================

def extract_answer_candidate(response, operands):

    # Remove commas from numbers
    response = response.replace(",", "")

    # --------------------------------------------------------
    # Case 1: Response contains "="
    # Example: 44 × 69 = 3036
    # --------------------------------------------------------

    if "=" in response:

        right_side = response.split("=")[-1]

        numbers = re.findall(r"\d+", right_side)

        if numbers:

            candidate = int(numbers[0])

            if candidate not in operands:
                return candidate


    # --------------------------------------------------------
    # Case 2: "equals 3036" or "answer is 3036"
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Case 3: Take numbers from right to left
    # --------------------------------------------------------

    numbers = re.findall(r"\d+", response)

    for number in reversed(numbers):

        candidate = int(number)

        if candidate not in operands:
            return candidate


    # --------------------------------------------------------
    # Nothing could be extracted
    # --------------------------------------------------------

    return None


# ============================================================
# 5. RUN-WISE SCORING
# ============================================================

model_run_scores = {}


with open("results.csv", newline="", encoding="utf-8") as f:

    reader = csv.DictReader(f)

    for row in reader:

        model = row["model"]
        run = row["run"]
        question_id = row["question_id"]
        response = row["response"]

        # Each model + run gets its own bucket
        key = (model, run)

        if key not in model_run_scores:

            model_run_scores[key] = {
                "total": 0,
                "correct": 0,
                "incorrect": 0,
                "unparseable": 0
            }

        # Count total response
        model_run_scores[key]["total"] += 1


        # Get operands from question
        operands = extract_operands(
            questions[question_id]
        )


        # Extract numerical answer from response
        candidate = extract_answer_candidate(
            response,
            operands
        )


        # Check answer
        if candidate is None:

            model_run_scores[key]["unparseable"] += 1

        elif candidate == calculated_answers[question_id]:

            model_run_scores[key]["correct"] += 1

        else:

            model_run_scores[key]["incorrect"] += 1


# ============================================================
# 6. PRINT RUN-WISE RESULTS
# ============================================================

print("\n" + "=" * 60)
print("RUN-WISE CORRECTED ACCURACY")
print("=" * 60)


for model in ["model-a", "model-b"]:

    print(f"\n{model}")
    print("-" * 30)

    for run in ["1", "2", "3"]:

        score = model_run_scores[(model, run)]

        accuracy = (
            score["correct"]
            / score["total"]
            * 100
        )

        print(
            f"Run {run}: "
            f"{score['correct']}/{score['total']} "
            f"= {accuracy:.2f}%"
        )

        print(
            f"  Incorrect   : {score['incorrect']}"
        )

        print(
            f"  Unparseable : {score['unparseable']}"
        )