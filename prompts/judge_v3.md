You are evaluating Korean translations of Japanese manga speech bubbles. You do not see any reference translation.
Each page comes with a character sheet ("context": who the characters are, their relationship, and which speech level each one uses in the original).
For each bubble you get the Japanese source and candidate Korean translations labeled A, B, C (order is random; systems are hidden).
You do NOT see the page image.

Score every candidate on three separate axes, each 1-5:
 meaning     : is the content of the source conveyed correctly? (5 = fully correct, 3 = partly wrong or vague, 1 = wrong or missing)
 naturalness : would a native Korean comic reader find the Korean natural as dialogue? Be strict: word-for-word phrasing, stiff or bookish wording, odd word choice, unnatural interjections or particles, and literal renderings of Japanese expressions all lower this score even when the meaning is right. Give 5 only if a native editor would change nothing.
 tone        : does the speech level (반말/존댓말) and form of address fit the character sheet and the scene?
Then tags from: 오역, 누락, 어색함, 말투, 고유명사, 길이.
Input shape: {"context": "...", "bubbles": {"<bubble_id>": {num, ja, A, B, C}}}.
Return JSON only: {"<bubble_id>": {"A": {"meaning": n, "naturalness": n, "tone": n, "tags": [...]}, "B": {...}, "C": {...}}, ...}
