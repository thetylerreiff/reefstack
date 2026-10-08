---
name: design
description: Establish caller-first contracts, ownership, acceptance criteria, and fixtures for substantial changes or uncertain component boundaries.
---

# Design

Write how callers will use the behavior before choosing types and module boundaries. Prefer the existing architecture and the smallest durable change. Define shared shapes once and make downstream work point to that authoritative contract.

Set observable acceptance criteria and representative fixtures, including the variants that cross boundaries. Name independent pieces, shared writes, and blocking assumptions. A list of exclusive files is not proof of independence.

For an unfamiliar integration, prove a thin representative path before dependent fan-out when implementation is authorized. For a snapshot pipeline, verify collection, normalization, persistence input, and consumption against one common fixture. In read-only design work, report the proposed probe rather than performing unauthorized writes.

Explore alternatives only when evidence cannot settle a consequential choice cheaply. Use parallel design attempts for expensive uncertainty, not every function boundary. Evaluate candidates against explicit criteria and keep the synthesized result coherent; do not mechanically combine incompatible designs.

Output the contract, ownership, acceptance checks, fixtures, and unresolved blockers at a scale proportionate to the task. Repeated implementation deviations signal a contract problem: re-ground and revise the shape rather than bolt on workarounds.
