# Reviewing changes to weft-loom

Moissanite Labs sorts every change into one of three lanes by the paths it touches. Each lane has its own checklist.
A design note is not reviewed like code, and a record is not reviewed like a design note. The plan and the reasons are
in [Moissanite-Labs/siliconcordat#13](https://github.com/Moissanite-Labs/siliconcordat/issues/13).

| Lane | Paths here | Label |
|---|---|---|
| **record** | `experiments/`, `audit/`, `incidents/`, `archive/` | `lane: record` |
| **idea** | `notes/` | `lane: idea` |
| **build** | `.github/`, `scripts/`, `siliconcordat-cut/`, `workers/`, `wrangler*.jsonc` | `lane: build` |

The `lanes` workflow adds the labels. Read the label first and use that lane's checklist. A pull request that touches
two lanes is reviewed against both, each for its own files.

## Record lane

A record is ready to merge when:

1. **The question is stated before the answer.** A preregistration, or a hypothesis and the planned measure written
   down before the results. If it was written afterwards, the record says so and the status is `exploratory`.
2. **It can be rerun.** There is a command, the seeds, and the environment it ran in. If it only runs on one machine
   or one host, the record says so.
3. **The limits are stated as clearly as the findings.** Sample size, what was not controlled, and what the result
   does not show.
4. **Claims are no bigger than the evidence.** Every number in the prose matches the committed output. A toy result
   is not described as a general law.
5. **Raw output is committed or linked with a hash.** See the raw-data rule in [CONTRIBUTING.md](CONTRIBUTING.md).
6. **It is in the index** ([experiments/README.md](experiments/README.md)) with a status that matches what the record
   shows. CI checks that the row exists.

Not reasons to block a record: writing style, file layout inside the folder, disagreement with another record (say
so in a comment, and the record may cite it), or a result that is negative or null. A negative result stated plainly
is a good record.

Who merges: an independent reviewer. The author does not merge their own record.

## Idea lane

A design note is ready to merge when:

1. **It reads as an idea.** It is listed in [notes/README.md](notes/README.md) with a status (`idea`, `proposal`,
   `adopted`, `superseded` or `withdrawn`), an owner and a date. CI checks the index row.
2. **Speculation is not stated as fact.** Anything not built or measured is phrased as a proposal or a question.
3. **Statements about existing code are correct.** If the note says a function exists or does not, or a test
   passes, that is checked like any factual claim.
4. **No secrets, personal data or unsafe instructions.**

Not reasons to block a note: missing evidence (that is what makes it an idea), disagreement with other notes, an
open question left open, or style. Raise these as comments. A note may contradict another note; the index can record
which one the team adopts.

Who merges: the author, after one approval or after 24 hours with no blocking review.

## Build lane

Code, CI and the siliconcordat-cut pipeline follow weft's build checklist
([weft REVIEWING.md](https://github.com/Moissanite-Labs/weft/blob/main/REVIEWING.md)): a test that fails without the
change, green CI on the exact head, and claims that match the code. The author does not merge.

## Review comments

Request changes only for a defect against the lane's checklist. Everything else is a comment. When a record moves
here from another repository, review the move (is every file present and unchanged?) separately from the content.
Content findings stay open on the record, and the index says so.
