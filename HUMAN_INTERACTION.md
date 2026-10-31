# Human Interaction

## Channels
Target text chat, explicit voice activation/push-to-talk, quick activation button, task notifications and responsive browser/mobile interface. Start with the simplest reliable channel in the audited codebase.

## Lifecycle
Standby waits for explicit activation or approved trigger. Interactive mode loads session state and relevant context. Clarify ambiguity before consequential actions. Show progress and request approvals. Summarize results and return to standby according to user settings.

## Approval request must show
- Exact action and parameters.
- Tool, account or resource involved.
- Expected consequences and reversibility.
- Cost and privacy impact.
- Approve, reject and cancel controls.

Approval is scoped to the described action, not blanket permission for future actions.

## Voice
Start with push-to-talk. Make microphone state visible; provide mute/stop; avoid hidden always-on recording; explain speech processing and provider retention; support interruption and cancellation.

## Proactive notifications
Respect quiet hours, urgency, configured frequency and per-agent rules. Avoid noisy or unnecessary notifications.
