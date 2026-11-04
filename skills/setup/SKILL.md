---
name: setup
description: Install, check, or repair Reefstack, or fix Reefstack skills not triggering in chats, automations, or cloud tasks. Use during onboarding or when the user asks why Reefstack did not run.
---

# Reefstack setup

This is onboarding or repair, never a prerequisite to ordinary engineering work. Reefstack is a set of skills; it has no hooks or settings. Report installation, which surfaces load the skills, and behavioral validation separately.

Follow the host's [install mechanics](../reefstack/harness/install.md): choose one install with the user, confirm what the host actually loaded and under which names, and repair scheduled prompts that do not name the coordinator.

A skill runs when a turn names it or the task clearly matches its description. Where Reefstack must apply on every turn, offer the single instruction line the install mechanics give; add it, or change any automation or committed repository file, only with the user's approval, and never edit global instructions silently.

From a Reefstack checkout, `python3 scripts/health.py` validates the files. It does not prove a host loaded them: confirm in a fresh chat that the skill list shows Reefstack, that an ordinary engineering request follows it, and that a small edit stays small.
