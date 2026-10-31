# Project Status

**Stage:** planning baseline; technical audit pending.  
**Implementation:** no runtime implementation has been verified in this repository.

## Confirmed direction
- Personal AI assistant beyond a conventional chatbot.
- Cloud-first runtime accessible from phone/browser.
- Local Ollama is optional, not a hard requirement.
- Interactive activation by text, button or voice.
- Lightweight event-driven standby; no continuous LLM reasoning loop.
- Approved scheduled and event-triggered task execution.
- Modular agents, tools and multi-provider model routing.
- Separate personal memory and sourced knowledge.
- Learning through research, validation, user clarification and evaluated workflows.
- Explicit approval for sensitive actions; sandboxed self-improvement.

## Environment constraints
Development PC reported: Intel i5 first generation, 8 GB DDR3 RAM, HDD. Ollama, VS Code and Codex CLI are available. Avoid requiring large local models. Cloud hosting and model costs are not selected.

## Next milestone: OpenJarvis audit
1. Inspect source tree, docs, dependencies and license.
2. Identify working features, partial features, placeholders and broken paths.
3. Run existing tests/startup checks where practical.
4. Map reusable components to N.E.X.U.S. requirements.
5. Produce AUDIT_REPORT.md and a minimal phased implementation proposal.
6. Make no broad code changes until the user reviews and approves the audit.

## Open risks
- OpenJarvis version, capabilities and license are not yet verified.
- Cloud model usage can create recurring costs; background jobs need budgets.
- Learning must not be misrepresented as permanent model-weight training.
- Public repository: never commit secrets, private conversation exports, credentials or personal records.

## Audit checklist
- [ ] Stack and repository structure documented.
- [ ] License and attribution checked.
- [ ] Functional code separated from placeholders.
- [ ] Tests and run instructions verified.
- [ ] Reuse/gap analysis completed.
- [ ] Architecture and first sprint proposed.
