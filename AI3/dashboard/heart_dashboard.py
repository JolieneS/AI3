"""
heart_dashboard.py - Frontend HEART dashboard and cohort visualization UI

Simple matplotlib visualization of the five HEART metrics.
Run directly to print scores and display the bar chart.
"""

import matplotlib.pyplot as plt
from src.heart import compute_heart_metrics

if __name__ == "__main__":
    heart_scores = compute_heart_metrics()
    print(heart_scores)

    plt.figure(figsize=(6, 4))
    plt.bar(heart_scores.keys(), heart_scores.values(), color="teal")
    plt.title("HEART Framework Scores")
    plt.ylabel("Score")
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig("dashboard/heart_scores.png")
    plt.show()
