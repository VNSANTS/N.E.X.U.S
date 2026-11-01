# Cognitive Adaptation Engine (CAE)

**Status:** first local implementation; opt-in profile store and prompt-context builder. Not a trained cognitive model and not an autonomous psychological profiler.

## Purpose

Help N.E.X.U.S. collaborate more effectively with its user by adapting response length, explanation style, challenge level and disagreement style, while learning only from patterns that the user reviews.

## Boundaries

- Disabled by default. The user must explicitly enable it.
- Explicit preferences are accepted only from a user-supplied value.
- Behavioral patterns begin as proposals and are excluded from prompt context until the user confirms them.
- Rejected patterns are never used for adaptation.
- Raw conversations are not copied into the profile.
- No personality, intelligence, mental-health or other sensitive-trait diagnosis.
- Current instructions always override stored preferences.
- Disabling adaptation stops profile context from being supplied; it does not delete the profile.
- Profile data remains in the local SQLite database and is covered by the existing database handling policy.

## Initial preference schema

| Key | Allowed values |
|---|---|
| `response_length` | `short`, `medium`, `long` |
| `explanation_style` | `direct`, `step_by_step`, `conceptual` |
| `challenge_level` | `gentle`, `balanced`, `demanding` |
| `disagreement_style` | `candid`, `gentle` |

## Pattern lifecycle

`proposed -> confirmed | rejected`

A proposed pattern includes a concise description, rationale and confidence estimate. Only confirmed patterns can enter the adaptation context. The confidence value records uncertainty; it is not a probability that the pattern is objectively true. The user can reject a pattern that feels inaccurate or unhelpful.

## Runtime integration

`CognitiveAdaptation.build_context()` returns a compact instruction fragment only when the feature is enabled and at least one preference or confirmed pattern exists. The runtime may append this fragment to its system guidance. It does not grant tools, permissions, memory-write authority or additional autonomy.

The current offline runtime uses a MockProvider. This feature therefore provides a tested profile and context hook, not a claim that a live model already adapts in production.

## Next validation

- Run `python -m unittest discover -s tests -v`.
- Review opt-in and profile controls before connecting a real provider.
- Add authenticated per-user profile isolation before any multi-user deployment.
- Add explicit export/delete controls before persistent cloud synchronization.
