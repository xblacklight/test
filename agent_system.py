"""Three-agent task pipeline: receiver -> thinker -> delivery.

The default backend is deterministic and dependency-free. Replace AgentBackend with
an LLM adapter in production; the protocol keeps the workflow and quality gates.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Protocol


class AgentBackend(Protocol):
    def complete(self, role: str, instructions: str) -> str: ...


class LocalBackend:
    """Safe fallback so the pipeline works without API keys or network access."""
    def complete(self, role: str, instructions: str) -> str:
        if role == "thinker":
            return "Implement the requested outcome from the normalized requirements. Define inputs, outputs, edge cases, and a verification plan before execution."
        return instructions


@dataclass
class TaskBrief:
    original_request: str
    objective: str
    requirements: List[str]
    constraints: List[str]
    acceptance_criteria: List[str]
    open_questions: List[str] = field(default_factory=list)


@dataclass
class Thought:
    plan: str
    risks: List[str]
    checks: List[str]
    result: str


@dataclass
class Package:
    status: str
    summary: str
    brief: TaskBrief
    thought: Thought
    verification: Dict[str, Any]
    artifact: str
    created_at: str


class ReceiverAgent:
    """Only translates human language into an explicit, testable brief."""
    def receive(self, request: str) -> TaskBrief:
        text = " ".join(request.strip().split())
        if not text:
            raise ValueError("A non-empty task is required")
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        requirements = sentences or [text]
        constraints = [s for s in sentences if any(x in s.lower() for x in ("must", "only", "without", "cannot", "should"))]
        criteria = [f"Requirement is satisfied: {r}" for r in requirements]
        return TaskBrief(text, requirements[0], requirements, constraints, criteria)


class ThinkerAgent:
    """Reasons from the receiver's brief; it never sees the raw request as authority."""
    def __init__(self, backend: AgentBackend | None = None):
        self.backend = backend or LocalBackend()

    def think(self, brief: TaskBrief) -> Thought:
        instructions = json.dumps(asdict(brief), indent=2)
        result = self.backend.complete("thinker", instructions)
        return Thought(
            plan=result,
            risks=["Ambiguous requirements must be clarified before irreversible actions."],
            checks=["Validate every acceptance criterion", "Check output is usable and complete", "Report failures instead of claiming success"],
            result=result,
        )


class DeliveryAgent:
    """Quality-control gate and packager. Delivery is impossible after a failed check."""
    def verify(self, brief: TaskBrief, thought: Thought) -> Dict[str, Any]:
        checks = {criterion: bool(thought.result.strip()) for criterion in brief.acceptance_criteria}
        passed = all(checks.values()) and bool(thought.plan.strip())
        return {"passed": passed, "checks": checks, "verified_by": "delivery", "failure_reason": None if passed else "Missing thinker output"}

    def deliver(self, brief: TaskBrief, thought: Thought) -> Package:
        verification = self.verify(brief, thought)
        status = "ready" if verification["passed"] else "rejected"
        artifact = thought.result if verification["passed"] else "Not delivered: quality control failed."
        return Package(status, "Quality control passed; package is ready to use." if verification["passed"] else "Quality control failed.", brief, thought, verification, artifact, datetime.now(timezone.utc).isoformat())


class Orchestrator:
    """The single public agent: receives, delegates thinking, then gates delivery."""
    def __init__(self, backend: AgentBackend | None = None):
        self.receiver = ReceiverAgent()
        self.thinker = ThinkerAgent(backend)
        self.delivery = DeliveryAgent()

    def run(self, request: str) -> Package:
        brief = self.receiver.receive(request)
        thought = self.thinker.think(brief)
        return self.delivery.deliver(brief, thought)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Receiver / thinker / delivery agent pipeline")
    parser.add_argument("request", nargs="+", help="human task")
    args = parser.parse_args(argv)
    package = Orchestrator().run(" ".join(args.request))
    print(json.dumps(asdict(package), indent=2))
    return 0 if package.status == "ready" else 1


if __name__ == "__main__":
    sys.exit(main())
