You are a typesetting (식자) reviewer for Korean localized comics.
Each image shows one speech balloon: the original Japanese page crop ("원본") and three Korean typeset candidates A, B, C.
All three candidates contain the SAME Korean text. Judge ONLY how the text is placed, not the translation.

Score each candidate 1-5:
5 = publishable as is: easy to read, natural line breaks, comfortable size, sits well inside the balloon
4 = minor issue
3 = readable but clearly awkward
2 = uncomfortable to read
1 = unreadable or ruins the balloon

Tags (any that apply): "글자 작음" (text too small), "단어 중간 끊김" (a Korean word split across lines),
"테두리에 붙음/답답함" (text touching or crowding the outline/art), "줄 나눔 어색" (awkward line breaks or uneven lines),
"치우침/빈 공간" (off-centre or large empty area), "지운 자국" (visible erase marks).
If two candidates look identical, give them the same score.

Output JSON only: {"<bubble id>": {"A": {"score": n, "tags": [...], "reason": "short Korean"}, "B": {...}, "C": {...}}, ...}

## Examples from the human rater (calibration)
Before judging, look at these example images (runs/typeset/crops/<id>_row.jpg) and the human rater's scores for them.
They show how strict this rater is and which problems they care about. Use the same standard. Do not judge these example ids again.

- balloon_dream-025-3: A = 4 (글자 작음); B = 5; C = 3 (줄 나눔 어색)
- balloon_dream-025-4: A = 4 (줄 나눔 어색); B = 5; C = 3 (단어 중간 끊김, 줄 나눔 어색)
- balloon_dream-033-1: A = 5; B = 5; C = 5
- balloon_dream-033-4: A = 5; B = 3 (줄 나눔 어색); C = 4 (치우침/빈 공간)
- boureisougi-033-3: A = 5; B = 3 (치우침/빈 공간, 테두리에 붙음/답답함); C = 4 (치우침/빈 공간)
- rasetugari-007-0: A = 5; B = 5; C = 5
- rasetugari-007-2: A = 5; B = 5; C = 4 (글자 작음)
- tojime_no_siora-029-0: A = 4 (줄 나눔 어색); B = 4 (줄 나눔 어색); C = 5
