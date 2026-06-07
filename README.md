# HireSense.AI 🎯

> AI-powered resume intelligence — beat every ATS, land every interview.

HireSense.AI analyzes your resume against any job description in seconds, giving you a detailed breakdown of keyword matches, skill gaps, bullet point rewrites, and a downloadable PDF report.

---

## Features

- **Dual Scoring** — AI match score (LLM-based) + keyword match score (heuristic) for a complete picture
- **Skill Gap Analysis** — see exactly which skills from the JD are present or missing in your resume
- **Bullet Point Rewrites** — AI rewrites weak, vague bullets into quantified, high-impact achievements
- **Resume Structure Check** — flags missing sections (Summary, Experience, Education, Skills, Projects)
- **Language & Grammar Review** — catches weak action verbs, tense inconsistencies, and phrasing issues
- **PDF Report Download** — branded, professionally styled report you can save and share
- **Caching** — same inputs never re-call the API, saving tokens and time
- **Dark Glassmorphism UI** — sleek, modern interface built with Streamlit

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI / LLM | Groq API (`llama-3.3-70b-versatile`) |
| PDF Generation | ReportLab |
| PDF Parsing | pypdf |
| Language | Python 3.10+ |

---

## Project Structure

```
HireSense-AI/
├── app.py                  # Streamlit UI — layout, CSS, rendering
├── utils.py                # Backend logic — extraction, analysis, caching
├── prompts.py              # All LLM prompts isolated here
├── report_generator.py     # PDF report generation with ReportLab
├── requirements.txt
└── .streamlit/
    └── secrets.toml        # API keys (never commit this)
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/HireSense-AI.git
cd HireSense-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_key_here"
```

Get a free key at [console.groq.com/keys](https://console.groq.com/keys).

### 5. Run the app

```bash
streamlit run app.py
```

---

## Deploying to Streamlit Cloud

1. Push your code to GitHub (make sure `.streamlit/secrets.toml` is in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select your repo
3. Under **Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
4. Deploy 🚀

---

## Environment Variables

| Variable | Description | Where to set |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference | `.streamlit/secrets.toml` or Streamlit Cloud Secrets |

---

## How It Works

1. **PDF Extraction** — resume text is extracted using `pypdf` and cleaned
2. **Keyword Match** — heuristic comparison of JD and resume word sets (stop words filtered)
3. **LLM Analysis** — resume + JD sent to Groq with a structured prompt; response locked to JSON via `response_format`
4. **Scoring** — weighted across keyword match (40%), experience relevance (25%), education (15%), achievement quality (20%)
5. **PDF Report** — ReportLab builds a dark-themed branded report with score rings, skill pills, and bullet rewrites

---

## Notes

- Free Groq tier has a **100k token/day** limit — upgrade at [console.groq.com/settings/billing](https://console.groq.com/settings/billing) for higher limits
- Scanned/image-based PDFs are not supported — text must be extractable
- Results are AI-generated and should be used as guidance, not guarantees

---

## Author

**Sachin** — B.Tech AI/ML, AKGEC Ghaziabad  
Built as part of a Data Science portfolio project.

---

## License

MIT License — free to use, modify, and distribute.
