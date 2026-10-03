import csv

question_to_ids = {}

# Read questions.csv
with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        question = row["question"]
        qid = row["question_id"]

        if question not in question_to_ids:
            question_to_ids[question] = []

        question_to_ids[question].append(qid)


# Read answer_key.csv
answer_key = {}

with open("answer_key.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        answer_key[row["question_id"]] = row["expected"]


# Check duplicate questions and compare their answers
duplicate_count = 0

for question, ids in question_to_ids.items():

    if len(ids) > 1:
        duplicate_count += 1

        print(f"\nQuestion: {question}")
        print(f"Question IDs: {ids}")

        answers = []

        for qid in ids:
            answer = answer_key[qid]
            answers.append(answer)
            print(f"{qid} -> {answer}")

        # Check whether all expected answers are the same
        if len(set(answers)) == 1:
            print("Answer key: CONSISTENT")
        else:
            print("Answer key: INCONSISTENT")


# Summary
total_questions = sum(len(ids) for ids in question_to_ids.values())
unique_questions = len(question_to_ids)

print("\n--- Summary ---")
print(f"Total question records: {total_questions}")
print(f"Unique questions: {unique_questions}")
print(f"Duplicate question texts: {duplicate_count}")
print(f"Extra repeated records: {total_questions - unique_questions}")