import re
import io
import json
import pdfplumber
import streamlit as st
from groq import Groq
from prompts import ANALYSIS_PROMPT

# ── Stop words ────────────────────────────────────────────────────────────────
STOP_WORDS = {
    'and', 'the', 'is', 'in', 'at', 'of', 'to', 'a', 'for', 'with', 'on',
    'as', 'be', 'by', 'or', 'an', 'are', 'was', 'has', 'have', 'will',
    'you', 'we', 'our', 'your', 'they', 'this', 'that', 'it', 'not',
    'from', 'but', 'all', 'can', 'its', 'their', 'also', 'if', 'which',
    'who', 'been', 'more', 'about', 'than', 'into', 'such', 'when',
}

# ── Text helpers ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    # Fix lowercase-to-uppercase glued words (wordWord -> word Word)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    # Fix letter-digit boundaries (e.g. "Present2024" -> "Present 2024")
    text = re.sub(r'(?<=[a-zA-Z])(?=[0-9])', ' ', text)
    text = re.sub(r'(?<=[0-9])(?=[a-zA-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()


# Cache PDF extraction by file bytes so re-runs are free
@st.cache_data(show_spinner=False)
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract and clean text from PDF bytes using pdfplumber (preserves layout/spacing far better than pypdf)."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    raw_text = "\n".join(text_parts)
    cleaned = clean_text(raw_text)
    if not cleaned or len(cleaned) < 50:
        raise ValueError("Could not extract readable text from the PDF. Is it scanned/image-based?")
    return cleaned


# Cache analysis so the same (resume, JD) pair isn't re-called
@st.cache_data(show_spinner=False)
def keyword_match(resume_text: str, jd_text: str) -> tuple[int, list[str]]:
    jd_words = set(re.findall(r'\b\w+\b', jd_text.lower()))
    resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
    jd_keywords = jd_words - STOP_WORDS
    matched = jd_keywords.intersection(resume_words)
    score = round((len(matched) / len(jd_keywords)) * 100) if jd_keywords else 0
    return score, sorted(matched)


@st.cache_data(show_spinner=False)
def analyze_resume(resume_text: str, jd_text: str, keyword_score: int) -> dict | None:
    """Call Groq API and return parsed dict, or None on failure."""
    import os
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        api_key = None
    api_key = api_key or os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error(
            "⚠️ **GROQ_API_KEY not found.** "
            "Add it to `.streamlit/secrets.toml` (local) or Streamlit Cloud Secrets."
        )
        return None

    client = Groq(api_key=api_key)
    prompt = ANALYSIS_PROMPT.format(
        keyword_score=keyword_score,
        resume_text=resume_text[:6000],   # stay within context limits
        jd_text=jd_text[:3000],
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.0,
            seed=42,
        )
        raw = response.choices[0].message.content
        # Strip any accidental markdown fences
        raw = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"```$", "", raw.strip())
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        st.error("The AI returned an invalid response. Please try again.")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def build_html_report(result: dict, keyword_score: int) -> str:
    """Build a styled, professional HTML report for download."""
    from datetime import datetime
    date_str = datetime.now().strftime("%B %d, %Y")

    score = result.get("match_score", 0)
    score_color = "#22c55e" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    kw_color = "#22c55e" if keyword_score >= 70 else "#f59e0b" if keyword_score >= 50 else "#ef4444"

    def score_ring(value, color, label):
        pct = value / 100
        circumference = 2 * 3.14159 * 52
        dash = circumference * pct
        gap = circumference - dash
        return f"""
        <div class="ring-wrap">
            <svg width="120" height="120" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="52" fill="none" stroke="#1e293b" stroke-width="12"/>
                <circle cx="60" cy="60" r="52" fill="none" stroke="{color}" stroke-width="12"
                    stroke-dasharray="{dash:.1f} {gap:.1f}"
                    stroke-dashoffset="{circumference * 0.25:.1f}"
                    stroke-linecap="round"/>
                <text x="60" y="56" text-anchor="middle"
                    font-family="Syne,sans-serif" font-size="22" font-weight="800" fill="white">{value}%</text>
                <text x="60" y="74" text-anchor="middle"
                    font-family="DM Sans,sans-serif" font-size="9" fill="#94a3b8">{label}</text>
            </svg>
        </div>"""

    matched_badges = "".join(
        f'<span class="badge badge-green">✓ {s}</span>'
        for s in result.get("matched_skills", [])
    ) or '<span class="muted">None found</span>'

    missing_badges = "".join(
        f'<span class="badge badge-red">✗ {s}</span>'
        for s in result.get("missing_skills", [])
    ) or '<span class="muted">No critical gaps</span>'

    bullets_html = ""
    for item in result.get("weak_bullets", []):
        bullets_html += f"""
        <div class="bullet-card">
            <div class="bullet-label">Original</div>
            <p class="bullet-original">{item.get('original', '')}</p>
            <div class="bullet-label green">✦ Improved Version</div>
            <p class="bullet-improved">{item.get('suggestion', '')}</p>
        </div>"""
    if not bullets_html:
        bullets_html = '<p class="muted">No weak bullets found — great job!</p>'

    missing_sec = result.get("missing_sections", [])
    sections_html = "".join(
        f'<div class="issue-row red">⚠ Missing: {s}</div>' for s in missing_sec
    ) or '<div class="ok-row">✓ All key sections present</div>'

    grammar = result.get("grammar_issues", [])
    grammar_html = "".join(
        f'<div class="issue-row yellow">💡 {g}</div>' for g in grammar
    ) or '<div class="ok-row">✓ No language issues found</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HireSense.AI — Resume Analysis Report</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #080c14;
    color: #e2e8f0;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    padding: 0;
  }}

  /* ── Header ── */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
    border-bottom: 1px solid rgba(99,179,237,0.15);
    padding: 40px 60px 36px;
    position: relative;
    overflow: hidden;
  }}
  .header::before {{
    content: "";
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 80% 50%, rgba(99,179,237,0.08) 0%, transparent 60%);
  }}
  .header-top {{
    display: flex; justify-content: space-between; align-items: flex-start;
    position: relative;
  }}
  .logo {{
    font-family: 'Syne', sans-serif;
    font-size: 28px; font-weight: 800;
    background: linear-gradient(135deg, #63b3ed, #b794f4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .report-meta {{
    text-align: right; color: #64748b; font-size: 12px; line-height: 1.8;
  }}
  .report-title {{
    font-family: 'Syne', sans-serif;
    font-size: 13px; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #63b3ed; margin-top: 20px; position: relative;
  }}
  .header h1 {{
    font-family: 'Syne', sans-serif;
    font-size: 36px; font-weight: 800;
    color: #f8fafc; margin-top: 6px; position: relative;
  }}
  .accent-bar {{
    height: 2px; width: 60px;
    background: linear-gradient(90deg, #63b3ed, #b794f4);
    border-radius: 2px; margin-top: 14px;
  }}

  /* ── Page body ── */
  .page {{ padding: 40px 60px; }}

  /* ── Score row ── */
  .scores-row {{
    display: flex; gap: 24px; margin-bottom: 28px;
  }}
  .score-card {{
    background: rgba(15,25,50,0.7);
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 16px; padding: 28px 24px;
    flex: 1; text-align: center;
  }}
  .ring-wrap {{ margin: 0 auto 8px; width: fit-content; }}
  .score-card-label {{
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #64748b; margin-bottom: 12px;
  }}
  .assessment-card {{
    background: rgba(15,25,50,0.7);
    border: 1px solid rgba(99,179,237,0.12);
    border-radius: 16px; padding: 28px 28px;
    flex: 2;
  }}
  .assessment-card p {{
    color: #cbd5e0; line-height: 1.75; font-size: 14px;
  }}

  /* ── Section ── */
  .section {{ margin-bottom: 32px; }}
  .section-title {{
    font-family: 'Syne', sans-serif;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #63b3ed; margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
  }}
  .section-title::after {{
    content: "";
    flex: 1; height: 1px;
    background: rgba(99,179,237,0.12);
  }}
  .card {{
    background: rgba(15,25,50,0.6);
    border: 1px solid rgba(99,179,237,0.1);
    border-radius: 14px; padding: 22px 24px;
  }}

  /* ── Badges ── */
  .badge {{
    display: inline-block; padding: 4px 12px;
    border-radius: 20px; font-size: 12px;
    font-weight: 500; margin: 3px;
  }}
  .badge-green {{
    background: rgba(34,197,94,0.1); color: #4ade80;
    border: 1px solid rgba(34,197,94,0.25);
  }}
  .badge-red {{
    background: rgba(239,68,68,0.1); color: #f87171;
    border: 1px solid rgba(239,68,68,0.25);
  }}

  /* ── Two columns ── */
  .two-col {{ display: flex; gap: 20px; }}
  .two-col > div {{ flex: 1; }}

  /* ── Bullet cards ── */
  .bullet-card {{
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 16px 18px;
    margin-bottom: 12px;
  }}
  .bullet-label {{
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #64748b; margin-bottom: 6px;
  }}
  .bullet-label.green {{ color: #4ade80; }}
  .bullet-original {{ color: #94a3b8; margin-bottom: 12px; font-size: 13px; }}
  .bullet-improved {{ color: #4ade80; font-weight: 500; font-size: 13px; }}

  /* ── Issue rows ── */
  .issue-row {{
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin-bottom: 8px; font-size: 13px; color: #e2e8f0;
  }}
  .issue-row.red {{ background: rgba(239,68,68,0.07); border-left: 3px solid #ef4444; }}
  .issue-row.yellow {{ background: rgba(245,158,11,0.07); border-left: 3px solid #f59e0b; }}
  .ok-row {{
    color: #4ade80; font-weight: 500; font-size: 13px; padding: 4px 0;
  }}
  .muted {{ color: #475569; font-size: 13px; }}

  /* ── Footer ── */
  .footer {{
    border-top: 1px solid rgba(99,179,237,0.1);
    padding: 24px 60px;
    display: flex; justify-content: space-between; align-items: center;
    color: #334155; font-size: 11px;
  }}
  .footer-logo {{
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 13px;
    background: linear-gradient(135deg, #63b3ed, #b794f4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
  <div class="header-top">
    <div class="logo">HireSense.AI</div>
    <div class="report-meta">
      <div>Resume Analysis Report</div>
      <div>Generated: {date_str}</div>
    </div>
  </div>
  <div class="report-title">ATS Optimization Report</div>
  <h1>Resume Intelligence<br>Summary</h1>
  <div class="accent-bar"></div>
</div>

<!-- BODY -->
<div class="page">

  <!-- SCORES -->
  <div class="section">
    <div class="section-title">Score Overview</div>
    <div class="scores-row">
      <div class="score-card">
        <div class="score-card-label">AI Match Score</div>
        {score_ring(score, score_color, "AI Score")}
      </div>
      <div class="score-card">
        <div class="score-card-label">Keyword Match</div>
        {score_ring(keyword_score, kw_color, "Keywords")}
      </div>
      <div class="assessment-card">
        <div class="score-card-label" style="margin-bottom:12px;">Overall Assessment</div>
        <p>{result.get("overall_feedback", "No feedback available.")}</p>
      </div>
    </div>
  </div>

  <!-- SKILLS -->
  <div class="section">
    <div class="section-title">Skill Analysis</div>
    <div class="two-col">
      <div class="card">
        <div class="score-card-label" style="color:#4ade80;margin-bottom:10px;">✅ Matched Skills</div>
        <div>{matched_badges}</div>
      </div>
      <div class="card">
        <div class="score-card-label" style="color:#f87171;margin-bottom:10px;">❌ Missing Skills</div>
        <div>{missing_badges}</div>
      </div>
    </div>
  </div>

  <!-- BULLET REWRITES -->
  <div class="section">
    <div class="section-title">💡 AI Bullet Point Rewrites</div>
    {bullets_html}
  </div>

  <!-- STRUCTURE & GRAMMAR -->
  <div class="section">
    <div class="section-title">Resume Quality</div>
    <div class="two-col">
      <div class="card">
        <div class="score-card-label" style="margin-bottom:10px;">📋 Resume Structure</div>
        {sections_html}
      </div>
      <div class="card">
        <div class="score-card-label" style="margin-bottom:10px;">✏️ Language & Grammar</div>
        {grammar_html}
      </div>
    </div>
  </div>

</div>

<!-- FOOTER -->
<div class="footer">
  <div class="footer-logo">HireSense.AI</div>
  <div>This report was generated by AI. Use it as a guide, not a guarantee.</div>
  <div>{date_str}</div>
</div>

</body>
</html>"""


def build_pdf_report(result: dict, keyword_score: int) -> bytes:
    """Generate a styled PDF report using reportlab."""
    from report_generator import generate_pdf_report
    return generate_pdf_report(result, keyword_score)
