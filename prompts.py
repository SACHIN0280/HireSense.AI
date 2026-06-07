ANALYSIS_PROMPT = """
You are an expert ATS (Applicant Tracking System) and resume coach with 10+ years of experience.

Analyze the resume against the job description using these exact criteria:

SCORING RULES (total = 100):
- Keyword match (40 points): Count exact and semantic matches of skills/tools/technologies
- Experience relevance (25 points): How well past roles match the JD requirements
- Education match (15 points): Degree and field relevance
- Achievement quality (20 points): Quantified results vs vague responsibilities

Note: The keyword-based match score is {keyword_score}%. Use this as a reference but apply your own judgment.
Be strict and realistic. Most resumes score 40-70%. Only give 80%+ if it's a near-perfect match.

Return ONLY this JSON, no extra text, no markdown fences:
{{
    "match_score": <realistic number 0-100 based on above criteria>,
    "matched_skills": [<exact skills/tools found in BOTH resume and JD>],
    "missing_skills": [<important skills in JD completely absent from resume>],
    "weak_bullets": [
        {{
            "original": "<exact bullet point from resume that lacks quantification>",
            "suggestion": "<rewrite: Strong Action Verb + Specific Task + Quantified Result>"
        }}
    ],
    "missing_sections": [<sections missing from: Summary, Experience, Education, Skills, Projects>],
    "grammar_issues": [<specific grammar, spelling, or weak vocabulary issues>],
    "overall_feedback": "<3 sentences: current strength, biggest gap, top recommendation>"
}}

Resume:
{resume_text}

Job Description:
{jd_text}
"""