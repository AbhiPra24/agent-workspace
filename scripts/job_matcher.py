#!/usr/bin/env python3
"""
Job Matcher CLI Script
======================
Extracts Senior Software QA Automation Engineer roles (Gurugram / Noida / Remote)
using Firecrawl, evaluates job descriptions against a candidate's resume via Local LLM,
and prints a ranked match score table.

Criteria:
- Heavily prioritize Python + Playwright
- Focus on Independent Project QA Leadership over Direct People Management
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    # Search for .env in current directory and parent directories
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Rich formatting (with graceful fallback)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


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


def parse_resume(file_path: str) -> str:
    """Reads and extracts text from a PDF or TXT resume file."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found at: {path}")

    suffix = path.suffix.lower()
    if suffix in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    elif suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text).strip()
        except ImportError:
            try:
                import pypdf2
                reader = pypdf2.PdfReader(str(path))
                text = [p.extract_text() for p in reader.pages if p.extract_text()]
                return "\n".join(text).strip()
            except ImportError:
                raise ImportError("Please install `pypdf` to parse PDF resumes: `pip install pypdf`")
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported formats: .pdf, .txt, .md")


def search_jobs_with_firecrawl(
    query: str,
    api_key: Optional[str] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches career sites and job boards using Firecrawl API.
    """
    api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
    
    # If no valid API key or placeholder is detected, fallback to sample mock jobs for instant testing
    if not api_key or api_key.startswith("fc-YOUR_") or api_key == "YOUR_FIRECRAWL_API_KEY":
        log_warning("FIRECRAWL_API_KEY not configured or set to placeholder in .env.")
        log_info("Fetching curated sample QA Automation roles for Gurugram/Noida/Remote...")
        return get_mock_job_listings()

    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=api_key)
        
        log_info(f"Executing Firecrawl search: '{query}' (limit={limit})...")
        search_result = app.search(
            query=query,
            params={
                "scrapeOptions": {
                    "formats": ["markdown"]
                },
                "limit": limit
            }
        )
        
        # Firecrawl returns data structure with 'data' key or list
        items = search_result.get("data", []) if isinstance(search_result, dict) else search_result
        
        formatted_jobs = []
        for item in items:
            title = item.get("title") or "Senior Software QA Automation Engineer"
            url = item.get("url") or item.get("link") or "https://careers.google.com"
            content = item.get("markdown") or item.get("description") or item.get("content") or ""
            metadata = item.get("metadata", {})
            company = metadata.get("og:site_name") or metadata.get("author") or "Tech Company"
            
            formatted_jobs.append({
                "title": title,
                "company": company,
                "url": url,
                "description": content[:3000] # Limit token usage
            })
            
        return formatted_jobs if formatted_jobs else get_mock_job_listings()

    except Exception as e:
        log_error(f"Firecrawl search encountered an error: {e}")
        log_info("Falling back to curated sample job listings...")
        return get_mock_job_listings()


def get_mock_job_listings() -> List[Dict[str, Any]]:
    """Provides realistic sample listings for Gurugram, Noida, and Remote."""
    return [
        {
            "title": "Senior QA Automation Engineer (Python + Playwright)",
            "company": "FastScale Tech",
            "url": "https://jobs.lever.co/fastscale/qa-sr-lead",
            "description": (
                "Location: Gurugram (Hybrid / Remote Option)\n"
                "Requirements: 5+ years experience building automated test frameworks from scratch using Python and Playwright. "
                "Must take autonomous project ownership of end-to-end quality architecture, API testing, CI/CD pipeline integration "
                "in GitHub Actions. Individual technical contributor / QA project leadership role, no direct HR/people management required."
            )
        },
        {
            "title": "Lead SDET / Senior Automation Lead",
            "company": "Noida FinTech Labs",
            "url": "https://boards.greenhouse.io/noidafintech/sdet-senior",
            "description": (
                "Location: Noida, UP\n"
                "We are seeking a Senior QA Automation Architect to drive test strategy across distributed microservices. "
                "Stack: Python, Playwright, PyTest, Docker, AWS, Kafka. "
                "Focus: Technical project leadership, mentor developers on test automation best practices, independent QA governance. "
                "Not a people management position."
            )
        },
        {
            "title": "Engineering Manager - QA & People Operations",
            "company": "Global Enterprise Services",
            "url": "https://careers.enterprise.com/roles/qa-manager",
            "description": (
                "Location: Gurugram, Cyber City\n"
                "Role: 100% People Management. Manage a team of 15 manual and automation QA engineers. "
                "Conduct quarterly performance reviews, resource planning, sprint capacity management, and client stakeholder presentations. "
                "Minimal hands-on coding. Legacy Java/Selenium stack."
            )
        },
        {
            "title": "Senior QA Engineer - Remote",
            "company": "CloudNative Solutions",
            "url": "https://wellfound.com/jobs/cloudnative-senior-qa-python",
            "description": (
                "Location: 100% Remote (India)\n"
                "Requirements: Deep expertise in Python-based automation suites (Playwright, Requests, PyTest). "
                "Architect resilient regression suites, performance testing, and continuous deployment gates. "
                "Individual project leadership and cross-functional QA ownership."
            )
        }
    ]


def evaluate_job_match(
    resume_text: str,
    job: Dict[str, Any],
    llm_base_url: str,
    llm_model: str,
    llm_api_key: str
) -> Dict[str, Any]:
    """
    Calls the LLM (local Ollama / LM Studio or OpenAI-compatible) to evaluate resume fit.
    Evaluates:
    - Python + Playwright expertise (heavily weighted)
    - Independent Project QA Leadership vs. Direct People Management
    """
    system_prompt = """You are an expert Senior Technical Recruiter and SDET Evaluation Engine.
Your task is to evaluate a candidate's resume against a specific Job Description.

Evaluation Guidelines:
1. Python + Playwright Stack (Weight: 45%):
   - Heavily reward strong proficiency in Python and Playwright for UI/API automation.
2. Independent Project QA Leadership (Weight: 35%):
   - Reward candidates and roles focused on technical QA leadership, test architecture, framework creation, and autonomous project quality ownership.
   - PENALIZE direct people management roles (e.g. HR reviews, line management, administrative oversight) because the candidate seeks technical/project leadership, NOT people management.
3. Domain, CI/CD, & Automation Depth (Weight: 20%):
   - CI/CD pipelines, PyTest, Docker, API testing, performance.

You must output valid JSON ONLY with these exact keys:
{
  "job_title": "<job title>",
  "company": "<company name>",
  "url": "<job url>",
  "match_score": <integer from 0 to 100>,
  "stack_fit": "<Brief evaluation of Python + Playwright match>",
  "leadership_type": "<'Independent Project QA Lead' or 'People Manager' or 'Individual Contributor'>",
  "reasoning": "<1-2 sentences summarizing why this matches or does not match>"
}
"""

    user_prompt = f"""### CANDIDATE RESUME:
{resume_text[:4000]}

### JOB DETAILS:
Title: {job.get('title')}
Company: {job.get('company')}
URL: {job.get('url')}
Description:
{job.get('description')}

Evaluate the match now and respond in strict JSON format."""

    # Attempt LLM call
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=llm_base_url,
            api_key=llm_api_key or "ollama"
        )
        
        response = client.chat.completions.create(
            model=llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"} if "gpt" in llm_model.lower() else None
        )
        
        content = response.choices[0].message.content.strip()
        # Clean markdown code blocks if returned
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        return data

    except Exception as e:
        # If local LLM server is not running, provide heuristic fallback
        return heuristic_evaluator(resume_text, job)


def heuristic_evaluator(resume_text: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based heuristic evaluator when LLM endpoint is offline."""
    desc = (job.get("description", "") + " " + job.get("title", "")).lower()
    resume_lower = resume_text.lower()
    
    score = 50
    has_python = "python" in desc
    has_playwright = "playwright" in desc
    is_people_mgr = any(k in desc for k in ["people management", "managing 15", "performance reviews", "100% people"])
    is_tech_lead = any(k in desc for k in ["project leadership", "architect", "independent", "ownership", "framework"])
    
    if has_python and has_playwright:
        score += 35
    elif has_python:
        score += 20
        
    if is_tech_lead:
        score += 15
        
    if is_people_mgr:
        score -= 40
        
    score = max(5, min(98, score))
    
    return {
        "job_title": job.get("title", "QA Engineer"),
        "company": job.get("company", "Company"),
        "url": job.get("url", ""),
        "match_score": score,
        "stack_fit": "Python + Playwright identified" if (has_python and has_playwright) else "Partial stack match",
        "leadership_type": "People Manager (Penalized)" if is_people_mgr else "Independent Project QA Lead",
        "reasoning": "Evaluated with high weighting on Python/Playwright and independent project QA leadership."
    }


def render_results_table(evaluations: List[Dict[str, Any]]):
    """Renders the final results table in terminal."""
    # Sort descending by match score
    evaluations = sorted(evaluations, key=lambda x: x.get("match_score", 0), reverse=True)
    
    if HAS_RICH and console:
        table = Table(
            title="🎯 Senior Software QA Automation Job Matches",
            header_style="bold magenta",
            show_lines=True
        )
        
        table.add_column("Rank", justify="center", style="dim", width=6)
        table.add_column("Score", justify="center", width=10)
        table.add_column("Job Title", style="bold cyan", width=32)
        table.add_column("Company", style="green", width=22)
        table.add_column("Leadership Fit", style="yellow", width=24)
        table.add_column("Job URL / Link", style="blue", overflow="fold")
        
        for idx, item in enumerate(evaluations, 1):
            score = item.get("match_score", 0)
            if score >= 80:
                score_str = f"[bold green]{score}%[/bold green] 🌟"
            elif score >= 60:
                score_str = f"[bold yellow]{score}%[/bold yellow] 👍"
            else:
                score_str = f"[bold red]{score}%[/bold red] ⛔"
                
            table.add_row(
                str(idx),
                score_str,
                item.get("job_title", "N/A"),
                item.get("company", "N/A"),
                item.get("leadership_type", "N/A"),
                item.get("url", "N/A")
            )
            
        console.print("\n")
        console.print(table)
        console.print("\n[bold dim]Priority filters applied: Python + Playwright, Gurugram/Noida/Remote, Independent QA Leadership.[/bold dim]\n")
    else:
        # Fallback ASCII table
        print("\n" + "=" * 90)
        print(f"{'Rank':<6} {'Score':<8} {'Job Title':<32} {'Company':<20} {'Job URL'}")
        print("=" * 90)
        for idx, item in enumerate(evaluations, 1):
            score = item.get("match_score", 0)
            print(f"{idx:<6} {score:<7}% {item.get('job_title')[:30]:<32} {item.get('company')[:18]:<20} {item.get('url')}")
        print("=" * 90 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Senior QA Automation Job Matcher & Firecrawl Evaluator"
    )
    parser.add_argument(
        "--resume",
        "-r",
        type=str,
        required=True,
        help="Path to candidate resume file (.pdf, .txt, .md)"
    )
    parser.add_argument(
        "--location",
        "-l",
        type=str,
        default="Gurugram OR Noida OR Remote",
        help="Target locations for role extraction"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum job postings to evaluate"
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        default=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
        help="Base URL for local/remote LLM endpoint"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLM_MODEL", "llama3.2"),
        help="LLM model identifier"
    )

    args = parser.parse_args()

    log_info("Starting Job Matcher Agent Workflow...")
    
    # 1. Parse Resume
    try:
        resume_text = parse_resume(args.resume)
        log_success(f"Loaded resume from '{args.resume}' ({len(resume_text)} chars).")
    except Exception as e:
        log_error(f"Failed to read resume: {e}")
        sys.exit(1)

    # 2. Firecrawl Search
    search_query = f'"Senior Software QA Automation Engineer" ({args.location}) "Python"'
    log_info(f"Targeting role query: {search_query}")
    
    jobs = search_jobs_with_firecrawl(
        query=search_query,
        limit=args.limit
    )
    log_success(f"Retrieved {len(jobs)} candidate job listings for evaluation.")

    # 3. LLM Evaluation
    log_info(f"Evaluating candidate fit against roles via LLM ({args.model})...")
    evaluations = []
    
    for job in jobs:
        ev = evaluate_job_match(
            resume_text=resume_text,
            job=job,
            llm_base_url=args.llm_url,
            llm_model=args.model,
            llm_api_key=os.getenv("LLM_API_KEY", "")
        )
        evaluations.append(ev)

    # 4. Render Table
    render_results_table(evaluations)


if __name__ == "__main__":
    main()
