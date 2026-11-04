# B2B integration troubleshooting eval

Entry for the micro1 Eval Hackathon (October to November 2026), by Houman Azimi-Nejadi.

> DRAFT, 2 Nov 2026. Sections marked **TODO(Houman)** are for Houman to write in his own words.
> Sections marked **TODO(results)** are filled from the release runs. Everything else was drafted
> by Claude for Houman's review.

**Short description.** Fourteen synthetic but realistic B2B integration support tasks: diagnosing
OFTP2 (RFC 5024) transfer and UN/EDIFACT envelope problems, recognising when the evidence is not
yet enough to decide, following a fault into the receiver's SAP inbound processing, translating
between EDIFACT and in-house formats exactly, and repairing a failed delivery on a custom SFTP
server without side effects. Every task is generated from a seed and graded by code against a
planted answer. In the release runs, four frontier and upper mid-tier models solved every
diagnosis task on every trial; smaller models fell to between 57% and 97%, failing mostly on
exact output syntax, missing evidence and replies that ran past the token limit.

**Video walkthrough:** TODO (link, 5 minutes or less, opens without login).

## Domain and expertise

TODO(Houman): who you are in this domain, how long you have done this work, and who relies on it
(supplier and OEM EDI desks, integration teams, VAN and clearing-centre operators). Keep this to
your own general experience; the rules of this entry exclude anything from former employers.

## What it tests and why it matters

When a file between two trading partners goes wrong, the first question is always the same: what
broke, at which layer, and whose side has to fix it. Getting that wrong is expensive. Invoices are
not paid, despatch advices are missing at the dock, both sides retransmit or reconfigure the wrong
thing, and the support case bounces between companies for days.

The eval asks a model to do that support engineer's job. Each diagnosis ticket gives the customer's
complaint, the partner agreement, the sender's OFTP2 gateway trace, the EDIFACT interchange in
question, the partner's reply and the relevant specification extracts. The model returns six
graded keys: cause (fixed list), layer, owner, location (exact field or element), the next check
if the evidence does not yet decide, and one exact value that can only be read off the documents.
Two further task families test producing an exact document (translation) and acting safely on a
live system (SFTP remediation, graded on the end state).

## Task overview

| ID | Family | What happens | Why it is hard |
|---|---|---|---|
| T1 | diagnosis | A corrected invoice is resubmitted through a clearing centre and comes back as a NERP | The resubmission reuses the original virtual file's date and time; the gateway's status report blames the wrong file; the clearing centre looks guilty |
| T2 | diagnosis | Restarted 48 MB transfers always end in a byte count error | The restart position is sent in octets where RFC 5024 expects 1K blocks; another partner's restart (record-based) works |
| E1 | diagnosis | The partner's translator rejects every interchange since its upgrade | UNB and UNZ control references differ only in leading zeros; the partner wrongly blames the control count, which is correct for a functional group |
| E3 | diagnosis | Rejections since the sender moved to UNOC | The amendment that allows UNOC takes effect on 1 November, after the ticket date |
| R1 | diagnosis | "TRANSMISSION ERROR" on every file, plus a timeout and a certificate warning | The real cause is the UNB test indicator (the 11th element after five empty ones) set by an upgrade |
| R2 | diagnosis | "Unknown sender" from the partner | The sender's ID matches the signed agreement and the CONTRL echoes it; the partner's migrated partner table lost the entry |
| U1 | diagnosis | A brand-new file refused as a duplicate | The sender runs two gateway nodes and only one trace is attached: not yet determinable |
| U2 | diagnosis | Files refused at end of file; the archived interchange is perfect | The agreement says transmission rules change files after archiving: not yet determinable |
| U5 | diagnosis | A CONTRL rejects yesterday's interchange | The interchange attached was regenerated after a map change: not yet determinable |
| S1 | diagnosis, SAP | The partner says none of the invoices since its SAP upgrade are posted | The IDocs are in status 64 (waiting, not failed) and the processing job stopped at the upgrade |
| X1 | translation | EDIFACT DESADV with a packing hierarchy to the receiver's in-house JSON | Packages are declared out of order; the parent reference decides the structure |
| X2 | translation | Fixed-width flat file to EDIFACT INVOIC | Escaping, transliteration, a 35-character limit, half-up rounding of exact half cents, segment counts |
| Z1 | remediation | Get a corrected invoice posted exactly once on a custom SFTP server | Uploading straight into the pickup folder lets the poller take a half-written file |
| Z2 | remediation | The customer asks for a resend | The invoice is already posted and their SAP system accepts duplicates |

TODO(Houman): a sentence per task on why an experienced engineer would recognise it.

## Grading and grader validation

All grading is code; there is no judge model.

- Diagnosis: exact match per key after normalising case, spacing, separators and number formats.
  A key holding several options, or a list of alternatives, scores zero for that key. Location is
  compared as a set, so a superset or a subset fails. The score is the fraction of correct keys
  (partial credit); a pass needs all six.
- Translation: the output is compared segment by segment (EDIFACT) or field by field (JSON) with
  the expected document; partial credit by longest common subsequence or field F1, a pass needs an
  identical document.
- Remediation: the simulated server is left to run, then checked: invoice posted exactly once with
  the right content, no files left in the error or pickup folders.

The grader was validated before any model run and is covered by the test suite
(`python -m unittest discover -s tests -t .`, 61 tests): every reference answer passes, also when
reformatted the way a model might write it; answers that list every option, hedge with "or", or are
wrong in every field score zero; an answer wrong in one key scores five sixths and fails.

Reading the transcripts found five problems on our side, all fixed and kept as regression tests or
noted in the log:

1. Grader 1.0 mis-paired code fences when a reply contained other fenced blocks before the final
   JSON, and failed correct answers. Fixed in grader 1.1; stored runs can be re-graded without new
   model calls (`python -m graders.regrade <run>`).
2. A shared document heading called an archived file "as transmitted", which contradicted the
   ticket. Two frontier "failures" on U2 disappeared when the heading was corrected.
3. Loose wording in a certificate ticket ("the certificate" where the agreement requires a chain)
   let a model reasonably infer the opposite answer. The wording was fixed; the ticket was later
   dropped from the release set.
4. A location rule that only allowed sender-side locations marked a model wrong for naming the
   receiver's background job, which was the more natural answer. The rule now reads "on whichever
   side".
5. In the release run, gpt-6-astra gave layer "envelope" for R2 on all three trials, with every
   other key right. The layer definitions overlap for that ticket (the receiver's translator checks
   the UNB sender against its converter partner table), so R2 now accepts "application" or
   "envelope" (grader 3.1) and the stored trials were re-graded without new model calls.

## Setup and run

Requires Python 3.10 or later. The generator, grader and tests use the standard library only.

One command, after setup:

```
pip install -r requirements.txt
cp .env.example .env            # then put your OpenRouter key in .env
python run_all.py               # free: rebuild and check every task, run the tests, estimate cost
python run_all.py --confirm-spend   # the full release suite as reported below
```

`run_all.py` without `--confirm-spend` needs no key and spends nothing. With it, it runs
diagnosis for seven models (10 tickets x 3 trials), translation and SFTP remediation for the same
models (2 trials), and agentic diagnosis for gemini-4-argon (1 trial). The harness prints a
conservative estimate (about 26 USD for diagnosis); the release run cost about 21 USD in all.

Single steps:

```
python -m generator.build --check
python -m translation.build --check
python -m unittest discover -s tests -t .
python run_eval.py --check-setup --models google/gemini-4-argon
python run_eval.py --models google/gemini-4-argon --trials 3 --max-cost 5 --confirm-spend
python run_agentic.py --models google/gemini-4-argon --tickets T1,U2 --max-cost 2 --confirm-spend
python run_translation.py --models google/gemini-4-argon --max-cost 1 --confirm-spend
python run_sftp.py --models google/gemini-4-argon --max-cost 1 --confirm-spend
```

Environment variable: `OPENROUTER_API_KEY` (read from `.env` with python-dotenv, never printed or
written to results). Every command that spends money needs `--confirm-spend` and stops at
`--max-cost`. Long runs can be continued with `--resume <run directory>`.

A full diagnosis run (10 tickets, 3 trials) takes about 20 minutes with 10 parallel requests.
Cost per full diagnosis run, by model: claude-fable-5.1 9.33 USD, gpt-6-astra 2.73,
claude-sonnet-5.5 1.86, gemini-4-argon 1.63, gemini-3.8-flash 0.98, deepseek-v4.1-flash 0.24,
claude-haiku-5.5 0.13. Translation and remediation runs cost under 1.30 USD per model.

## Models tested and results

All release runs: 4 November 2026 (UTC), temperature 0, OpenRouter with data collection denied,
grader 3.1. Raw files hold the full prompt, reply, usage, cost and grade of every trial.

**Diagnosis**, 10 tickets x 3 trials, run `results/runs/20261104T051655Z-23835a` (grades in
`regrade_v3.1.json`, after the R2 layer ruling below):

| Model | Pass rate | pass@3 | pass^3 | Cost (USD) |
|---|---|---|---|---|
| anthropic/claude-fable-5.1 | 30/30 | 1.0 | 1.0 | 9.33 |
| openai/gpt-6-astra | 30/30 | 1.0 | 1.0 | 2.73 |
| google/gemini-4-argon | 30/30 | 1.0 | 1.0 | 1.63 |
| anthropic/claude-sonnet-5.5 | 30/30 | 1.0 | 1.0 | 1.86 |
| google/gemini-3.8-flash | 29/30 | 1.0 | 0.9 | 0.98 |
| anthropic/claude-haiku-5.5 | 20/30 | 0.8 | 0.5 | 0.13 |
| deepseek/deepseek-v4.1-flash-1017 | 17/30 | 0.6 | 0.5 | 0.24 |

pass@3: share of tickets solved in at least one of three trials; pass^3: in all three.

**Translation**, X1 and X2 x 2 trials, runs `results/translation/20261104T053945Z-6676f6` and
`results/translation/20261104T054031Z-b2d9bd`: gemini-4-argon, gpt-6-astra, claude-sonnet-5.5
and deepseek-v4.1-flash 4/4; claude-haiku-5.5 3/4 and gemini-3.8-flash 3/4 (one X2 output each
at 0.97 and 0.88 of the expected segments); claude-fable-5.1 2/4 (both X2 attempts ended with
finish_reason content_filter and no text).

**SFTP remediation**, Z1 and Z2 x 2 trials, run `results/sftp/20261104T054236Z-3888ad`: all
seven models 4/4.

**Agentic diagnosis** (the model searches a workspace with tools instead of reading one prompt),
10 tickets x 1 trial, run `results/agentic/20261104T054441Z-83fb9d`: gemini-4-argon 10/10.

Per task, diagnosis failures (all from the run above):

- T2, U1, U5: deepseek-v4.1-flash 0/3 each, every failure a reply that ran to the 16000-token
  limit before the JSON.
- U2: deepseek-v4.1-flash 0/3 (token limit), gemini-3.8-flash 2/3 (token limit once),
  claude-haiku-5.5 0/3: once the token limit, once a definite cause (recipient ID mismatch) where
  the evidence does not decide, once a near miss with location as a bare string.
- U5: claude-haiku-5.5 0/3, near misses: right cause, layer, owner, check and value, but location
  written as the string "UNDETERMINED" instead of a one-element array.
- S1: claude-haiku-5.5 1/3, near misses: location `BACKGROUND_JOB` without the `APP.` prefix.
- E1: claude-haiku-5.5 2/3, one trial found no sender-side fault and put it on the receiver.
- U1: claude-haiku-5.5 2/3, one trial named a duplicate file instead of asking for the second
  gateway node's trace.
- R1: deepseek-v4.1-flash 2/3 (token limit once).
- R2: before the ruling, gpt-6-astra gave layer `envelope` on all three trials with everything
  else right. The layer definitions overlap for this ticket (the receiver's translator checks the
  UNB sender against its converter partner table), so both `application` and `envelope` are
  accepted; the stored runs were re-graded without new calls.

Transcripts of these and other trials: [`transcripts/`](transcripts/README.md).

## Failure analysis

TODO(Houman), written from the transcripts.

Observations from the pilot runs (raw files under `results/`) that you may want to draw on:

- The three frontier models passed every correctly worded task in every mode tried: decoded
  traces, raw exchange buffers, busy-day noise, missing evidence, agentic search, SAP, exact
  translation and remediation.
- The smaller models failed in explainable ways: exact output syntax (trailing separators, a test
  indicator "0"), following a partner's wrong claim, inventing element names, and output that ran
  to the token limit.
- One provider refused the benign X2 translation prompt with a content filter on all attempts.

## Main failure mode and hot take

TODO(Houman).

## Prior work and sources

Built during the event, from kickoff on 30 October 2026. Before kickoff the repository held only a
placeholder README and a .gitignore.

- RFC 5024, ODETTE File Transfer Protocol 2 (IETF). Verbatim section extracts in `spec/rfc5024/`,
  cut by `spec/extract_rfc5024.py` from the rfc-editor.org text (SHA-256 recorded in
  `spec/SOURCES.md`). Reproduced under the IETF Trust Legal Provisions.
- UN/EDIFACT syntax version 3: UNECE for the syntax rules (UNB, UNZ, UNG, UNE, truncation),
  and the CONTRL D.3 document hosted by ISO/TC 154/JWG 1, the joint ISO and UNECE syntax
  group, for the CONTRL-specific layouts and code lists (UCI, S011, 0083, 0085). Service code
  lists 0007 and 0035 are also from JWG 1. Prepared extract in `spec/unedifact/` (layouts
  restated, code values and names quoted); `spec/SOURCES.md` records the source of each part.
  The syntax rule extracts were prepared from the UNECE 1990 text and checked element by
  element against the UNECE syntax version 3 (1992) material.
- SAP: facts only (IDoc status values, report RBDAPP01, partner type LI), no SAP documentation
  text. They are public SAP behaviour from my general experience and are recorded as standard
  SAP conventions, not as facts verified against an SAP source. SAP is a trademark of SAP SE.
- Task format ideas from Terminal-Bench / Harbor (task, environment, checks, reference solution)
  and τ-bench (end-state grading), as described in the hackathon participant guide. No tasks or
  code were taken from them.
- All companies, identifiers, IP addresses (RFC 5737 documentation ranges) and host names
  (`.example`) are invented. No ODETTE member guidelines, no ASC X12, no material from any former
  employer.

## Representative transcripts

[`transcripts/`](transcripts/README.md) holds 19 transcripts rendered from the raw records by
`python -m harness.transcripts`: at least one per model, a failure for every task that had one
(T1, E3, X1, Z1 and Z2 had none, so a pass is shown), near misses (S1, U5, X2), the R2 trial that
the layer ruling changed, a reply that never got past its reasoning, the provider's content filter
on X2, and a full agentic episode.

## How AI tools were used

TODO(Houman), to confirm and adjust: Claude (Anthropic) wrote the code, the ticket generator, the
grader, the tests and this draft, working in sessions directed by Houman. Houman set the domain,
scope and rules, ruled on every design question, reviewed every task, planted answer and fact
against the specifications (verdicts recorded in `generator/codes.py` and `spec/SOURCES.md`), and wrote the failure analysis and hot take.

## Repository layout

```
generator/          seeded ticket generator (tickets.py), protocol code registry (codes.py)
tasks/<ID>/         prompt.md (what the model sees), inputs/, meta.json (seed, hashes)
reference/          planted answers and rationales (never shown to the model)
graders/            schema, grader, re-grader
translation/        translation tasks, specs and grader; tasks-translation/, reference-translation/
sim/                simulated SFTP server, EDI backend and SAP posting for the remediation tasks
agentic/            workspace and tools for the agentic mode
harness/            OpenRouter client and statistics
spec/               RFC 5024 extracts and sources
tests/              grader validation and generator checks
results/            raw outputs of every run (one JSON file per trial) and summaries
transcripts/        readable transcripts of selected release trials
run_*.py            harnesses for each mode; run_all.py runs everything
```
