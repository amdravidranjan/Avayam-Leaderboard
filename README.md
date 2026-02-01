# Avayam Leaderboard

This repository stores the leaderboard results for the **Avayam Green Agent**, a benchmark for evaluating AI agents on their ability to repair software vulnerabilities using similarity scoring against expert fixes.

## Structure

- `scenario.toml`: Configuration for the AgentBeats scenario runner.
- `results/`: Contains the collected assessment results in JSON format.

## Green Agent

The green agent runs the Avayam benchmark, which:
1. Provisions a Dockerized environment with vulnerable code (MSR Dataset + Synthetic Variants).
2. Scores the patch based on **Security Integrity** (Static Analysis) and **Expert Similarity** (Tree-sitter AST Comparison).
3. Returns a similarity score indicating how close the agent's fix is to the ground truth.
