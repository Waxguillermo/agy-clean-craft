---
name: readme-craft
description: >-
  Enforces a visual, scannable, high-utility README standard built around 3 pillars:
  understandability (with Mermaid graphs, dataviz, or screenshots when useful),
  easy deployment (with uv), and newcomer utility. Activate whenever creating,
  updating, or reviewing a README.md or project overview document.
---

# README Craft Skill

Every `README.md` must optimize for **three goals**:
1. **Understandability** — A reader grasps what the project does and how its pieces fit together in under 30 seconds.
2. **Easy Deployment** — Anyone can install, configure, and run/deploy the project on the first try using `uv`.
3. **Utility for Newcomers** — A new developer immediately knows where the entrypoints are, how to use it on a real example, and how to test/modify it.

---

## Core Writing Rules

- **Cut the prose, keep the signal**: Avoid marketing fluff, filler paragraphs, or repetitive explanations. Use tables, bullet points, code blocks, and visuals instead of walls of text.
- **Use Visuals Whenever Useful**:
  - **Architecture / Data Flow / Pipelines**: Include a clean **Mermaid diagram** (`flowchart LR`, `flowchart TD`, `sequenceDiagram`, or `stateDiagram-v2`) showing how components interact or how data moves through the system.
  - **Data / ML / Analytics Projects**: Include a **data visualization**, sample chart (`xychart-beta` or embedded plot image), or a concise before/after table of real outputs.
  - **UI / CLI / Web Apps**: Include or link a **screenshot**, terminal capture, or GIF showing the actual interface or output.
  - *Rule of thumb*: Don't force a diagram on a trivial 20-line script, but whenever there is a workflow, pipeline, multi-module architecture, data output, or UI, show it visually.
- **Mermaid Syntax Safety**:
  - Always quote node labels containing parentheses or special characters: `A["Parser (uv)"] --> B["Database"]`.
  - Avoid HTML tags inside Mermaid labels.

---

## Standard README Structure

Adapt the sections below to the project (skip sections that don't apply, keep total length tight and scannable):

### 1. Title & 2-Sentence Pitch
```markdown
# <Project Name>

<1–2 crisp sentences explaining what this project does and the problem it solves.>
```

### 2. Visual Overview (When Useful)
Include the most helpful visual for the project type:
- **System / Pipeline Flow**:
  ```mermaid
  flowchart LR
      A["Input Data"] --> B["Core Engine"]
      B --> C["Output / API"]
  ```
- **Or Screenshot / DataViz**:
  `![Overview](docs/assets/overview.png)` or a sample output table/chart.

### 3. Quickstart & Deployment (`uv`)
Zero-friction commands to get running immediately:
```markdown
## Quickstart

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment (if needed)
cp .env.example .env

# 3. Run
uv run <main-command-or-entrypoint>
```
```
If the project deploys via Docker, systemd, or cloud CLI, include the exact 1-step deployment command right below.

### 4. Practical Usage Example
Show **one realistic input → output example** (CLI invocation, API call, or Python snippet) so newcomers see immediate utility.

### 5. Newcomer Map (Key Files & Configuration)
Instead of a giant `tree` dump, provide a compact table of only the files/env vars a newcomer actually cares about:

| Path / Variable | Purpose |
| :--- | :--- |
| `src/<pkg>/main.py` | Main entrypoint & CLI |
| `src/<pkg>/pipeline.py` | Core processing logic |
| `API_KEY` | Required in `.env` for external service |

### 6. Development & Testing
```markdown
## Development

```bash
uv run pytest
uvx ruff check . && uvx ruff format --check .
```
```

---

## Verification Checklist Before Finishing
- [ ] Can a newcomer understand the architecture/flow at a glance (is a Mermaid graph, dataviz, or screenshot included if the project has a workflow, data output, or UI)?
- [ ] Are all setup, run, and test commands copy-pasteable using `uv`?
- [ ] Is all verbose filler removed?
