# RepoMind AI - System Schemas

This document defines the contracts between ingestion, retrieval, agents, backend, and frontend layers.

---

# 1. Dependency Graph Schema

The dependency graph represents structural relationships inside a repository.

## Node Types

### File Node

Represents a source file.

```json
{
  "id": "file:src/auth/login.py",
  "type": "file",
  "path": "src/auth/login.py",
  "language": "python"
}