# v3 decomposed judge: plan fixed before results (2026-11-27 15:45 KST)
Hypothesis: the v2 judges miss Korean awkwardness (human 3 / judge 5). Splitting the score into meaning / naturalness / tone,
with a strict naturalness instruction, should raise agreement with the human rater.
- Same input as v2 (runs/judge_input.json, character sheet, no image). Judges: Sonnet, Opus (text-only; image showed no gain in v2).
- Primary overall score = min(meaning, naturalness, tone). Secondary = rounded mean.
- Success: Spearman and pairwise accuracy vs human higher than the same model's v2 text judge.
- Also report: share of 5s (leniency), recall of human "어색함"-tagged items (judge naturalness <= 4).
