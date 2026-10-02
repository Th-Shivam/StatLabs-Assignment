from collections import Counter 
import csv 

with open('questions.csv', newline="" , encoding='utf-8') as f:
    reader = csv.DictReader(f)
    question_ids = [row['question_id'] for row in reader]

# Count frequency of each question ID
id_counts = Counter(question_ids)

# Find duplicate question IDs
duplicate_ids = []

for qid, frequency in id_counts.items():
    if frequency > 1:
        duplicate_ids.append(qid)

# Display results
print("Total question IDs:", len(question_ids))
print("Unique question IDs:", len(id_counts))
print("Duplicate question IDs:", duplicate_ids)

# Show frequency of duplicates
for qid in duplicate_ids:
    print(f"{qid}: {id_counts[qid]} occurrences")  