---
name: writing-tests-that-can-fail
description: >-
  Use when writing, reviewing or fixing tests in any language or framework:
  before committing tests, when about to mock or stub a dependency, when a new
  test passes on its first run, when coverage looks high but bugs still ship,
  or when an existing test goes red and the quick fix would be to change the
  test instead of the code.
  Triggers: "write tests", "add unit tests", "review these tests", "make the
  tests pass", "fix the failing test", "increase coverage", "mock this".
license: MIT
metadata:
  version: "1.0.1"
  author: IonDen
---

# Writing tests that can fail

## The rule

**A test earns its place only if you can name the one-line bug that turns it red.** If you can't name it, the test is decoration: delete it or rewrite it.

You will be pulled toward green. Green is not the goal; a suite that fails on the bugs it exists to catch is. Coding agents mock more than people do: 36% of their commits add mocks, against 26% for other commits (Hora & Robbes, 2026). They also take expected values from what the code returns now. And when a test fails, they hard-code the expected value or edit the test until it passes. Every rule below is aimed at one of those habits.

**Violating the letter of these rules is violating the spirit.**

## Is it worth a test?

For each test you are about to write:

1. **Name the bug** a caller or user would see. No bug, no test.
2. **Classify the code.**
   - Logic with few collaborators (rules, calculations, parsers): thorough tests, every condition.
   - Glue that wires collaborators together: a few tests through the real wiring.
   - Trivia gets no test. That covers plain data holders and their fields, assign-only constructors, stubs that raise "not implemented", constants restated as literals, and framework or language behaviour.
3. **Test behaviour, not structure.** Assert what a caller can observe. Don't assert the order of internal calls, private fields or helper methods; those tests break on refactors and catch nothing.

The full rule, and the exceptions that bring trivia back in: `references/worth-testing.md`.

## Test real behaviour

Classify every collaborator of the unit under test:

| Tier | Collaborator | Use |
|---|---|---|
| 1 | The unit under test and its own logic | Always the real thing |
| 2 | Owned, deterministic, in-process (value objects, parsers, pure helpers) | The real thing |
| 3 | Owned adapters over slow or nondeterministic resources (a repository over a database, a clock, an HTTP client wrapper) | A fake: a small in-memory implementation of the same interface. Or a stub |
| 4 | Boundaries you don't own (network, wall clock, filesystem, randomness, paid APIs) | A fake or a stub. A mock only to verify an unavoidable outgoing side effect |

Preference order, always: **real → fake → stub → mock.**

- **Never** mock the unit under test or its tier 1–2 collaborators.
- **Never** make a call check (`was called with`, call counts, call order) the main assertion. Assert the state or output the caller sees: the record saved in the fake, the message in the fake outbox, the value returned.
- **Expected values and boundary inputs are literals from the spec**: the docstring, the ticket, a worked example. Never build them from the code's own constants, helpers or current output. `expect discounted(item) == MEMBER_PRICE` passes when `MEMBER_PRICE` is wrong. `expect discounted(item) == 8.50` does not. The same holds for inputs: a boundary test at `MAX_ITEMS + 1` moves when `MAX_ITEMS` moves, so it can't catch a wrong `MAX_ITEMS`.
- **Deterministic:** inject the clock, seed randomness, don't depend on test order, poll with a timeout instead of sleeping.
- **Snapshots:** a snapshot is a test only if a reviewer can read it, it is normalised, and updating it takes a reviewed diff.

```
WRONG  svc = Service(client = MOCK)
       svc.recommend("Oslo")
       expect MOCK.current_temp.called_with("Oslo")      # tests the mock

RIGHT  svc = Service(FakeClient(temp = 4.0))
       expect svc.recommend("Oslo") == "bring a coat"      # tests behaviour
       expect Service(FakeClient(temp = 10.0)).recommend("Oslo") == "no coat needed"
       # the boundary: flip `< 10` to `<= 10` and this goes red
```

## Cover every condition

This applies to the units step 2 kept. Glue gets its few integration tests, and trivia gets none.

- **Partitions:** one test per class of input the spec treats differently, invalid ones included. Put one invalid value in each test.
- **Boundaries:** three values per boundary: just below, on, just above (x-1, x, x+1).
- **Compound conditions:** for each part of `a and b or c`, a pair of tests that differ only in that part and give different results. That's about n+1 tests for n parts. Branch coverage can be met with two tests that prove none of this.
- **Error paths:** trigger each failure the unit can see and assert what the caller observes (the error raised or returned, the state rolled back). "It didn't crash" is not an assertion.
- **Edges:** empty, zero, one, many, maximum; negative; NaN; Unicode; duplicates; time zones and DST; concurrent calls; calling twice.

Techniques, the full edge set and a worked condition-pair table: `references/edge-cases.md`.

## Prove it can fail

Before you keep a test, break the code on purpose and watch the test go red:

- flip a comparison (`<` to `<=`, `>=` to `>`);
- shift a constant or boundary by one;
- swap `and` and `or`;
- replace a condition with `true` or `false`;
- delete a call or a line;
- return early or return a constant;
- swallow an error instead of raising it.

Or run the ecosystem's mutation tool (`references/languages/<language>.md` names it). Every mutant that survives gets a new test, or a written reason it is equivalent (no observable difference) or not worth catching. A test that passed on its first run, before you ever saw it fail, has proved nothing yet.

## When a test goes red

A red test is information. Decide from the spec, not from the code, which one is wrong.

- **Inside a fix, never:**
  - change a test's expected value, tolerance, input or skip status;
  - special-case the test's input in the code;
  - swallow the error;
  - exit or return early;
  - touch the test runner or its config.
- **If the spec shows the test is wrong,** stop and report it: the spec line, the value you measured, the cause. Change the test only as a separate, labelled change the user agrees to. That is a correct outcome, not a failure.
- **A tolerance moves** only with a measurement that shows the old bound was wrong, never to whatever value now passes.
- **After three failed attempts** on the same failure, stop and report what you tried. Don't keep iterating toward green.

| Excuse | Reality |
|---|---|
| "The test is obviously outdated" | Then the spec says so. Quote it and report. Don't edit it inside the fix. |
| "Just this once, to unblock" | An edited oracle ships the bug with a green badge. |
| "The expected value was a typo" | Maybe. Show where the right value comes from, in a separate change. |
| "The tolerance was always too tight" | Measure it. If you're widening it to the number you got, that's the cheat. |

The trickier ways to turn a test green without fixing anything (copied oracles, special-cased inputs, always-equal objects, patched runners and more) are in `references/cheating-patterns.md`. None is ever acceptable, and each entry says how to spot it in review.

## Keep-or-kill checklist

For every test, new or existing:

1. Can it fail? Name the one-line bug.
2. Does it test behaviour through the public surface, not internals or call order?
3. Is the unit under test real, not mocked?
4. Does the main assertion pin output or state, with an expected value from the spec, not a mock call or a value computed from the code?
5. Would it survive a refactor that keeps behaviour?
6. Is it at the cheapest level that still catches the bug, with no heavy test standing in for a missing cheap one?

Any "no": rewrite it or delete it.

## References

- `references/worth-testing.md`: deciding what deserves a test, and the exceptions.
- `references/edge-cases.md`: partitions, boundaries, condition pairs, the edge set, properties.
- `references/cheating-patterns.md`: load when reviewing a red-to-green diff, or before changing a failing test.
- `references/smell-catalog.md`: named test smells with before/after fixes.
- `references/rationalizations.md`: excuses for keeping bad tests, and the reality.
- `references/evidence.md`: the studies behind these rules.
- `references/languages/<language>.md`: runners, fakes, mock libraries, property and mutation tools, and red-flag commands per ecosystem.
