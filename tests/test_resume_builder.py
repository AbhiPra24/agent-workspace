#!/usr/bin/env python3
"""
Unit tests for Resume Builder, ATS Auditor & Bidirectional Converter
"""

import json
import unittest
import tempfile
from pathlib import Path
from scripts.resume_builder import (
    escape_latex,
    strip_latex_commands,
    DocumentIngester,
    ResumeParser,
    ResumeConverter,
    ATSAuditor,
    LaTeXResumeGenerator
)

class TestResumeBuilder(unittest.TestCase):

    def test_escape_latex(self):
        self.assertEqual(escape_latex("C++ & Python"), r"C++ \& Python")
        self.assertEqual(escape_latex("100% test coverage"), r"100\% test coverage")
        self.assertEqual(escape_latex("$50k cost reduction"), r"\$50k cost reduction")
        self.assertEqual(escape_latex("user_id"), r"user\_id")

    def test_strip_latex_commands(self):
        self.assertEqual(strip_latex_commands(r"\textbf{Important} text"), "Important text")
        self.assertEqual(strip_latex_commands(r"\href{https://example.com}{Link}"), "Link (https://example.com)")

    def test_resume_parser_contact(self):
        text = """Abhinav Prakash
abhinavprakash616@gmail.com | +91 94575 48199 | Noida, India | linkedin.com/in/abhipra24 | github.com/abhipra24

SUMMARY
Senior QA Automation Engineer with 5 years experience.
"""
        info = ResumeParser.extract_contact_info(text)
        self.assertEqual(info["email"], "abhinavprakash616@gmail.com")
        self.assertEqual(info["linkedin"], "linkedin.com/in/abhipra24")
        self.assertEqual(info["github"], "github.com/abhipra24")
        self.assertIn("94575", info["phone"])

    def test_ats_auditor_high_scoring(self):
        sample_latex = r"""\documentclass{article}
\begin{document}
\textbf{Abhinav Prakash}
abhinavprakash616@gmail.com | +91 94575 48199 | linkedin.com/in/abhipra24

\section{Summary}
\begin{itemize}
    \item Senior SDET with \textbf{5 years} of experience architecting test automation frameworks.
\end{itemize}

\section{Experience}
\textbf{Senior Software QA Engineer} \hfill \textit{Apr 2025 -- Present}\\
Company Name
\begin{itemize}
    \item Architected internal utilities in Python and FastAPI, reducing defect triage time by 30\%.
    \item Engineered modular BDD automation frameworks, achieving \textbf{40\% faster execution} across pipelines.
    \item Automated 100+ REST API test suites using Python and Playwright, reducing manual effort by 25\%.
\end{itemize}

\section{Education}
\textbf{B.Tech, Electronics \& Communications} \hfill \textit{2017 -- 2021}\\
Jaypee Institute

\section{Skills}
\textbf{Frameworks:} Python, Java, Pytest, Playwright\\
\textbf{DevOps:} Docker, Jenkins, CI/CD
\end{document}
"""
        report = ATSAuditor.audit(sample_latex)
        self.assertGreaterEqual(report["total_score"], 80)
        self.assertIn(report["grade"], ["A", "A+"])
        self.assertEqual(report["scores"]["structure"], 25)
        self.assertGreaterEqual(report["scores"]["metrics"], 18)
        self.assertGreaterEqual(report["scores"]["action_verbs"], 20)

    def test_bidirectional_conversions(self):
        sample_latex = r"""\documentclass[a4paper,10pt]{article}
\begin{document}
\begin{center}
    {\Huge \textbf{Abhinav Prakash}}\\[4pt]
    \href{mailto:abhinav@example.com}{abhinav@example.com} \,|\, +91 94575 48199 \,|\, \href{https://linkedin.com/in/abhipra24}{linkedin.com/in/abhipra24}
\end{center}

\section{Summary}
\begin{itemize}
    \item Senior SDET with 5 years experience.
\end{itemize}

\section{Experience}
\textbf{Senior QA Engineer} \hfill \textit{2024 -- Present}\\
Tech Corp
\begin{itemize}
    \item Architected automated frameworks with 40\% faster execution.
\end{itemize}

\section{Education}
\textbf{B.Tech} \hfill \textit{2021}\\
Institute Name

\section{Skills}
\textbf{Languages:} Python, Java
\end{document}
"""
        # 1. LaTeX -> Markdown
        md = ResumeConverter.latex_to_markdown(sample_latex)
        self.assertIn("# Abhinav Prakash", md)
        self.assertIn("## Work Experience", md)
        self.assertIn("Tech Corp", md)
        self.assertIn("40% faster execution", md)

        # 2. LaTeX -> Plain Text
        txt = ResumeConverter.latex_to_text(sample_latex)
        self.assertIn("Abhinav Prakash", txt)
        self.assertIn("Work Experience", txt)

        # 3. LaTeX -> JSON
        json_str = ResumeConverter.latex_to_json(sample_latex)
        data = json.loads(json_str)
        self.assertEqual(data["contact"]["name"], "Abhinav Prakash")
        self.assertEqual(data["contact"]["email"], "abhinav@example.com")
        self.assertEqual(len(data["experience"]), 1)
        self.assertEqual(data["experience"][0]["role"], "Senior QA Engineer")

        # 4. JSON -> LaTeX
        regenerated_tex = ResumeConverter.json_to_latex(data)
        self.assertIn(r"\documentclass[a4paper,10pt]{article}", regenerated_tex)
        self.assertIn("Abhinav Prakash", regenerated_tex)
        self.assertIn(r"\section{Experience}", regenerated_tex)

if __name__ == "__main__":
    unittest.main()
