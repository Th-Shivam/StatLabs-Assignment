import statistics


# Correct answers from each run
model_a = [49 / 56, 49 / 56, 49 / 56]
model_b = [47 / 56, 50 / 56, 40 / 56]


# Convert to percentages
model_a = [x * 100 for x in model_a]
model_b = [x * 100 for x in model_b]


# Mean
mean_a = statistics.mean(model_a)
mean_b = statistics.mean(model_b)


# Sample standard deviation
std_a = statistics.stdev(model_a)
std_b = statistics.stdev(model_b)


print("=" * 60)
print("RUN-TO-RUN VARIABILITY")
print("=" * 60)

print()
print("Model-A")
print(f"Run accuracies : {[round(x, 2) for x in model_a]}")
print(f"Mean           : {mean_a:.2f}%")
print(f"Std deviation  : {std_a:.2f} percentage points")

print()
print("Model-B")
print(f"Run accuracies : {[round(x, 2) for x in model_b]}")
print(f"Mean           : {mean_b:.2f}%")
print(f"Std deviation  : {std_b:.2f} percentage points")