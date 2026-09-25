# Three-agent task pipeline

A single public `Orchestrator` coordinates three isolated roles:

1. **Receiver** — accepts human wording, normalizes it, and creates a structured `TaskBrief` with requirements, constraints, acceptance criteria, and open questions. It does not solve the task.
2. **Thinker** — receives only the structured brief and produces a plan, risks, checks, and proposed result. Plug an LLM into `AgentBackend.complete()` when desired.
3. **Delivery** — independently verifies the thinker's output against every acceptance criterion. It returns a ready-to-use `Package` only when quality control passes; otherwise it returns `rejected` and does not deliver the artifact.

## Run

No dependencies are required:

```bash
python agent_system.py "Build a service that validates customer emails. It must return JSON."
python -m unittest -v
```

The built-in backend is intentionally deterministic so the workflow can be tested offline. For an LLM, implement:

```python
class MyBackend:
    def complete(self, role, instructions):
        # send `instructions` to your model and return plain text
        ...

package = Orchestrator(MyBackend()).run("human request")
```

The raw human request is authoritative only at the receiver boundary. The thinker gets the receiver's JSON-shaped brief, and delivery is a hard quality-control gate.
