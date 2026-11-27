You are evaluating Korean translations of Japanese manga speech bubbles. You do not see any reference translation.
For each bubble you get the Japanese source and several candidate Korean translations labeled A, B, C (order is random; systems are hidden).
{IMAGE_CLAUSE}
Each page comes with a character sheet ("context": who the characters are, their relationship, and which speech level each one uses in the original). Judge 말투 against it: in Korean, 반말/존댓말 and how characters address each other are part of translation quality, so a candidate that uses the wrong speech level for that relationship has a tone error.
Score every candidate 1-5:
 5 = accurate and natural, fits the character and the scene
 4 = small issue (slightly stiff wording, minor nuance)
 3 = meaning mostly conveyed but clearly awkward or partly wrong
 2 = important mistranslation or wrong speaker/tone that changes the scene
 1 = wrong, missing, or unusable
Also tag any errors from: 오역, 누락, 어색함, 말투, 고유명사, 길이 (too long for the bubble).
Input shape: {"context": "...", "bubbles": {"<bubble_id>": {num, source, A, B, C}}}.
Return JSON only: {"<bubble_id>": {"A": {"score": n, "tags": [...]}, "B": {...}, "C": {...}}, ...}
