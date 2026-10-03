# RUN:
# python master_program.py

import csv
import re
import statistics
from collections import Counter, defaultdict


# ============================================================
# 1. LOAD DATA
# ============================================================

questions = {}
answer_key = {}
responses = []


with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        questions[row["question_id"]] = row["question"]


with open("answer_key.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        answer_key[row["question_id"]] = int(row["expected"])


with open("results.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        responses.append(row)


# ============================================================
# 2. INDEPENDENTLY CALCULATE THE ANSWER TO A QUESTION
# ============================================================

def calculate_answer(question):

    match = re.search(
        r"(\d+)\s*([+×−-])\s*(\d+)",
        question
    )

    if not match:
        raise ValueError(f"Cannot parse question: {question}")

    a = int(match.group(1))
    operator = match.group(2)
    b = int(match.group(3))

    if operator == "+":
        return a + b

    if operator in ("-", "−"):
        return a - b

    if operator == "×":
        return a * b

    raise ValueError(f"Unknown operator: {operator}")


# ============================================================
# 3. EXTRACT THE FINAL NUMERIC ANSWER FROM A MODEL RESPONSE
# ============================================================

def extract_answer(response, question):

    # 1,251 -> 1251
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

    # --------------------------------------------------------
    # Case 1:
    # "44 × 69 = 3036"
    # --------------------------------------------------------

    if "=" in response:

        right_side = response.split("=")[-1]

        numbers = re.findall(r"\d+", right_side)

        if numbers:

            candidate = int(numbers[0])

            if candidate not in operands:
                return candidate

    # --------------------------------------------------------
    # Case 2:
    # "The answer is 954"
    # "41 × 59 equals 2419"
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Case 3:
    # "954"
    # "**954**"
    # "The result is 954"
    #
    # Take the last number that isn't one of the operands.
    # --------------------------------------------------------

    numbers = re.findall(r"\d+", response)

    for number in reversed(numbers):

        candidate = int(number)

        if candidate not in operands:
            return candidate

    return None


# ============================================================
# 4. ORIGINAL SCORER
#
# Reproduce score.py exactly:
#
# response.strip() == answer_key[question_id]
# ============================================================

original_scores = defaultdict(lambda: {
    "correct": 0,
    "total": 0
})


for row in responses:

    model = row["model"]
    question_id = row["question_id"]
    response = row["response"]

    original_scores[model]["total"] += 1

    if response.strip() == str(answer_key[question_id]):
        original_scores[model]["correct"] += 1


# ============================================================
# 5. DUPLICATE QUESTION TEXT AUDIT
# ============================================================

question_text_to_ids = defaultdict(list)

for question_id, question in questions.items():
    question_text_to_ids[question].append(question_id)


duplicate_groups = {
    question: ids
    for question, ids in question_text_to_ids.items()
    if len(ids) > 1
}


duplicate_question_ids = []

for ids in duplicate_groups.values():
    duplicate_question_ids.extend(ids)


duplicate_question_ids.sort()


# ============================================================
# 6. CHECK WHETHER DUPLICATE QUESTIONS HAVE
#    CONSISTENT ANSWER KEYS
# ============================================================

duplicate_key_consistent = True

for ids in duplicate_groups.values():

    keys = {
        answer_key[question_id]
        for question_id in ids
    }

    if len(keys) != 1:
        duplicate_key_consistent = False


# ============================================================
# 7. INDEPENDENT ANSWER-KEY AUDIT
# ============================================================

wrong_answer_key_ids = []

for question_id, question in questions.items():

    calculated = calculate_answer(question)
    expected = answer_key[question_id]

    if calculated != expected:
        wrong_answer_key_ids.append(question_id)


# ============================================================
# 8. FULL RESPONSE AUDIT
#
# Classifications:
#
# EXACT_CORRECT
# FORMAT_FALSE_NEGATIVE
# KEY_ERROR
# GENUINELY_WRONG
# UNPARSEABLE
# ============================================================

audit_results = []


for row in responses:

    question_id = row["question_id"]
    model = row["model"]
    run = row["run"]
    response = row["response"]

    question = questions[question_id]

    key_answer = answer_key[question_id]
    real_answer = calculate_answer(question)

    extracted_answer = extract_answer(
        response,
        question
    )

    exact_match = (
        response.strip() == str(key_answer)
    )

    if exact_match:

        classification = "EXACT_CORRECT"

    elif extracted_answer is None:

        classification = "UNPARSEABLE"

    elif real_answer != key_answer:

        if extracted_answer == real_answer:
            classification = "KEY_ERROR"
        else:
            classification = "GENUINELY_WRONG"

    elif extracted_answer == real_answer:

        classification = "FORMAT_FALSE_NEGATIVE"

    else:

        classification = "GENUINELY_WRONG"


    audit_results.append({
        "question_id": question_id,
        "model": model,
        "run": run,
        "key_answer": key_answer,
        "real_answer": real_answer,
        "response": response,
        "extracted_answer": extracted_answer,
        "classification": classification
    })


audit_counts = Counter(
    row["classification"]
    for row in audit_results
)


# ============================================================
# 9. CORRECTED 56-QUESTION BENCHMARK
# ============================================================

corrected_scores = defaultdict(lambda: {
    "correct": 0,
    "total": 0
})


run_scores = defaultdict(lambda: {
    "correct": 0,
    "total": 0
})


for row in audit_results:

    model = row["model"]
    run = row["run"]

    corrected_scores[model]["total"] += 1
    run_scores[(model, run)]["total"] += 1

    if row["extracted_answer"] == row["real_answer"]:

        corrected_scores[model]["correct"] += 1
        run_scores[(model, run)]["correct"] += 1


# ============================================================
# 10. RUN-TO-RUN MEAN AND STANDARD DEVIATION
# ============================================================

run_percentages = {}


for model in sorted(corrected_scores):

    percentages = []

    for run in ["1", "2", "3"]:

        result = run_scores[(model, run)]

        percentage = (
            result["correct"] /
            result["total"]
        ) * 100

        percentages.append(percentage)

    run_percentages[model] = percentages


variability = {}

for model, percentages in run_percentages.items():

    mean = statistics.mean(percentages)
    std = statistics.stdev(percentages)

    variability[model] = {
        "mean": mean,
        "std": std
    }


# ============================================================
# 11. 50-UNIQUE-QUESTION BENCHMARK
#
# Keep the first occurrence of each unique question text.
# ============================================================

seen_questions = set()
unique_question_ids = []


for question_id, question in questions.items():

    if question not in seen_questions:

        seen_questions.add(question)
        unique_question_ids.append(question_id)


unique_question_id_set = set(unique_question_ids)


unique_scores = defaultdict(lambda: {
    "correct": 0,
    "total": 0
})


for row in audit_results:

    question_id = row["question_id"]

    if question_id not in unique_question_id_set:
        continue

    model = row["model"]

    unique_scores[model]["total"] += 1

    if row["extracted_answer"] == row["real_answer"]:
        unique_scores[model]["correct"] += 1


# ============================================================
# 12. TEMPERATURE AUDIT
# ============================================================

temperatures = defaultdict(set)

for row in responses:

    temperatures[row["model"]].add(
        float(row["temperature"])
    )


# ============================================================
# 13. PRINT FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("FINAL ASSIGNMENT ANALYSIS")
print("=" * 70)


# ------------------------------------------------------------
# Dataset size
# ------------------------------------------------------------

print()
print("1. DATASET")
print("-" * 70)

print(f"Question records       : {len(questions)}")
print(f"Unique question texts  : {len(question_text_to_ids)}")
print(f"Duplicate question texts: {len(duplicate_groups)}")
print(f"Total responses        : {len(responses)}")


# ------------------------------------------------------------
# Original score
# ------------------------------------------------------------

print()
print("2. ORIGINAL SCORE.PY RESULTS")
print("-" * 70)

for model in sorted(original_scores):

    correct = original_scores[model]["correct"]
    total = original_scores[model]["total"]

    accuracy = correct / total * 100

    print(
        f"{model}: "
        f"{correct}/{total} = "
        f"{accuracy:.1f}%"
    )


# ------------------------------------------------------------
# Duplicate questions
# ------------------------------------------------------------

print()
print("3. DUPLICATE QUESTION AUDIT")
print("-" * 70)

print(
    f"Duplicate question texts: "
    f"{len(duplicate_groups)}"
)

print(
    f"Extra duplicate records: "
    f"{len(questions) - len(unique_question_ids)}"
)

print(
    "Duplicate question IDs: "
    + ",".join(duplicate_question_ids)
)

print(
    f"Duplicate answer keys consistent: "
    f"{duplicate_key_consistent}"
)


for question, ids in duplicate_groups.items():

    print(
        f"  {','.join(ids)} -> "
        f"{answer_key[ids[0]]}"
    )


# ------------------------------------------------------------
# Answer key audit
# ------------------------------------------------------------

print()
print("4. ANSWER KEY AUDIT")
print("-" * 70)

print(
    f"Correct answer-key entries: "
    f"{len(questions) - len(wrong_answer_key_ids)}"
)

print(
    f"Wrong answer-key entries: "
    f"{len(wrong_answer_key_ids)}"
)

print(
    "Wrong answer-key IDs: "
    + ",".join(wrong_answer_key_ids)
)

for question_id in wrong_answer_key_ids:

    calculated = calculate_answer(
        questions[question_id]
    )

    expected = answer_key[question_id]

    print(
        f"  {question_id}: "
        f"calculated={calculated}, "
        f"key={expected}"
    )


# ------------------------------------------------------------
# Response audit
# ------------------------------------------------------------

print()
print("5. RESPONSE SCORING AUDIT")
print("-" * 70)

print(
    f"Exact correct         : "
    f"{audit_counts['EXACT_CORRECT']}"
)

print(
    f"Format false negative : "
    f"{audit_counts['FORMAT_FALSE_NEGATIVE']}"
)

print(
    f"Key error             : "
    f"{audit_counts['KEY_ERROR']}"
)

print(
    f"Genuinely wrong       : "
    f"{audit_counts['GENUINELY_WRONG']}"
)

print(
    f"Unparseable           : "
    f"{audit_counts['UNPARSEABLE']}"
)

print(
    f"Audit total           : "
    f"{sum(audit_counts.values())}"
)


# ------------------------------------------------------------
# Corrected 56-question score
# ------------------------------------------------------------

print()
print("6. CORRECTED 56-RECORD BENCHMARK")
print("-" * 70)

for model in sorted(corrected_scores):

    correct = corrected_scores[model]["correct"]
    total = corrected_scores[model]["total"]

    accuracy = correct / total * 100

    print(
        f"{model}: "
        f"{correct}/{total} = "
        f"{accuracy:.2f}%"
    )


# ------------------------------------------------------------
# Run-wise results
# ------------------------------------------------------------

print()
print("7. RUN-WISE CORRECTED RESULTS")
print("-" * 70)

for model in sorted(corrected_scores):

    print(model)

    for run in ["1", "2", "3"]:

        result = run_scores[(model, run)]

        accuracy = (
            result["correct"] /
            result["total"]
        ) * 100

        print(
            f"  Run {run}: "
            f"{result['correct']}/{result['total']} = "
            f"{accuracy:.2f}%"
        )


# ------------------------------------------------------------
# Variability
# ------------------------------------------------------------

print()
print("8. RUN-TO-RUN VARIABILITY")
print("-" * 70)

for model in sorted(variability):

    percentages = run_percentages[model]

    print(
        f"{model}:"
    )

    print(
        "  Run accuracies: "
        + str([
            round(value, 2)
            for value in percentages
        ])
    )

    print(
        f"  Mean: "
        f"{variability[model]['mean']:.2f}%"
    )

    print(
        f"  Sample SD: "
        f"{variability[model]['std']:.2f} percentage points"
    )


# ------------------------------------------------------------
# Temperature
# ------------------------------------------------------------

print()
print("9. TEMPERATURE CONFIGURATION")
print("-" * 70)

for model in sorted(temperatures):

    values = sorted(temperatures[model])

    print(
        f"{model}: "
        + ", ".join(str(value) for value in values)
    )

if (
    temperatures.get("model-a") == {0.0}
    and temperatures.get("model-b") == {0.7}
):

    print()
    print(
        "WARNING: model and temperature are confounded."
    )

    print(
        "Model-A was always evaluated at temperature 0.0."
    )

    print(
        "Model-B was always evaluated at temperature 0.7."
    )


# ------------------------------------------------------------
# Unique-question benchmark
# ------------------------------------------------------------

print()
print("10. 50-UNIQUE-QUESTION BENCHMARK")
print("-" * 70)

print(
    f"Unique questions: "
    f"{len(unique_question_ids)}"
)

for model in sorted(unique_scores):

    correct = unique_scores[model]["correct"]
    total = unique_scores[model]["total"]

    accuracy = correct / total * 100

    print(
        f"{model}: "
        f"{correct}/{total} = "
        f"{accuracy:.2f}%"
    )


# ------------------------------------------------------------
# Benchmark comparison
# ------------------------------------------------------------

print()
print("11. BENCHMARK COMPARISON")
print("-" * 70)

a_56 = (
    corrected_scores["model-a"]["correct"]
    / corrected_scores["model-a"]["total"]
    * 100
)

b_56 = (
    corrected_scores["model-b"]["correct"]
    / corrected_scores["model-b"]["total"]
    * 100
)

a_unique = (
    unique_scores["model-a"]["correct"]
    / unique_scores["model-a"]["total"]
    * 100
)

b_unique = (
    unique_scores["model-b"]["correct"]
    / unique_scores["model-b"]["total"]
    * 100
)

print(
    f"56-record gap (A - B): "
    f"{a_56 - b_56:.2f} percentage points"
)

print(
    f"50-unique gap (A - B): "
    f"{a_unique - b_unique:.2f} percentage points"
)

print()
print(
    "Conclusion supported by the measurements:"
)

if abs(a_unique - b_unique) < 1e-9:

    print(
        "After removing duplicate question texts, "
        "both models have the same observed accuracy."
    )

print(
    "The original 82.1% vs 48.2% comparison is "
    "affected by the exact-match scoring method, "
    "incorrect answer-key entries, duplicated questions, "
    "and the model/temperature confounding."
)

print()
print("=" * 70)
print("END OF ANALYSIS")
print("=" * 70)