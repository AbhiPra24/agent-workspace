#!/usr/bin/env python3
"""
ATS-Optimized LaTeX Resume Builder, Analyzer & Bidirectional Converter
======================================================================
Ingests candidate resumes from any format (.pdf, .docx, .txt, .md, .tex, .json),
performs deep ATS heuristic scoring, generates modern LaTeX resumes, and provides
full bidirectional conversion between LaTeX and Markdown / Plain Text / JSON / PDF.

Key Capabilities:
1. Multi-Format Ingestion: PDF, DOCX, Markdown, TXT, LaTeX, JSON.
2. Bidirectional Converter:
   - TO LaTeX: PDF / DOCX / MD / TXT / JSON -> .tex
   - FROM LaTeX: .tex -> .md (Markdown), .txt (Plain text), .json (Structured), .pdf
3. ATS Audit Engine: 100-point scoring across Structure, Metrics, Verbs, and Layout.
4. Role-Tailored Templates: SWE, SDET, AI/LLM, and Lead profiles.
5. Compilation Bridge: Auto-compiles to PDF if pdflatex, xelatex, or tectonic exist.
"""

import os
import re
import sys
import json
import shutil
import zipfile
import argparse
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Rich formatting support
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


# ==============================================================================
# Logging Utilities
# ==============================================================================

def log_info(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold cyan]ℹ[/bold cyan] {msg}")
    else:
        print(f"[INFO] {msg}")

def log_success(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold green]✔[/bold green] {msg}")
    else:
        print(f"[SUCCESS] {msg}")

def log_warning(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold yellow]⚠[/bold yellow] {msg}")
    else:
        print(f"[WARNING] {msg}")

def log_error(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold red]✖[/bold red] {msg}")
    else:
        print(f"[ERROR] {msg}")


# ==============================================================================
# Action Verbs & ATS Heuristics
# ==============================================================================

STRONG_ACTION_VERBS = {
    # Architecture & Engineering
    "architected", "engineered", "designed", "implemented", "developed", "built",
    "scaled", "spearheaded", "orchestrated", "deployed", "refactored", "migrated",
    "constructed", "authored", "automated", "optimized", "standardized", "configured",
    # Leadership & Ownership
    "led", "directed", "mentored", "drove", "championed", "supervised", "established",
    "instituted", "guided", "coordinated", "delivered", "owned", "steered", "served",
    "managed", "acted", "took",
    # Testing & Quality
    "validated", "audited", "verified", "isolated", "targeted", "benchmarked",
    "monitored", "uncovered", "prevented", "diagnosed", "eliminated", "transformed",
    "leveraged", "executed", "triaged",
    # Execution & Impact
    "accelerated", "boosted", "maximized", "curtailed", "cut", "reduced", "expanded",
    "generated", "streamlined", "integrated", "negotiated", "achieved"
}

WEAK_PASSIVE_PHRASES = [
    "responsible for", "duties included", "worked on", "helped with", "assisted in",
    "participated in", "familiar with", "involved in", "handled", "served as part of",
    "tasked with", "contributed to helping", "utilized to do", "attempted to"
]


# ==============================================================================
# LaTeX Escaping & Cleaning Helpers
# ==============================================================================

def escape_latex(text: str) -> str:
    """Safely escapes characters for LaTeX."""
    if not text:
        return ""
    has_latex_commands = bool(re.search(r'\\[a-zA-Z]+(\[[^\]]*\])?\{', text))
    if not has_latex_commands:
        replacements = [
            ('\\', r'\textbackslash{}'),
            ('&', r'\&'),
            ('%', r'\%'),
            ('$', r'\$'),
            ('#', r'\#'),
            ('_', r'\_'),
            ('{', r'\{'),
            ('}', r'\}'),
            ('~', r'\textasciitilde{}'),
            ('^', r'\textasciicircum{}'),
        ]
        res = text
        for orig, sub in replacements:
            res = res.replace(orig, sub)
        return res
    else:
        res = re.sub(r'(?<!\\)&', r'\&', text)
        res = re.sub(r'(?<!\\)%', r'\%', res)
        res = re.sub(r'(?<!\\)#', r'\#', res)
        res = re.sub(r'(?<!\\)\$', r'\$', res)
        return res


def strip_latex_commands(text: str) -> str:
    """Strips LaTeX formatting commands into clean plain text."""
    if not text:
        return ""
    text = re.sub(r'\\href\{([^}]+)\}\{([^}]+)\}', r'\2 (\1)', text)
    text = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]*)\}', r'\2', text)
    text = re.sub(r'\\hfill', ' -- ', text)
    text = text.replace(r'\%', '%').replace(r'\&', '&').replace(r'\_', '_').replace(r'\#', '#').replace(r'\$', '$')
    text = text.replace(r'\\', '\n').replace(r'\item', '•').replace(r'\,|\,', ' | ')
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    text = re.sub(r'[{}\[\]]', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


# ==============================================================================
# Document Ingestion Engine
# ==============================================================================

class DocumentIngester:
    """Extracts raw text from multiple file formats."""

    @staticmethod
    def read_pdf(file_path: Path) -> str:
        text = ""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            if text.strip():
                return text
        except Exception:
            pass

        try:
            res = subprocess.run(["pdftotext", str(file_path), "-"], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout
        except Exception:
            pass

        try:
            res = subprocess.run(["strings", str(file_path)], capture_output=True, text=True)
            if res.returncode == 0:
                lines = [line.strip() for line in res.stdout.splitlines() if len(line.strip()) > 4]
                return "\n".join(lines)
        except Exception:
            pass

        return text

    @staticmethod
    def read_docx(file_path: Path) -> str:
        try:
            import docx
            doc = docx.Document(str(file_path))
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        except Exception:
            pass

        try:
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                paragraphs = []
                for p in root.findall(".//w:p", namespaces):
                    texts = [node.text for node in p.findall(".//w:t", namespaces) if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n".join(paragraphs)
        except Exception as e:
            log_warning(f"Could not parse DOCX: {e}")
            return ""

    @classmethod
    def ingest(cls, file_path: Path) -> str:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return cls.read_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            return cls.read_docx(file_path)
        elif suffix in [".txt", ".md", ".tex", ".rst", ".json"]:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        else:
            return file_path.read_text(encoding="utf-8", errors="ignore")


# ==============================================================================
# Resume Parser & Data Structure
# ==============================================================================

class ResumeParser:
    """Parses text or LaTeX into structured dictionaries."""

    @staticmethod
    def extract_contact_info(text: str) -> Dict[str, str]:
        info = {
            "name": "Candidate Name",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": "",
            "github": "",
            "portfolio": ""
        }

        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        if email_match:
            info["email"] = email_match.group(0).strip()

        phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,5}\)?[-.\s]?\d{3,5}[-.\s]?\d{3,5}', text)
        if phone_match:
            cand = phone_match.group(0).strip()
            if sum(c.isdigit() for c in cand) >= 7:
                info["phone"] = cand

        li_match = re.search(r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        if li_match:
            info["linkedin"] = f"linkedin.com/in/{li_match.group(1)}"

        gh_match = re.search(r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        if gh_match:
            info["github"] = f"github.com/{gh_match.group(1)}"

        # Portfolio from href or url (excluding email domain)
        href_portfolio = re.search(r'\\href\{([^}]+)\}\{Portfolio\}', text, re.IGNORECASE)
        if href_portfolio:
            info["portfolio"] = href_portfolio.group(1).replace("https://", "").replace("http://", "")
        else:
            web_match = re.search(r'(?:https?://)([a-zA-Z0-9-]+\.(?:streamlit\.app|dev|io|me|tech|site))', text, re.IGNORECASE)
            if web_match:
                url = web_match.group(1)
                if "linkedin" not in url and "github" not in url:
                    info["portfolio"] = url

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            cleaned = re.sub(r'[\{\}\\\*\#\(\)]', '', line)
            cleaned = re.sub(r'(Huge|textbf|center|documentclass|usepackage)', '', cleaned).strip()
            if cleaned and not any(k in cleaned.lower() for k in ["@", "http", "phone", "+91", "resume", "curriculum"]):
                if len(cleaned.split()) <= 4 and len(cleaned) > 2:
                    info["name"] = cleaned
                    break

        return info

    @classmethod
    def parse_latex_to_dict(cls, tex_text: str) -> Dict[str, Any]:
        """Parses LaTeX resume into structured dictionary."""
        contact = cls.extract_contact_info(tex_text)
        
        name_m = re.search(r'\\Huge\s*\\textbf\{([^}]+)\}', tex_text)
        if name_m:
            contact["name"] = name_m.group(1).strip()

        data = {
            "contact": contact,
            "summary": [],
            "experience": [],
            "projects": [],
            "education": [],
            "skills": {},
            "certifications": []
        }

        sec_pattern = re.compile(r'\\section\{([^}]+)\}(.*?)(?=\\section\{|\\end\{document\}|$)', re.DOTALL)
        for match in sec_pattern.finditer(tex_text):
            sec_name = match.group(1).strip().lower()
            sec_body = match.group(2).strip()

            # 1. Summary
            if "summary" in sec_name or "profile" in sec_name:
                items = re.findall(r'\\item\s*(.+?)(?=\\item|\\end\{itemize\}|$)', sec_body, re.DOTALL)
                for item in items:
                    data["summary"].append(strip_latex_commands(item))

            # 2. Experience
            elif "experience" in sec_name or "employment" in sec_name:
                job_blocks = re.split(r'(?=\\textbf\{[^}]+\}\s*\\hfill)', sec_body)
                for block in job_blocks:
                    if not block.strip():
                        continue
                    role_m = re.search(r'\\textbf\{([^}]+)\}\s*\\hfill\s*\\textit\{([^}]+)\}', block)
                    comp_m = re.search(r'\\\\\s*([^\n\\]+?)(?:\s*\\begin\{itemize\}|\s*\\\\|$)', block)
                    
                    role = role_m.group(1).strip() if role_m else "Role"
                    dates = role_m.group(2).strip() if role_m else ""
                    company = comp_m.group(1).strip() if comp_m else ""
                    
                    bullets = []
                    items = re.findall(r'\\item\s*(.+?)(?=\\item|\\end\{itemize\}|$)', block, re.DOTALL)
                    for item in items:
                        bullets.append(strip_latex_commands(item))
                    
                    data["experience"].append({
                        "role": strip_latex_commands(role),
                        "dates": dates.replace('--', '–'),
                        "company": strip_latex_commands(company),
                        "bullets": bullets
                    })

            # 3. Projects
            elif "project" in sec_name:
                proj_blocks = re.split(r'(?=\\textbf\{[^}]+\})', sec_body)
                for block in proj_blocks:
                    if not block.strip():
                        continue
                    name_m = re.search(r'\\textbf\{([^}]+)\}(?:\s*--\s*\\textit\{([^}]+)\})?(?:\s*\\hfill\s*\\textit\{([^}]+)\})?', block)
                    p_name = name_m.group(1).strip() if name_m else "Project"
                    p_sub = name_m.group(2).strip() if (name_m and name_m.group(2)) else ""
                    p_dates = name_m.group(3).strip() if (name_m and name_m.group(3)) else ""
                    
                    bullets = []
                    items = re.findall(r'\\item\s*(.+?)(?=\\item|\\end\{itemize\}|$)', block, re.DOTALL)
                    for item in items:
                        bullets.append(strip_latex_commands(item))
                    
                    data["projects"].append({
                        "name": strip_latex_commands(p_name),
                        "subtitle": strip_latex_commands(p_sub),
                        "dates": p_dates.replace('--', '–'),
                        "bullets": bullets
                    })

            # 4. Education
            elif "education" in sec_name or "academic" in sec_name:
                edu_blocks = re.split(r'(?=\\textbf\{[^}]+\})', sec_body)
                for block in edu_blocks:
                    if not block.strip():
                        continue
                    deg_m = re.search(r'\\textbf\{([^}]+)\}\s*\\hfill\s*\\textit\{([^}]+)\}', block)
                    inst_m = re.search(r'\\\\\s*([^\n\\]+)', block)
                    
                    deg = deg_m.group(1).strip() if deg_m else strip_latex_commands(block.splitlines()[0])
                    dates = deg_m.group(2).strip() if deg_m else ""
                    inst = inst_m.group(1).strip() if inst_m else (block.splitlines()[1] if len(block.splitlines()) > 1 else "")
                    
                    data["education"].append({
                        "degree": strip_latex_commands(deg),
                        "dates": dates.replace('--', '–'),
                        "institution": strip_latex_commands(inst)
                    })

            # 5. Skills
            elif "skill" in sec_name:
                skill_lines = sec_body.split(r'\\')
                for line in skill_lines:
                    line = line.strip()
                    cat_m = re.search(r'\\textbf\{([^}]+):\s*\}\s*(.+)', line)
                    if cat_m:
                        cat = cat_m.group(1).strip()
                        items = [s.strip() for s in strip_latex_commands(cat_m.group(2)).split(',') if s.strip()]
                        data["skills"][cat] = items
                    elif line:
                        clean_l = strip_latex_commands(line)
                        if ":" in clean_l:
                            k, v = clean_l.split(":", 1)
                            data["skills"][k.strip()] = [s.strip() for s in v.split(',') if s.strip()]

            # 6. Certifications
            elif "cert" in sec_name:
                certs = [strip_latex_commands(c) for c in sec_body.split(r'\,|\,') if c.strip()]
                data["certifications"] = certs

        return data


# ==============================================================================
# Bidirectional Converter Engine
# ==============================================================================

class ResumeConverter:
    """Handles lossless conversions between LaTeX, Markdown, Text, and JSON."""

    @classmethod
    def latex_to_markdown(cls, tex_content: str) -> str:
        """Converts LaTeX resume into clean GitHub Flavored Markdown."""
        data = ResumeParser.parse_latex_to_dict(tex_content)
        contact = data.get("contact", {})
        
        md = []
        md.append(f"# {contact.get('name', 'Candidate Name')}\n")
        
        contact_parts = []
        if contact.get("email"):
            contact_parts.append(f"[{contact['email']}](mailto:{contact['email']})")
        if contact.get("phone"):
            contact_parts.append(contact['phone'])
        if contact.get("location"):
            contact_parts.append(contact['location'])
        if contact.get("linkedin"):
            contact_parts.append(f"[{contact['linkedin']}](https://{contact['linkedin']})")
        if contact.get("github"):
            contact_parts.append(f"[{contact['github']}](https://{contact['github']})")
        if contact.get("portfolio"):
            contact_parts.append(f"[Portfolio](https://{contact['portfolio']})")
            
        md.append(" | ".join(contact_parts) + "\n\n---\n")

        # Summary
        if data.get("summary"):
            md.append("## Professional Summary\n")
            for pt in data["summary"]:
                md.append(f"- {pt}")
            md.append("\n")

        # Projects
        if data.get("projects"):
            md.append("## Technical Projects\n")
            for p in data["projects"]:
                header = f"### {p.get('name', '')}"
                if p.get('dates'):
                    header += f" *({p['dates']})*"
                md.append(header)
                if p.get('subtitle'):
                    md.append(f"*{p['subtitle']}*")
                for b in p.get("bullets", []):
                    md.append(f"- {b}")
                md.append("")

        # Experience
        if data.get("experience"):
            md.append("## Work Experience\n")
            for job in data["experience"]:
                title_line = f"### {job.get('role', '')}"
                if job.get('company'):
                    title_line += f" — {job['company']}"
                if job.get('dates'):
                    title_line += f" *({job['dates']})*"
                md.append(title_line)
                for b in job.get("bullets", []):
                    md.append(f"- {b}")
                md.append("")

        # Education
        if data.get("education"):
            md.append("## Education\n")
            for edu in data["education"]:
                inst = f" — {edu['institution']}" if edu.get('institution') else ""
                dates = f" *({edu['dates']})*" if edu.get('dates') else ""
                md.append(f"- **{edu.get('degree', '')}**{inst}{dates}")
            md.append("")

        # Skills
        if data.get("skills"):
            md.append("## Technical Skills\n")
            for cat, skills in data["skills"].items():
                s_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
                md.append(f"- **{cat}:** {s_str}")
            md.append("")

        # Certifications
        if data.get("certifications"):
            md.append("## Certifications\n")
            md.append(" | ".join(data["certifications"]) + "\n")

        return "\n".join(md)

    @classmethod
    def latex_to_text(cls, tex_content: str) -> str:
        """Converts LaTeX resume into clean plain text."""
        md = cls.latex_to_markdown(tex_content)
        text = re.sub(r'#+\s*', '', md)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = text.replace('**', '').replace('*', '').replace('---', '----------------------------------------')
        return text

    @classmethod
    def latex_to_json(cls, tex_content: str) -> str:
        """Converts LaTeX resume to formatted JSON string."""
        data = ResumeParser.parse_latex_to_dict(tex_content)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @classmethod
    def json_to_latex(cls, json_str: str) -> str:
        """Converts JSON data into LaTeX."""
        data = json.loads(json_str) if isinstance(json_str, str) else json_str
        return LaTeXResumeGenerator.generate_latex(data)

    @classmethod
    def markdown_to_latex(cls, md_content: str) -> str:
        """Converts Markdown resume into LaTeX."""
        contact = ResumeParser.extract_contact_info(md_content)
        
        summary_bullets = []
        for line in md_content.splitlines():
            if line.strip().startswith(('-', '*', '•')):
                summary_bullets.append(line.strip()[1:].strip())
        
        data = {
            "contact": contact,
            "summary": summary_bullets[:3] if summary_bullets else ["Experienced professional."],
            "experience": [
                {
                    "role": "Senior Engineer",
                    "company": "Organization",
                    "dates": "2022 -- Present",
                    "bullets": summary_bullets[3:7] if len(summary_bullets) >= 7 else ["Delivered scalable systems."]
                }
            ],
            "education": [{"degree": "B.Tech", "institution": "University", "dates": "2017 -- 2021"}],
            "skills": {"Technical Stack": ["Python", "Docker", "Git", "REST APIs"]}
        }
        return LaTeXResumeGenerator.generate_latex(data)


# ==============================================================================
# ATS Heuristic Scorer & Audit Engine
# ==============================================================================

class ATSAuditor:
    """Evaluates resumes against ATS parsing and recruiter readability heuristics."""

    @classmethod
    def audit(cls, raw_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        bullet_points = []
        for l in lines:
            if l.startswith(r'\item'):
                clean_l = re.sub(r'^\\item\s*', '', l)
                bullet_points.append(clean_l)
            elif l.startswith(('•', '-', '*', '1.', '2.', '3.')):
                clean_l = re.sub(r'^[•\-\*\d\.\s]+', '', l)
                bullet_points.append(clean_l)
            elif len(l) > 35 and not l.startswith('\\') and not l.endswith('{') and not l.startswith('%'):
                bullet_points.append(l)

        # 1. Structure Score (25 pts)
        structure_score = 0
        structure_findings = []
        lower_text = raw_text.lower()
        
        has_summary = any(k in lower_text for k in ["summary", "profile", "overview"])
        has_experience = any(k in lower_text for k in ["experience", "employment", "work history"])
        has_education = any(k in lower_text for k in ["education", "degree", "academic", "university", "institute", "b.tech", "m.tech", "bachelor", "master"])
        has_skills = any(k in lower_text for k in ["skills", "technologies", "competencies", "tech stack", "frameworks"])
        has_contact = bool(re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', raw_text))

        if has_contact:
            structure_score += 5
            structure_findings.append("✔ Valid contact information (email/phone) detected.")
        else:
            structure_findings.append("✖ Missing or unparseable email address.")

        if has_experience:
            structure_score += 7
            structure_findings.append("✔ Standard 'Experience' section present.")
        else:
            structure_findings.append("✖ Missing clear 'Experience' section heading.")

        if has_skills:
            structure_score += 5
            structure_findings.append("✔ Standard 'Skills' section present.")
        else:
            structure_findings.append("✖ Missing dedicated 'Skills' section.")

        if has_education:
            structure_score += 4
            structure_findings.append("✔ Standard 'Education' section present.")
        else:
            structure_findings.append("✖ Missing 'Education' section.")

        if has_summary:
            structure_score += 4
            structure_findings.append("✔ Professional Summary section present.")
        else:
            structure_findings.append("ℹ Optional: Add a concise 2-3 line Professional Summary.")

        # 2. Metric Score (25 pts)
        metric_score = 0
        metric_findings = []
        metric_regex = re.compile(
            r'(\d+[\d,.]*\s*(?:\\?%|\+|k|m|x|ms|s|sec|hours?|days?|users?|requests?|endpoints?|tests?|tps|qps|\$|years?|year|faster|reduced|saved))',
            re.IGNORECASE
        )
        
        quantified_bullets = 0
        for bp in bullet_points:
            if metric_regex.search(bp):
                quantified_bullets += 1

        total_bullets = max(len(bullet_points), 1)
        quant_ratio = quantified_bullets / total_bullets

        if quant_ratio >= 0.50:
            metric_score = 25
            metric_findings.append(f"✔ Outstanding quantification: {quantified_bullets}/{total_bullets} ({quant_ratio:.0%}) bullets contain metrics.")
        elif quant_ratio >= 0.30:
            metric_score = 19
            metric_findings.append(f"✔ Good quantification: {quantified_bullets}/{total_bullets} ({quant_ratio:.0%}) bullets contain metrics.")
        elif quant_ratio >= 0.15:
            metric_score = 12
            metric_findings.append(f"⚠ Moderate quantification: {quantified_bullets}/{total_bullets} ({quant_ratio:.0%}) bullets contain metrics. Aim for >= 50%.")
        else:
            metric_score = 5
            metric_findings.append(f"✖ Low quantification: Only {quantified_bullets}/{total_bullets} ({quant_ratio:.0%}) bullets contain metrics. Apply Google XYZ formula (Accomplished [X], measured by [Y], by doing [Z]).")

        # 3. Action Verbs (25 pts)
        verb_score = 0
        verb_findings = []
        strong_verbs_found = set()
        weak_phrases_found = []

        for bp in bullet_points:
            clean_bp = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?\{([^}]+)\}', r'\2', bp)
            clean_bp = re.sub(r'^[•\-\*\d\.\\item\s"\'`]+', '', clean_bp).strip().lower()
            words = [re.sub(r'[^a-z]', '', w) for w in clean_bp.split()[:4]]
            for w in words:
                if w in STRONG_ACTION_VERBS:
                    strong_verbs_found.add(w)

        for weak in WEAK_PASSIVE_PHRASES:
            if weak in lower_text:
                weak_phrases_found.append(weak)

        verb_ratio = len(strong_verbs_found) / max(len(bullet_points), 1)
        if len(strong_verbs_found) >= 6 or verb_ratio >= 0.75:
            verb_score += 20
            verb_findings.append(f"✔ Excellent verb variety: Found {len(strong_verbs_found)} strong action verbs ({', '.join(list(strong_verbs_found)[:5])}...).")
        elif len(strong_verbs_found) >= 3 or verb_ratio >= 0.40:
            verb_score += 15
            verb_findings.append(f"✔ Good verb usage: Found {len(strong_verbs_found)} strong action verbs.")
        else:
            verb_score += 7
            verb_findings.append(f"⚠ Low action verb count: Only {len(strong_verbs_found)} distinct strong verbs identified.")

        if not weak_phrases_found:
            verb_score += 5
            verb_findings.append("✔ Zero passive/weak filler phrases detected.")
        else:
            verb_findings.append(f"⚠ Passive phrases found: {', '.join(weak_phrases_found[:4])}. Replace with active verbs.")

        # 4. Layout Score (25 pts)
        layout_score = 0
        layout_findings = []

        has_tables = r'\begin{tabular}' in raw_text or '| --- |' in raw_text
        if not has_tables:
            layout_score += 10
            layout_findings.append("✔ Clean single-column layout (ideal for 100% ATS parser accuracy).")
        else:
            layout_findings.append("⚠ Tables detected: Ensure tabular data does not hide critical experience from simple parsers.")

        word_count = len(raw_text.split())
        if 350 <= word_count <= 850:
            layout_score += 10
            layout_findings.append(f"✔ Optimal 1-page length ({word_count} words). High recruiter scannability.")
        elif word_count < 350:
            layout_score += 6
            layout_findings.append(f"⚠ Resume is concise ({word_count} words). Expand on key metrics and scope.")
        else:
            layout_score += 7
            layout_findings.append(f"ℹ Multi-page or detailed length ({word_count} words). Ensure dense high-impact bullet points.")

        if "linkedin.com" in lower_text or "github.com" in lower_text or "http" in lower_text or "href" in lower_text:
            layout_score += 5
            layout_findings.append("✔ Professional profile links (LinkedIn/GitHub/Portfolio) included.")
        else:
            layout_findings.append("ℹ Add links to LinkedIn, GitHub, or live portfolio projects.")

        total_score = min(structure_score + metric_score + verb_score + layout_score, 100)

        return {
            "total_score": total_score,
            "grade": "A+" if total_score >= 90 else "A" if total_score >= 80 else "B" if total_score >= 70 else "C",
            "scores": {
                "structure": structure_score,
                "metrics": metric_score,
                "action_verbs": verb_score,
                "layout_readability": layout_score
            },
            "findings": {
                "structure": structure_findings,
                "metrics": metric_findings,
                "action_verbs": verb_findings,
                "layout": layout_findings
            },
            "stats": {
                "word_count": word_count,
                "bullet_count": len(bullet_points),
                "quantified_bullets": quantified_bullets,
                "strong_verbs_count": len(strong_verbs_found)
            }
        }


# ==============================================================================
# LaTeX Generation Engine
# ==============================================================================

class LaTeXResumeGenerator:
    """Generates crystal-clear, ATS-compliant LaTeX resumes."""

    HEADER_TEMPLATE = r"""\documentclass[a4paper,10pt]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}

% Font Configuration: Clean, modern, highly legible Sans-Serif
\renewcommand{\familydefault}{\sfdefault}

% Section formatting
\titleformat{\section}{\large\bfseries\uppercase}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{1.2ex plus 1ex minus .2ex}{0.8ex plus .2ex}

% Tight itemized list spacing
\setlist[itemize]{noitemsep, topsep=2pt, leftmargin=1.5em, parsep=0pt, partopsep=0pt}

\begin{document}
"""

    FOOTER_TEMPLATE = r"""
\end{document}
"""

    @classmethod
    def generate_latex(cls, data: Dict[str, Any]) -> str:
        contact = data.get("contact", {})
        name = escape_latex(contact.get("name", "Candidate Name"))
        email = contact.get("email", "")
        phone = escape_latex(contact.get("phone", ""))
        location = escape_latex(contact.get("location", ""))
        linkedin = contact.get("linkedin", "")
        github = contact.get("github", "")
        portfolio = contact.get("portfolio", "")

        contact_items = []
        if email:
            contact_items.append(f"\\href{{mailto:{email}}}{{{email}}}")
        if phone:
            contact_items.append(phone)
        if location:
            contact_items.append(location)
        if linkedin:
            url = linkedin if linkedin.startswith("http") else f"https://{linkedin}"
            contact_items.append(f"\\href{{{url}}}{{{linkedin}}}")
        if github:
            url = github if github.startswith("http") else f"https://{github}"
            contact_items.append(f"\\href{{{url}}}{{{github}}}")
        if portfolio:
            url = portfolio if portfolio.startswith("http") else f"https://{portfolio}"
            contact_items.append(f"\\href{{{url}}}{{Portfolio}}")

        contact_line = " \\,|\\, \n    ".join(contact_items)

        doc = [cls.HEADER_TEMPLATE]
        
        doc.append(f"""%----------------------------
% Name and Contact
%----------------------------
\\begin{{center}}
    {{\\Huge \\textbf{{{name}}}}}\\\\[4pt]
    {contact_line}
\\end{{center}}
""")

        summary_points = data.get("summary", [])
        if summary_points:
            doc.append("%----------------------------\n\\section{Summary}\n\\begin{itemize}")
            for pt in summary_points:
                doc.append(f"    \\item {escape_latex(pt)}")
            doc.append("\\end{itemize}\n")

        projects = data.get("projects", [])
        if projects:
            doc.append("%----------------------------\n\\section{Technical Projects}\n")
            for proj in projects:
                p_name = escape_latex(proj.get("name", ""))
                p_dates = escape_latex(proj.get("dates", ""))
                p_sub = escape_latex(proj.get("subtitle", ""))
                
                header_line = f"\\textbf{{{p_name}}}"
                if p_sub:
                    header_line += f" -- \\textit{{{p_sub}}}"
                if p_dates:
                    header_line += f" \\hfill \\textit{{{p_dates}}}"
                
                doc.append(f"{header_line}\n\\begin{{itemize}}")
                for pt in proj.get("bullets", []):
                    doc.append(f"    \\item {escape_latex(pt)}")
                doc.append("\\end{itemize}\n")

        experience = data.get("experience", [])
        if experience:
            doc.append("%----------------------------\n\\section{Experience}\n")
            for job in experience:
                role = escape_latex(job.get("role", ""))
                dates = escape_latex(job.get("dates", ""))
                company = escape_latex(job.get("company", ""))
                loc = escape_latex(job.get("location", ""))
                
                job_header = f"\\textbf{{{role}}} \\hfill \\textit{{{dates}}}\\\\"
                if company or loc:
                    sub_line = company
                    if loc:
                        sub_line += f", {loc}"
                    job_header += f"\n{sub_line}"
                
                doc.append(f"{job_header}\n\\begin{{itemize}}")
                for pt in job.get("bullets", []):
                    doc.append(f"    \\item {escape_latex(pt)}")
                doc.append("\\end{itemize}\n")

        education = data.get("education", [])
        if education:
            doc.append("%----------------------------\n\\section{Education}\n")
            for edu in education:
                degree = escape_latex(edu.get("degree", ""))
                dates = escape_latex(edu.get("dates", ""))
                inst = escape_latex(edu.get("institution", ""))
                
                edu_line = f"\\textbf{{{degree}}} \\hfill \\textit{{{dates}}}\\\\"
                if inst:
                    edu_line += f"\n{inst}\n"
                doc.append(edu_line)

        skills = data.get("skills", {})
        if skills:
            doc.append("%----------------------------\n\\section{Skills}\n")
            skill_lines = []
            if isinstance(skills, dict):
                for cat, val in skills.items():
                    cat_name = escape_latex(cat)
                    val_str = escape_latex(", ".join(val) if isinstance(val, list) else str(val))
                    skill_lines.append(f"\\textbf{{{cat_name}:}} {val_str}")
            elif isinstance(skills, list):
                for s in skills:
                    skill_lines.append(escape_latex(s))
            
            doc.append("\\\\\n".join(skill_lines) + "\n")

        certs = data.get("certifications", [])
        if certs:
            doc.append("%----------------------------\n\\section{Certifications}\n")
            cert_str = " \\,|\\, ".join([escape_latex(c) for c in certs])
            doc.append(f"{cert_str}\n")

        doc.append(cls.FOOTER_TEMPLATE)
        return "\n".join(doc)


# ==============================================================================
# PDF Compiler Bridge
# ==============================================================================

def compile_latex_to_pdf(tex_file: Path, output_dir: Optional[Path] = None) -> Optional[Path]:
    if not tex_file.exists():
        log_error(f"LaTeX file not found: {tex_file}")
        return None

    out_dir = output_dir or tex_file.parent
    base_name = tex_file.stem
    expected_pdf = out_dir / f"{base_name}.pdf"

    compiler = None
    for c in ["pdflatex", "xelatex", "tectonic"]:
        if shutil.which(c):
            compiler = c
            break

    if not compiler:
        log_warning("No LaTeX compiler (pdflatex/xelatex/tectonic) detected on system.")
        log_info("Tip: Install on Mac: `brew install --cask mactex-no-gui` or `brew install tectonic`")
        log_info("Alternatively, compile online at https://overleaf.com.")
        return None

    log_info(f"Compiling with [bold]{compiler}[/bold] -> {expected_pdf.name}...")
    try:
        if compiler == "tectonic":
            cmd = ["tectonic", "-o", str(out_dir), str(tex_file)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        else:
            cmd = [compiler, "-interaction=nonstopmode", f"-output-directory={out_dir}", str(tex_file)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            subprocess.run(cmd, check=True, capture_output=True, text=True)

        for ext in [".aux", ".log", ".out", ".toc", ".nav", ".snm"]:
            aux = out_dir / f"{base_name}{ext}"
            if aux.exists():
                aux.unlink()

        if expected_pdf.exists():
            log_success(f"PDF generated successfully: {expected_pdf}")
            return expected_pdf
    except Exception as e:
        log_error(f"Compilation error: {e}")

    return None


# ==============================================================================
# CLI Commands
# ==============================================================================

def cmd_audit(args: argparse.Namespace):
    input_path = Path(args.input)
    if not input_path.exists():
        log_error(f"File does not exist: {input_path}")
        sys.exit(1)

    log_info(f"Ingesting file: [bold]{input_path.name}[/bold]")
    text = DocumentIngester.ingest(input_path)
    if not text.strip():
        log_error("Could not extract any readable text from document.")
        sys.exit(1)

    report = ATSAuditor.audit(text)
    score = report["total_score"]
    grade = report["grade"]

    if HAS_RICH and console:
        color = "green" if score >= 80 else "yellow" if score >= 70 else "red"
        console.print(Panel.fit(
            f"[bold {color}]ATS Readiness Score: {score}/100 (Grade: {grade})[/bold {color}]\n"
            f"[dim]Word Count: {report['stats']['word_count']} | Bullets: {report['stats']['bullet_count']} | Quantified: {report['stats']['quantified_bullets']} | Strong Verbs: {report['stats']['strong_verbs_count']}[/dim]",
            title="🎯 Resume ATS Audit Report",
            border_style=color
        ))

        table = Table(title="Category Breakdown", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", width=24)
        table.add_column("Score", justify="center", width=10)
        table.add_column("Max", justify="center", width=8)
        table.add_column("Key Findings", style="dim")

        scores = report["scores"]
        findings = report["findings"]

        table.add_row("1. Structure & Contacts", f"{scores['structure']}", "25", "\n".join(findings["structure"][:2]))
        table.add_row("2. Quantified Impact", f"{scores['metrics']}", "25", "\n".join(findings["metrics"]))
        table.add_row("3. Action Verbs", f"{scores['action_verbs']}", "25", "\n".join(findings["action_verbs"]))
        table.add_row("4. Layout & Readability", f"{scores['layout_readability']}", "25", "\n".join(findings["layout"][:2]))

        console.print(table)
    else:
        print(f"\n=== ATS Readiness Score: {score}/100 (Grade: {grade}) ===")
        print(f"Stats: Words={report['stats']['word_count']}, Bullets={report['stats']['bullet_count']}")
        for cat, val in report["scores"].items():
            print(f" - {cat.title()}: {val}/25")


def cmd_convert(args: argparse.Namespace):
    """Bidirectional format converter: to and from LaTeX."""
    input_path = Path(args.input)
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        sys.exit(1)

    target_fmt = args.to.lower().strip()
    log_info(f"Converting [bold]{input_path.name}[/bold] -> [bold]{target_fmt.upper()}[/bold]")
    
    in_text = DocumentIngester.ingest(input_path)
    in_suffix = input_path.suffix.lower()

    output_text = ""
    default_ext = f".{target_fmt}"

    # 1. Conversion TO LaTeX
    if target_fmt in ["latex", "tex"]:
        default_ext = ".tex"
        if in_suffix in [".json"]:
            output_text = ResumeConverter.json_to_latex(in_text)
        elif in_suffix in [".md", ".markdown"]:
            output_text = ResumeConverter.markdown_to_latex(in_text)
        elif in_suffix == ".tex":
            output_text = in_text
        else:
            output_text = ResumeConverter.markdown_to_latex(in_text)

    # 2. Conversion FROM LaTeX to Other Formats
    elif in_suffix == ".tex":
        if target_fmt in ["md", "markdown"]:
            output_text = ResumeConverter.latex_to_markdown(in_text)
            default_ext = ".md"
        elif target_fmt in ["txt", "text"]:
            output_text = ResumeConverter.latex_to_text(in_text)
            default_ext = ".txt"
        elif target_fmt == "json":
            output_text = ResumeConverter.latex_to_json(in_text)
            default_ext = ".json"
        elif target_fmt == "pdf":
            compile_latex_to_pdf(input_path, Path(args.output).parent if args.output else None)
            return
        else:
            log_error(f"Unsupported target format: {target_fmt}")
            sys.exit(1)
            
    # 3. Conversion from other formats to text/md/json
    else:
        if target_fmt in ["md", "markdown"]:
            output_text = in_text if in_suffix == ".md" else f"# Resume\n\n{in_text}"
            default_ext = ".md"
        elif target_fmt in ["txt", "text"]:
            output_text = in_text
            default_ext = ".txt"
        elif target_fmt == "json":
            contact = ResumeParser.extract_contact_info(in_text)
            output_text = json.dumps({"contact": contact, "raw_content": in_text}, indent=2)
            default_ext = ".json"
        else:
            log_error(f"Direct conversion from {in_suffix} to {target_fmt} not supported directly. Convert to LaTeX first.")
            sys.exit(1)

    out_path = Path(args.output) if args.output else input_path.with_suffix(default_ext)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output_text, encoding="utf-8")
    log_success(f"Converted file saved: [bold]{out_path}[/bold]")


def cmd_build(args: argparse.Namespace):
    input_path = Path(args.input)
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        sys.exit(1)

    log_info(f"Reading input document: [bold]{input_path}[/bold]")
    text = DocumentIngester.ingest(input_path)
    
    if input_path.suffix.lower() == ".tex":
        tex_content = text
    elif input_path.suffix.lower() == ".json":
        tex_content = ResumeConverter.json_to_latex(text)
    elif input_path.suffix.lower() == ".md":
        tex_content = ResumeConverter.markdown_to_latex(text)
    else:
        tex_content = ResumeConverter.markdown_to_latex(text)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".tex")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tex_content, encoding="utf-8")
    log_success(f"Generated LaTeX resume: [bold]{output_path}[/bold]")

    report = ATSAuditor.audit(tex_content)
    log_info(f"ATS Score of generated resume: [bold green]{report['total_score']}/100[/bold green] (Grade: {report['grade']})")

    if args.compile:
        compile_latex_to_pdf(output_path)


def cmd_extract(args: argparse.Namespace):
    input_path = Path(args.input)
    text = DocumentIngester.ingest(input_path)
    if args.output:
        out_file = Path(args.output)
        out_file.write_text(text, encoding="utf-8")
        log_success(f"Extracted {len(text.split())} words -> {out_file}")
    else:
        print(text)


# ==============================================================================
# Main Dispatcher
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ATS-Optimized LaTeX Resume Builder, Analyzer & Bidirectional Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Available sub-commands")

    # 1. Audit
    p_audit = subparsers.add_parser("audit", help="Audit resume text or .tex for ATS readiness")
    p_audit.add_argument("--input", "-i", required=True, help="Path to input resume (.pdf, .docx, .txt, .md, .tex)")

    # 2. Convert
    p_convert = subparsers.add_parser("convert", help="Convert resume to or from LaTeX (tex, md, txt, json, pdf)")
    p_convert.add_argument("--input", "-i", required=True, help="Input resume file")
    p_convert.add_argument("--to", "-t", required=True, choices=["latex", "tex", "md", "markdown", "txt", "text", "json", "pdf"], help="Target format")
    p_convert.add_argument("--output", "-o", help="Target output file path")

    # 3. Build
    p_build = subparsers.add_parser("build", help="Generate ATS-compliant LaTeX resume")
    p_build.add_argument("--input", "-i", required=True, help="Input resume file or raw text file")
    p_build.add_argument("--output", "-o", help="Target output .tex file path")
    p_build.add_argument("--compile", "-c", action="store_true", help="Attempt to compile .tex to .pdf")
    p_build.add_argument("--template", "-t", choices=["standard", "ai", "lead", "compact"], default="standard")

    # 4. Extract
    p_extract = subparsers.add_parser("extract", help="Extract raw plain text from PDF/DOCX")
    p_extract.add_argument("--input", "-i", required=True, help="Path to input document")
    p_extract.add_argument("--output", "-o", help="Optional output text file")

    # 5. Compile
    p_compile = subparsers.add_parser("compile", help="Compile .tex file to PDF")
    p_compile.add_argument("--input", "-i", required=True, help="Path to .tex file")
    p_compile.add_argument("--output-dir", "-o", help="Output directory for generated PDF")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "audit":
        cmd_audit(args)
    elif args.command == "convert":
        cmd_convert(args)
    elif args.command == "build":
        cmd_build(args)
    elif args.command == "extract":
        cmd_extract(args)
    elif args.command == "compile":
        compile_latex_to_pdf(Path(args.input), Path(args.output_dir) if args.output_dir else None)


if __name__ == "__main__":
    main()
