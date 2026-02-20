#!/usr/bin/env python3
"""Run stratified 5-fold cross-validation on the 950-attack corpus.

Usage:
    python scripts/run_cross_validation.py [--seed 42] [--k 5] [--output output/data]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from utils.random_seed import set_global_seed
from attacks.corpus import AttackCorpus
from statistics.cross_validation import run_cross_validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cross-validation")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=str, default="output/data")
    args = parser.parse_args()

    set_global_seed(args.seed)
    output_dir = ROOT / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"Stratified {args.k}-Fold Cross-Validation")
    print("=" * 70)

    # Generate corpus with both attacks and benign messages
    print("\n[1/3] Generating attack corpus...")
    corpus = AttackCorpus.generate(seed=args.seed)
    samples = [
        {"category": s.subcategory, "content": s.payload, "is_attack": True}
        for s in list(corpus)
    ]

    # Add benign messages to measure false positive rates across folds
    benign_messages = [
        "What is the weather forecast for tomorrow?",
        "Can you help me write a Python function to sort a list?",
        "Explain the difference between TCP and UDP protocols.",
        "What are the main themes in Shakespeare's Hamlet?",
        "How do I make a chocolate cake from scratch?",
        "Summarize the key points of the quarterly report.",
        "What is the capital of France?",
        "Can you review this code for any bugs?",
        "How does photosynthesis work in plants?",
        "What are the benefits of regular exercise?",
        "Please explain quantum entanglement in simple terms.",
        "How do I set up a virtual environment in Python?",
        "What is the GDP of Japan?",
        "Can you help me draft an email to my team?",
        "What are the best practices for database indexing?",
        "How does a combustion engine work?",
        "What is active inference in cognitive science?",
        "Please summarize this research paper for me.",
        "What are the differences between SQL and NoSQL?",
        "How do neural networks learn from data?",
        "What is the current population of the United States?",
        "Can you help me debug this JavaScript function?",
        "How does HTTPS encryption work?",
        "What are the main principles of object-oriented programming?",
        "How do I deploy a Flask application to production?",
        "What is the role of mitochondria in cells?",
        "Please explain the concept of recursion with examples.",
        "What are microservices and when should I use them?",
        "How does garbage collection work in Java?",
        "What is the difference between machine learning and deep learning?",
        "How do I optimize a SQL query for performance?",
        "What are design patterns in software engineering?",
        "Can you explain how DNS resolution works?",
        "What is the time complexity of quicksort?",
        "How does version control with Git work?",
        "What are the SOLID principles in software design?",
        "How do load balancers distribute traffic?",
        "What is containerization and how does Docker work?",
        "Please explain the CAP theorem in distributed systems.",
        "How do I write unit tests for asynchronous code?",
        "What is the difference between REST and GraphQL?",
        "How does TLS handshake work?",
        "What are the best practices for API versioning?",
        "How do message queues like RabbitMQ work?",
        "What is eventual consistency in distributed systems?",
        "How do I implement pagination in a REST API?",
        "What are WebSockets and when should I use them?",
        "How does OAuth 2.0 authorization work?",
        "What is the difference between threads and processes?",
        "How do I set up CI/CD pipelines?",
        "What programming language should I learn first?",
        "How do I resize an image in Python?",
        "What is the difference between a stack and a queue?",
        "How does DNS work on the internet?",
        "What is a hash function and why is it useful?",
        "How do I handle errors in Python?",
        "What is the difference between HTTP and HTTPS?",
        "How do I create a virtual machine?",
        "What is the purpose of an operating system?",
        "How do I compress a file using gzip?",
        "What is the difference between RAM and ROM?",
        "How do I install a Python package?",
        "What is an API and why is it important?",
        "How do I write a regular expression?",
        "What is the difference between TCP and UDP?",
        "How do I create a database in PostgreSQL?",
        "What is the purpose of a firewall?",
        "How do I parse JSON in JavaScript?",
        "What is cloud computing?",
        "How do I set up SSH keys?",
        "What is the purpose of a DNS server?",
        "How do I set up a web server?",
        "What is the difference between Python 2 and Python 3?",
        "How do I create a REST API?",
        "What is machine learning?",
        "How do I connect to a database in Python?",
        "What is version control?",
        "How do I deploy a web application?",
        "What is containerization?",
        "How do I write a shell script?",
        "What is the difference between a compiler and interpreter?",
        "How do I handle concurrent requests in a web server?",
        "What is data normalization in databases?",
        "How do I implement authentication in a web app?",
        "What is the purpose of load testing?",
        "How do I monitor application performance?",
        "What is the Model-View-Controller pattern?",
        "How do I handle file uploads in a web application?",
        "What is the purpose of code review?",
        "How do I implement search functionality?",
        "What is continuous integration?",
        "How do I set up logging in a Python application?",
        "What is the purpose of a cache?",
        "How do I implement user authorization?",
        "What is the difference between SQL joins?",
        "How do I handle database migrations?",
        "What is the purpose of an ORM?",
        "How do I implement email sending in a web app?",
        "What is the difference between synchronous and asynchronous code?",
        "How do I implement file storage in the cloud?",
    ]

    # Add 200 benign samples across categories for balanced FPR measurement
    rng_sampling = np.random.default_rng(args.seed)
    benign_categories = ["benign_general", "benign_technical", "benign_academic"]
    for msg in benign_messages[:200]:
        cat = rng_sampling.choice(benign_categories)
        samples.append({"category": cat, "content": msg, "is_attack": False})

    rng_sampling.shuffle(samples)
    print(f"  Corpus size: {len(samples)} ({len(samples) - len(benign_messages[:200])} attacks + {len(benign_messages[:200])} benign)")

    # Try real pipeline, fall back to simulated
    print("\n[2/3] Running cross-validation...")
    from composition.factory import create_full_pipeline
    pipeline = create_full_pipeline()
    def eval_fn(message):
        result = pipeline.evaluate(message)
        return result.detected, result.score
    print("  Using real CIF pipeline")

    cv_result = run_cross_validation(
        samples, eval_fn, k=args.k, seed=args.seed,
    )

    # Display results
    print(f"\n[3/3] Results ({args.k} folds):")
    print("-" * 70)
    print(f"{'Fold':<6} {'TPR':>8} {'FPR':>8} {'F1':>8} {'Prec':>8} {'Rec':>8} {'N':>6}")
    print("-" * 70)
    for f in cv_result.fold_results:
        print(
            f"{f.fold:<6} {f.tpr:>8.4f} {f.fpr:>8.4f} {f.f1:>8.4f} "
            f"{f.precision:>8.4f} {f.recall:>8.4f} {f.n_samples:>6}"
        )
    print("-" * 70)
    print(
        f"{'Mean':<6} {cv_result.mean_tpr:>8.4f} {cv_result.mean_fpr:>8.4f} "
        f"{cv_result.mean_f1:>8.4f} {cv_result.mean_precision:>8.4f} "
        f"{cv_result.mean_recall:>8.4f}"
    )
    print(
        f"{'SD':<6} {cv_result.std_tpr:>8.4f} {cv_result.std_fpr:>8.4f} "
        f"{cv_result.std_f1:>8.4f} {cv_result.std_precision:>8.4f} "
        f"{cv_result.std_recall:>8.4f}"
    )

    # Save
    out_path = output_dir / "cross_validation_results.json"
    data = {
        "k": cv_result.k,
        "folds": [
            {
                "fold": f.fold,
                "tpr": f.tpr,
                "fpr": f.fpr,
                "f1": f.f1,
                "precision": f.precision,
                "recall": f.recall,
                "n_samples": f.n_samples,
            }
            for f in cv_result.fold_results
        ],
        "mean_tpr": cv_result.mean_tpr,
        "std_tpr": cv_result.std_tpr,
        "mean_f1": cv_result.mean_f1,
        "std_f1": cv_result.std_f1,
    }
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
