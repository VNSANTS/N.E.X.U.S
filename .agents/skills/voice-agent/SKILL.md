---
name: voice-agent
description: Design voice interaction flows for N.E.X.U.S., including turn-taking, interruption, and fallback behavior.
---
# Voice Agent
- Design explicit states: standby, listening, transcribing, thinking, speaking, interrupted, and error.
- Use push-to-talk as reliable baseline; wake-word detection is optional and must be privacy-conscious.
- Support barge-in: stop speech immediately when the user interrupts.
- Show or speak when audio is being captured; provide a clear mute/stop control.
- Keep short-term turn context separate from long-term memory.
- Do not claim voice runtime exists until STT, TTS, streaming, permissions, and tests are integrated.