---
name: grill
description: Interview the user to pressure-test an idea or resolve consequential intent and product tradeoffs before design, when the answer could materially change the work.
---

# Grill

Clarify whether the proposed work solves the right problem and what it must achieve. Pressure-test assumptions with the user before locking in technical design. The main agent owns this conversation; research helpers may gather supporting facts but do not separately interview the user.

## When it earns its place

Use when the user asks to be interviewed or pressure-tested, or when an unresolved human choice could materially change substantial or consequential work: intended users, actual problem, scope, success, acceptable failure, or an expensive product tradeoff.

Do not start an interview merely because a feature is large. Clear requirements proceed to design and delivery. Small known edits stay direct. Technical facts that source, documentation, logs, or an authorized experiment can establish belong to [ground](../ground/SKILL.md) or [design](../design/SKILL.md), not a question for the user. A concrete narrow ambiguity may need one clarification rather than this full procedure.

## Conduct the conversation

Read the relevant context first and reuse answers already given. State the consequential uncertainty briefly, then ask one high-value question. Listen to the answer and choose the next question from what it changes. Use a small batch only when the questions are independent and the user prefers that format. Avoid fixed questionnaires, arbitrary question counts, and asking the user to repeat discoverable information.

Challenge the premise constructively. Distinguish the observed problem from the proposed solution; offer simpler alternatives and explain their tradeoffs. Test the assumption that would invalidate the idea first. Do not manufacture objections, use an adversarial persona, or prolong the interview to show rigor. Accept a well-supported decision and move forward.

Useful lines of inquiry, only when relevant:

- Who is blocked today, and what do they do instead?
- What outcome would make this worth shipping, and how would we observe it?
- What happens when the proposed behavior guesses wrong or fails?
- What is necessary in the first version, and what can be left out?
- Could an existing capability or smaller change achieve the same outcome?
- What evidence would make us reject or revise the approach?

Keep verified facts, user preferences, and untested assumptions distinct. Let evidence settle factual uncertainty. Reserve questions for choices the user owns. Do not invent an answer to a material pending question; continue independent work while awaiting it when possible.

## Stop and hand off

Stop when enough is known for the next decision, not when every imaginable question is answered. Return a compact brief scaled to the task: problem, intended outcome/users, constraints, non-goals, observable success criteria, and material assumptions or decisions still unresolved. Explain any recommendation to reduce scope, use an existing solution, or avoid the proposed change.

Feed the clarified intent to [design](../design/SKILL.md). Return to the user only for a new decision that materially changes the work; do not reopen settled answers without new evidence.

Grill does not grant or revoke implementation authorization. A discussion-only request stays read-only and ends with the brief. When implementation was already requested, proceed within that existing scope after blocking decisions are resolved; do not require a ceremonial approval merely because the interview ended. The brief itself authorizes no external action or scope expansion. Keep it in the conversation unless saving it is requested or already part of the authorized task.
