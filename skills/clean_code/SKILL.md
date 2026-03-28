---
name: clean-code
description: Applies principles from Robert C. Martin's Clean Code. Use when writing, reviewing, or refactoring code to ensure readability, maintainability, and quality. Covers naming, functions, comments, formatting, error handling, and testing.
risk: safe
source: "ClawForge (https://github.com/jackjin1997/ClawForge)"
date_added: "2026-02-27"
---

## 📌 Overview

This skill embodies the principles of *Clean Code* by Robert C. Martin. It transforms "code that works" into "code that is clean" — readable, maintainable, and honest about its intent.

> *"Code is clean if it can be read, and enhanced by a developer other than its original author."* — Grady Booch

---

## ✅ When to Use

- Writing new code — enforce quality from the start
- Reviewing pull requests — provide principle-based feedback
- Refactoring legacy code — identify and remove code smells
- Improving team standards — align on industry best practices

---

## 📐 Core Principles

### 1. Meaningful Names
- **Intention-revealing**: `elapsedTimeInDays` not `d`
- **No disinformation**: Don't call it `accountList` if it's a `Map`
- **No noise words**: Avoid `ProductData` vs `ProductInfo`
- **Pronounceable & searchable**: Avoid `genymdhms`
- **Classes** → nouns (`Customer`, `WikiPage`). Avoid `Manager`, `Data`
- **Methods** → verbs (`postPayment`, `deletePage`)

---

### 2. Functions
- **Small**: Shorter than you think — aim for < 20 lines
- **Do one thing**: One function, one responsibility
- **One abstraction level**: Don't mix business logic with regex/string parsing
- **Descriptive names**: `isPasswordValid` beats `check`
- **Arguments**: 0 ideal · 1–2 acceptable · 3+ needs strong justification
- **No side effects**: Don't secretly mutate global state

---

### 3. Comments
Comments are a failure to express yourself in code. Prefer:

```python
# Bad: comment explaining unclear code
if employee.flags & HOURLY and employee.age > 65:

# Good: code that explains itself
if employee.isEligibleForFullBenefits():
```

**Good comments**: legal notices, regex intent, clarification of external library behavior, TODOs
**Bad comments**: redundant, misleading, noise, position markers, mandated headers

---

### 4. Formatting
- **Newspaper metaphor**: High-level concepts at top, details at bottom
- **Vertical density**: Related lines stay close together
- **Variable proximity**: Declare variables near their first use
- **Consistent indentation**: Non-negotiable for structural readability

---

### 5. Objects & Data Structures
- **Hide implementation**: Expose behaviour through interfaces, not internals
- **Law of Demeter**: Don't chain — avoid `a.getB().getC().doSomething()`
- **DTOs**: Public variables, no functions — used for data transfer only

---

### 6. Error Handling
- **Use exceptions, not return codes**: Keeps the happy path clean
- **Write try-catch-finally first**: Defines the transactional scope
- **Never return null**: Forces callers into null-check hell
- **Never pass null**: Leads to `NullPointerException` at a distance

---

### 7. Unit Tests — F.I.R.S.T.

| Letter | Principle |
|--------|-----------|
| **F** | Fast — tests must run quickly |
| **I** | Independent — no test depends on another |
| **R** | Repeatable — same result in any environment |
| **S** | Self-validating — pass or fail, no manual inspection |
| **T** | Timely — written before or alongside production code |

**TDD Three Laws:**
1. Don't write production code until you have a failing test
2. Don't write more test than is sufficient to fail
3. Don't write more production code than is sufficient to pass

---

### 8. Classes
- **Single Responsibility Principle (SRP)**: One reason to change
- **Small**: If you can't summarize the class in ~25 words without "and", it's too big
- **Stepdown rule**: Code reads like a top-down narrative

---

### 9. Code Smells

| Smell | Symptom |
|-------|---------|
| **Rigidity** | Hard to change — one change cascades |
| **Fragility** | Breaks in many places from one change |
| **Immobility** | Hard to reuse components elsewhere |
| **Viscosity** | Easier to do the wrong thing than the right thing |
| **Needless complexity** | Over-engineered for current needs |
| **Needless repetition** | Same logic copied instead of extracted |

---

## 🛠️ Pre-Commit Checklist

- [ ] Is this function < 20 lines?
- [ ] Does this function do exactly one thing?
- [ ] Are all names searchable and intention-revealing?
- [ ] Have I replaced comments with clearer code?
- [ ] Are there ≤ 2 function arguments?
- [ ] Are exceptions used instead of return codes?
- [ ] Is there a failing test for this change?
- [ ] Does each class have a single responsibility?

---

## 🤖 Instructions for Antigravity Agent

When this skill is active, apply the following guidelines to every code task:

1. **Name everything clearly**: Flag single-letter variables, vague nouns (`data`, `info`, `manager`), and non-searchable abbreviations. Always suggest a cleaner alternative.
2. **Function size enforcement**: Flag any function exceeding 20 lines and suggest extraction points.
3. **Single responsibility check**: Before writing a function or class, state what its one responsibility is. If it has two, split it.
4. **Comment audit**: Replace any comment that explains *what* the code does with code that explains itself. Only keep comments that explain *why*.
5. **Null safety**: Never write a function that returns `null` or accepts `null` as a parameter without explicit justification.
6. **Error handling**: Always use exceptions over error codes. Wrap risky operations in try-catch-finally.
7. **Test-first reminder**: Before implementing a non-trivial function, prompt the user about writing the test first (TDD).
8. **Law of Demeter**: Flag method chains longer than 2 levels and suggest introducing a mediator or query method.
9. **Code smell identification**: During refactoring, explicitly name the smell being addressed (e.g., "This is a Rigidity smell — removing the tight coupling here…").
10. **Checklist on completion**: After writing or refactoring significant code, run through the pre-commit checklist and report any items that were intentionally deferred.
