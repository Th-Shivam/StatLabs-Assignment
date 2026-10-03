import csv

question_to_ids = {}

with open("questions.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        question = row["question"]
        qid = row["question_id"]

        if question not in question_to_ids:
            question_to_ids[question] = []

        question_to_ids[question].append(qid)


# Print only duplicate questions
duplicate_count = 0

for question, ids in question_to_ids.items():
    if len(ids) > 1:
        duplicate_count += 1
        print(f"{question}: {ids}")


# Summary
total_questions = sum(len(ids) for ids in question_to_ids.values())
unique_questions = len(question_to_ids)

print("\n--- Summary ---")
print(f"Total question records: {total_questions}")
print(f"Unique questions: {unique_questions}")
print(f"Duplicate question texts: {duplicate_count}")
print(f"Extra repeated records: {total_questions - unique_questions}")