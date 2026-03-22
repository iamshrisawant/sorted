import os
import sys
import random

# Add root
sys.path.insert(0, os.path.abspath("."))
os.environ["SORTED_TEST_DATA_DIR"] = os.path.abspath("benchmark_data")

from evaluation.benchmark import setup_env, generate_noise, normalize, evaluate_phase

tr_docs, tr_labels = setup_env()
base_cases = [
    ("inv_1.txt", "Invoice for July Services", "Work/Finance"),
    ("err_1.txt", "Python StackTrace Error", "Work/Engineering"),
    ("fiscal.txt", "Fiscal Year End Summary", "Work/Finance"), 
    ("meds.txt", "Patient Clinical Report", "Personal/Medical"), 
    ("aws.txt", "AWS Cloud Server Monthly Cost", "Work/Finance"),
    ("python_fin.txt", "Python Script for calculating Taxes", "Work/Engineering"),
    ("hiring.txt", "New Developer Onboarding Checklist", "Work/HR"),
    ("random.txt", "Recipe for Chocolate Cake", "None") 
]
test_set_A = []
random.seed(42)
for _ in range(40): 
    for fname, content, exp in base_cases:
        test_set_A.append({
            "name": f"{random.randint(10000,99999)}_{fname}",
            "content": generate_noise(content),
            "label": normalize(exp)
        })

evaluate_phase("Phase A (Synthetic)", tr_docs, tr_labels, test_set_A)
