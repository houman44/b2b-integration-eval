# Representative transcripts

Rendered by `python -m harness.transcripts` from the raw records of the release runs (4 November 2026). Long replies are shortened in the middle; the raw record holds the full text.

| Transcript | Mode | Model | Why |
|---|---|---|---|
| [T1](diagnosis-T1__google__gemini-4-argon__t1.md) | diagnosis | google/gemini-4-argon | T1 had no failures; one pass |
| [T2](diagnosis-T2__deepseek__deepseek-v4.1-flash-1017__t1.md) | diagnosis | deepseek/deepseek-v4.1-flash-1017 | failure: reply ran to the token limit |
| [E1](diagnosis-E1__anthropic__claude-haiku-5.5__t2.md) | diagnosis | anthropic/claude-haiku-5.5 | failure: no sender-side fault found |
| [E3](diagnosis-E3__anthropic__claude-fable-5.1__t1.md) | diagnosis | anthropic/claude-fable-5.1 | E3 had no failures; one pass |
| [R1](diagnosis-R1__deepseek__deepseek-v4.1-flash-1017__t2.md) | diagnosis | deepseek/deepseek-v4.1-flash-1017 | failure: reply ran to the token limit |
| [R2](diagnosis-R2__openai__gpt-6-astra__t1.md) | diagnosis | openai/gpt-6-astra | layer 'envelope': failed before the R2 ruling, passes after it |
| [S1](diagnosis-S1__anthropic__claude-haiku-5.5__t1.md) | diagnosis | anthropic/claude-haiku-5.5 | near miss: location without the APP. prefix |
| [U1](diagnosis-U1__anthropic__claude-haiku-5.5__t2.md) | diagnosis | anthropic/claude-haiku-5.5 | failure: definite cause where the evidence does not decide |
| [U2](diagnosis-U2__anthropic__claude-haiku-5.5__t2.md) | diagnosis | anthropic/claude-haiku-5.5 | failure: definite cause where the evidence does not decide |
| [U2](diagnosis-U2__google__gemini-3.8-flash__t3.md) | diagnosis | google/gemini-3.8-flash | failure: reply ran to the token limit |
| [U2](diagnosis-U2__anthropic__claude-sonnet-5.5__t1.md) | diagnosis | anthropic/claude-sonnet-5.5 | pass on the hardest ticket for small models |
| [U5](diagnosis-U5__anthropic__claude-haiku-5.5__t1.md) | diagnosis | anthropic/claude-haiku-5.5 | near miss: location as a bare string |
| [X1](translation-X1__openai__gpt-6-astra__t1.md) | translation | openai/gpt-6-astra | X1 had no failures; one pass |
| [X2](translation-X2__anthropic__claude-haiku-5.5__t2.md) | translation | anthropic/claude-haiku-5.5 | near miss: party name cut at 34 characters instead of the 35 allowed |
| [X2](translation-X2__google__gemini-3.8-flash__t1.md) | translation | google/gemini-3.8-flash | failure: implied decimals misread, amounts and price a factor of 10 off |
| [X2](translation-X2__anthropic__claude-fable-5.1__t1.md) | translation | anthropic/claude-fable-5.1 | no output: provider content filter |
| [Z1](sftp-Z1__anthropic__claude-sonnet-5.5__t1.md) | sftp | anthropic/claude-sonnet-5.5 | Z1 had no failures; one pass |
| [Z2](sftp-Z2__openai__gpt-6-astra__t1.md) | sftp | openai/gpt-6-astra | Z2 had no failures; one pass |
| [U2](agentic-U2__google__gemini-4-argon__t1.md) | agentic | google/gemini-4-argon | agentic pass: workspace search on a not-yet-determinable ticket |
