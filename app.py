import streamlit as st
from utils import extract_text_from_pdf, keyword_match, analyze_resume, build_pdf_report

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HireSense.AI | Smart ATS Optimizer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #080C14 !important;
    color: #F0F4FF !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Noise texture overlay */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
    opacity: 0.4;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D1321 0%, #080C14 100%) !important;
    border-right: 1px solid rgba(99, 179, 237, 0.08) !important;
}

header, [data-testid="stHeader"] { background: transparent !important; }

/* Typography */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* Glass card */
.glass-card {
    background: rgba(15, 25, 50, 0.6);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(99, 179, 237, 0.1);
    border-radius: 18px;
    padding: 1.5rem;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    margin-bottom: 1rem;
    transition: border-color 0.3s ease;
}
.glass-card:hover { border-color: rgba(99, 179, 237, 0.2); }

/* Gradient text */
.gradient-text {
    background: linear-gradient(135deg, #63B3ED 0%, #76E4F7 50%, #B794F4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-family: 'Syne', sans-serif;
    font-weight: 800;
}

/* Accent line */
.accent-line {
    height: 2px;
    background: linear-gradient(90deg, #63B3ED, #B794F4, transparent);
    border-radius: 2px;
    margin-bottom: 1rem;
}

/* File uploader */
[data-testid="stFileUploadDropzone"] {
    background: linear-gradient(135deg, rgba(99, 179, 237, 0.12) 0%, rgba(183, 148, 244, 0.08) 100%) !important;
    border: 1.5px dashed rgba(99, 179, 237, 0.4) !important;
    border-radius: 14px !important;
    padding: 3rem 2rem !important;
    transition: all 0.3s ease !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: rgba(99, 179, 237, 0.8) !important;
    background: linear-gradient(135deg, rgba(99, 179, 237, 0.18) 0%, rgba(183, 148, 244, 0.12) 100%) !important;
}
[data-testid="stFileUploader"] * { color: #CBD5E0 !important; fill: #63B3ED !important; }
[data-testid="stUploadedFile"] {
    background: rgba(99, 179, 237, 0.1) !important;
    border: 1px solid rgba(99, 179, 237, 0.3) !important;
    border-radius: 8px !important;
}

/* Text area */
.stTextArea [data-baseweb="textarea"],
.stTextArea textarea {
    background: rgba(99, 179, 237, 0.07) !important;
    color: #E2E8F0 !important;
    border: 1.5px solid rgba(99, 179, 237, 0.2) !important;
    border-radius: 14px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.3s ease !important;
}
.stTextArea textarea:focus {
    border-color: rgba(99, 179, 237, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(99, 179, 237, 0.08) !important;
}
.stTextArea textarea::placeholder { color: rgba(203, 213, 224, 0.4) !important; }

/* Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #3182CE 0%, #805AD5 100%);
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 2rem !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 20px rgba(50, 130, 206, 0.35) !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    margin-top: 1rem !important;
}
div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(50, 130, 206, 0.5) !important;
}
div.stButton > button:active { transform: translateY(0) !important; }

/* Download button — distinct style */
div.stDownloadButton > button {
    background: transparent !important;
    border: 1.5px solid rgba(99, 179, 237, 0.4) !important;
    color: #63B3ED !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.4rem 1.2rem !important;
    transition: all 0.25s ease !important;
}
div.stDownloadButton > button:hover {
    border-color: #63B3ED !important;
    background: rgba(99, 179, 237, 0.08) !important;
}

/* Score ring */
.score-ring-wrap {
    position: relative; width: 130px; height: 130px;
    border-radius: 50%; margin: 0 auto;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 30px rgba(0,0,0,0.4);
}
.score-ring-wrap::before {
    content: ""; position: absolute;
    width: 104px; height: 104px;
    border-radius: 50%; background: #080C14;
}
.score-number {
    position: relative;
    font-family: 'Syne', sans-serif;
    font-size: 2rem; font-weight: 800; color: #F0F4FF;
}

/* Skill badges */
.skill-badge {
    display: inline-block; padding: 0.25rem 0.75rem;
    border-radius: 20px; font-size: 0.82rem;
    margin: 0.2rem; font-weight: 500; letter-spacing: 0.01em;
}
.skill-match {
    background: rgba(72, 187, 120, 0.1);
    color: #68D391;
    border: 1px solid rgba(72, 187, 120, 0.25);
}
.skill-miss {
    background: rgba(252, 129, 74, 0.1);
    color: #FC8A4E;
    border: 1px solid rgba(252, 129, 74, 0.25);
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(15, 25, 50, 0.4) !important;
    border: 1px solid rgba(99, 179, 237, 0.1) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary p {
    color: #CBD5E0 !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* Alert box */
.info-tag {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(99, 179, 237, 0.08);
    border: 1px solid rgba(99, 179, 237, 0.15);
    color: #90CDF4; border-radius: 6px;
    padding: 0.25rem 0.7rem; font-size: 0.8rem;
    margin: 0.2rem;
}

/* Section label */
.section-label {
    font-family: 'Syne', sans-serif;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #63B3ED; margin-bottom: 0.4rem;
}

/* Issue rows */
.issue-row-red {
    background: rgba(252, 129, 74, 0.06);
    border-left: 3px solid #FC8A4E;
    padding: 0.7rem 1rem; margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    color: #E2E8F0; font-size: 0.9rem;
}
.issue-row-yellow {
    background: rgba(246, 224, 94, 0.06);
    border-left: 3px solid #F6E05E;
    padding: 0.7rem 1rem; margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    color: #E2E8F0; font-size: 0.9rem;
}
.ok-text { color: #68D391; font-weight: 500; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style='padding: 1rem 0 2rem 0;'>
            <span style='font-family:Syne,sans-serif;font-size:1.6rem;font-weight:800;
                background:linear-gradient(135deg,#63B3ED,#B794F4);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
                HireSense.AI
            </span>
        </div>
        <div class='accent-line'></div>
        <p style='color:#718096;font-size:0.78rem;font-weight:600;
            letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.2rem;'>
            Why use this?
        </p>
    """, unsafe_allow_html=True)

    features = [
        ("🤖", "#68D391", "Beat the Bots", "Optimize keywords to pass automated ATS filters."),
        ("✨", "#63B3ED", "AI-Powered Rewrites", "Transform weak bullets into high-impact achievements."),
        ("🎯", "#F6E05E", "Skill Gap Analysis", "See exactly what's missing before you apply."),
        ("⚡", "#B794F4", "Instant Report", "Download a full analysis report in one click."),
    ]
    for icon, color, title, desc in features:
        st.markdown(f"""
            <div style='margin-bottom:1.2rem;padding:0.8rem;border-radius:10px;
                background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.04);'>
                <p style='margin:0 0 0.2rem 0;'>
                    {icon} <strong style='color:{color};font-family:Syne,sans-serif;'>{title}</strong>
                </p>
                <p style='margin:0;color:#718096;font-size:0.85rem;line-height:1.5;'>{desc}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div style='margin-top:2rem;padding:0.8rem;border-radius:8px;
            background:rgba(99,179,237,0.05);border:1px solid rgba(99,179,237,0.1);
            font-size:0.8rem;color:#718096;line-height:1.5;'>
            💡 Results are cached — editing inputs clears the cache automatically.
        </div>
    """, unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style='text-align:center;padding:2.5rem 0 2rem 0;'>
        <p style='font-family:Syne,sans-serif;font-size:0.75rem;font-weight:700;
            letter-spacing:0.18em;text-transform:uppercase;color:#63B3ED;margin-bottom:0.8rem;'>
            AI-Powered Resume Intelligence
        </p>
        <h1 style='font-family:Syne,sans-serif;font-size:2.8rem;font-weight:800;
            line-height:1.15;margin:0 0 1rem 0;'>
            Beat every ATS.<br>
            <span style='background:linear-gradient(135deg,#63B3ED 0%,#76E4F7 40%,#B794F4 100%);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>
                Land every interview.
            </span>
        </h1>
        <p style='color:#718096;font-size:1rem;max-width:520px;margin:0 auto;line-height:1.6;'>
            Upload your resume, paste the job description — get a full AI analysis with skill gaps,
            rewrite suggestions, and a downloadable report.
        </p>
    </div>
""", unsafe_allow_html=True)

# ── Inputs ────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("<p class='section-label'>① Upload PDF Resume</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Resume PDF", type="pdf", label_visibility="collapsed"
    )
    st.markdown("""
        <div style='display:flex;gap:12px;margin-top:0.6rem;'>
            <span class='info-tag'>🔒 Processed locally</span>
            <span class='info-tag'>📄 PDF only</span>
            <span class='info-tag'>⚡ Cached results</span>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("<p class='section-label'>② Paste Job Description</p>", unsafe_allow_html=True)
    jd_text = st.text_area(
        "Job Description",
        height=200,
        placeholder="Paste the full job posting here...\n\nInclude responsibilities, requirements, and preferred qualifications for the best analysis.",
        label_visibility="collapsed",
    )

_, btn_col, _ = st.columns([1.2, 1, 1.2])
with btn_col:
    analyze_btn = st.button("🚀 Analyze My Resume", use_container_width=True)

# ── Analysis ──────────────────────────────────────────────────────────────────
if analyze_btn:
    if not uploaded_file:
        st.warning("⚠️ Please upload a PDF resume.")
    elif not jd_text or len(jd_text.strip()) < 50:
        st.warning("⚠️ Please paste a job description (at least 50 characters).")
    else:
        # Read bytes once so the stream isn't consumed across reruns
        file_bytes = uploaded_file.read()

        with st.spinner("Extracting resume text…"):
            try:
                resume_text = extract_text_from_pdf(file_bytes)
            except ValueError as e:
                st.error(str(e))
                st.stop()

        with st.spinner("Running AI analysis — this takes ~10 seconds…"):
            keyword_score, _ = keyword_match(resume_text, jd_text)
            result = analyze_resume(resume_text, jd_text, keyword_score)

        if result is None:
            st.stop()

        st.success("✅ Analysis complete!")

        # ── Score variables ──────────────────────────────────────────
        score = result.get("match_score", 0)

        def score_color(s):
            if s >= 70: return "#68D391"
            if s >= 50: return "#F6E05E"
            return "#FC8A4E"

        ai_col = score_color(score)
        kw_col = score_color(keyword_score)

        # ── 1. Metrics row ───────────────────────────────────────────
        st.markdown("<div style='margin-top:2rem;'></div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns([1, 1, 2])

        with m1:
            st.markdown(f"""
                <div class='glass-card' style='text-align:center;height:260px;
                    display:flex;flex-direction:column;justify-content:center;gap:1rem;'>
                    <p class='section-label' style='margin:0;'>AI Match Score</p>
                    <div class='score-ring-wrap'
                        style='background:conic-gradient({ai_col} {score}%, rgba(255,255,255,0.04) 0);'>
                        <span class='score-number'>{score}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
                <div class='glass-card' style='text-align:center;height:260px;
                    display:flex;flex-direction:column;justify-content:center;gap:1rem;'>
                    <p class='section-label' style='margin:0;'>Keyword Match</p>
                    <div class='score-ring-wrap'
                        style='background:conic-gradient({kw_col} {keyword_score}%, rgba(255,255,255,0.04) 0);'>
                        <span class='score-number'>{keyword_score}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
                <div class='glass-card' style='height:260px;overflow-y:auto;
                    display:flex;flex-direction:column;justify-content:center;'>
                    <p class='section-label'>Overall Assessment</p>
                    <p style='color:#CBD5E0;line-height:1.7;font-size:0.95rem;margin:0;'>
                        {result.get("overall_feedback", "No feedback available.")}
                    </p>
                </div>
            """, unsafe_allow_html=True)

        # ── 2. Download report ──────────────────────────────────────
        report_pdf = build_pdf_report(result, keyword_score)
        dl1, _, dl2 = st.columns([1, 2, 1])
        with dl1:
            st.download_button(
                label="📥 Download PDF Report",
                data=report_pdf,
                file_name="hiresense_analysis.pdf",
                mime="application/pdf",
            )

        # ── 3. Skills ───────────────────────────────────────────────
        st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:
            badges = "".join(
                f"<span class='skill-badge skill-match'>✓ {s}</span>"
                for s in result.get("matched_skills", [])
            )
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='section-label'>✅ Matched Skills</p>
                    <div>{badges or "<span style='color:#4A5568;'>No specific matches found.</span>"}</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            miss_badges = "".join(
                f"<span class='skill-badge skill-miss'>✗ {s}</span>"
                for s in result.get("missing_skills", [])
            )
            st.markdown(f"""
                <div class='glass-card'>
                    <p class='section-label'>❌ Missing Skills</p>
                    <div>{miss_badges or "<span style='color:#4A5568;'>No critical gaps found.</span>"}</div>
                </div>
            """, unsafe_allow_html=True)

        # ── 4. Bullet rewrites ──────────────────────────────────────
        weak = result.get("weak_bullets", [])
        if weak:
            st.markdown("""
                <h3 style='font-family:Syne,sans-serif;color:#E2E8F0;
                    font-size:1.1rem;margin:1.5rem 0 0.8rem 0;'>
                    💡 AI Bullet Point Rewrites
                </h3>
            """, unsafe_allow_html=True)
            for item in weak:
                label = (item.get("original", "")[:75] + "…") if item.get("original") else "Bullet point"
                with st.expander(f"📝 {label}"):
                    st.markdown(f"""
                        <div style='padding:1rem;border-radius:10px;
                            background:rgba(255,255,255,0.02);'>
                            <p class='section-label'>Original</p>
                            <p style='color:#A0AEC0;margin:0 0 1rem 0;
                                font-size:0.9rem;line-height:1.6;'>
                                {item.get("original", "")}
                            </p>
                            <p class='section-label' style='color:#68D391;'>Improved Version</p>
                            <p style='color:#68D391;margin:0;font-size:0.95rem;
                                font-weight:500;line-height:1.6;'>
                                {item.get("suggestion", "")}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

        # ── 5. Structure & Grammar ──────────────────────────────────
        st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("""
                <div class='glass-card'>
                    <p class='section-label'>📋 Resume Structure</p>
                    <p style='color:#4A5568;font-size:0.82rem;margin-bottom:0.8rem;'>
                        Recruiters spend only 6–7 seconds on first scan.
                    </p>
            """, unsafe_allow_html=True)
            missing_sec = result.get("missing_sections", [])
            if missing_sec:
                for sec in missing_sec:
                    st.markdown(f"<div class='issue-row-red'>⚠️ Missing: {sec}</div>",
                                unsafe_allow_html=True)
            else:
                st.markdown("<p class='ok-text'>✓ All key sections present</p>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c4:
            st.markdown("""
                <div class='glass-card'>
                    <p class='section-label'>✏️ Language & Grammar</p>
                    <p style='color:#4A5568;font-size:0.82rem;margin-bottom:0.8rem;'>
                        Strong action verbs dramatically improve recruiter impression.
                    </p>
            """, unsafe_allow_html=True)
            grammar = result.get("grammar_issues", [])
            if grammar:
                for issue in grammar:
                    st.markdown(f"<div class='issue-row-yellow'>💡 {issue}</div>",
                                unsafe_allow_html=True)
            else:
                st.markdown("<p class='ok-text'>✓ No language issues found</p>",
                            unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)