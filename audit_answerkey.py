import csv
import re

# question_id -> question
questions = {}

with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        questions[row["question_id"]] = row["question"]


correct_count = 0
incorrect_count = 0
incorrect_ids = []

# Store independently calculated answers
calculated_answers = []

# Read answer key and audit
with open("answer_key.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        qid = row["question_id"]
        expected = int(row["expected"])

        question = questions[qid]

        # Extract first number, operator, second number
        match = re.search(r"(\d+)\s*([+×−-])\s*(\d+)", question)

        if not match:
            print(f"{qid}: Could not parse question")
            continue

        first_number = int(match.group(1))
        operator = match.group(2)
        second_number = int(match.group(3))

        # Calculate actual answer
        if operator == "+":
            calculated = first_number + second_number

        elif operator in ("−", "-"):
            calculated = first_number - second_number

        elif operator == "×":
            calculated = first_number * second_number

        # Save calculated answer
        calculated_answers.append({
            "question_id": qid,
            "calculated_answer": calculated
        })

        # Strict comparison with original answer key
        if calculated == expected:
            status = "CORRECT"
            correct_count += 1
        else:
            status = "INCORRECT"
            incorrect_count += 1
            incorrect_ids.append(qid)

        print(
            f"{qid} | {question} | "
            f"Calculated: {calculated} | "
            f"Expected: {expected} | "
            f"{status}"
        )


# Write calculated answers to CSV
with open("calculated_answers.csv", "w", encoding="utf-8") as f:

    f.write("question_id,calculated_answer\n")

    for row in calculated_answers:
        f.write(f"{row['question_id']},{row['calculated_answer']}\n")


# Final summary
total_checked = correct_count + incorrect_count

print("\n" + "=" * 50)
print("ANSWER KEY AUDIT SUMMARY")
print("=" * 50)

print(f"Total questions checked : {total_checked}")
print(f"Correct answer keys     : {correct_count}")
print(f"Incorrect answer keys   : {incorrect_count}")

if total_checked > 0:
    accuracy = (correct_count / total_checked) * 100
    print(f"Answer key accuracy     : {accuracy:.2f}%")

print(f"Incorrect question IDs  : {incorrect_ids}")
print("\nCalculated answers saved to: calculated_answers.csv")