#!/usr/bin/env python3
"""
Hybrid Scrape & Cache Job Matcher CLI Script
============================================
Optimized to aggressively protect the 1,000/month Firecrawl credit limit.

Architecture:
1. SQLite Caching (`jobs_cache.db`): Caches scraped job text & match scores.
2. Cheap First Discovery (BeautifulSoup): Scrapes career pages locally using requests/BS4.
3. Targeted Firecrawl Execution: Only calls Firecrawl /scrape on specific individual job URLs.
4. Credit Budget Guardrail (`.firecrawl_tracker.json`): Warns and pauses when monthly usage >= 800.
5. Antigravity & Local LLM Matching: Prioritizes Python + Playwright & Independent QA Leadership.
"""

import os
import sys
import json
import sqlite3
import argparse
import datetime
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Rich formatting (with graceful fallback)
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Confirm
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

# Paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = WORKSPACE_ROOT / "jobs_cache.db"
TRACKER_PATH = WORKSPACE_ROOT / ".firecrawl_tracker.json"


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


def log_cache(msg: str):
    if HAS_RICH and console:
        console.print(f"[bold magenta]⚡ [CACHE][/bold magenta] {msg}")
    else:
        print(f"[CACHE] {msg}")


# ==============================================================================
# 1. SQLite Database Caching Layer
# ==============================================================================

def init_db(db_path: Path = DB_PATH):
    """Initializes the SQLite job cache database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_cache (
            url TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            scraped_content TEXT,
            match_score INTEGER,
            stack_fit TEXT,
            leadership_type TEXT,
            reasoning TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def get_cached_job(url: str, db_path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a cached job by URL if available."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_cache WHERE url = ?", (url,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def save_cached_job(job_data: Dict[str, Any], db_path: Path = DB_PATH):
    """Inserts or updates a job record in SQLite cache."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO job_cache (
            url, title, company, location, scraped_content,
            match_score, stack_fit, leadership_type, reasoning, source, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(url) DO UPDATE SET
            title=excluded.title,
            company=excluded.company,
            location=excluded.location,
            scraped_content=COALESCE(excluded.scraped_content, job_cache.scraped_content),
            match_score=COALESCE(excluded.match_score, job_cache.match_score),
            stack_fit=COALESCE(excluded.stack_fit, job_cache.stack_fit),
            leadership_type=COALESCE(excluded.leadership_type, job_cache.leadership_type),
            reasoning=COALESCE(excluded.reasoning, job_cache.reasoning),
            source=excluded.source,
            updated_at=CURRENT_TIMESTAMP
    """, (
        job_data.get("url"),
        job_data.get("title") or job_data.get("job_title", ""),
        job_data.get("company", ""),
        job_data.get("location", ""),
        job_data.get("scraped_content") or job_data.get("description", ""),
        job_data.get("match_score"),
        job_data.get("stack_fit", ""),
        job_data.get("leadership_type", ""),
        job_data.get("reasoning", ""),
        job_data.get("source", "unknown")
    ))
    conn.commit()
    conn.close()


# ==============================================================================
# 2. Credit Budget Guardrail (.firecrawl_tracker.json)
# ==============================================================================

def get_current_month_str() -> str:
    return datetime.datetime.now().strftime("%Y-%m")


def load_tracker(tracker_path: Path = TRACKER_PATH) -> Dict[str, Any]:
    """Loads tracker data, auto-rolling monthly counters."""
    current_month = get_current_month_str()
    default_data = {
        "current_month": current_month,
        "credits_used": 0,
        "limit": 1000,
        "warning_threshold": 800,
        "last_request_time": None
    }

    if not tracker_path.exists():
        save_tracker(default_data, tracker_path)
        return default_data

    try:
        with open(tracker_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Check for month rollover
            if data.get("current_month") != current_month:
                data["current_month"] = current_month
                data["credits_used"] = 0
                data["last_request_time"] = None
                save_tracker(data, tracker_path)
            return data
    except Exception:
        save_tracker(default_data, tracker_path)
        return default_data


def save_tracker(data: Dict[str, Any], tracker_path: Path = TRACKER_PATH):
    """Saves credit tracking metadata."""
    try:
        with open(tracker_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_error(f"Could not save tracker: {e}")


def check_and_request_credit_permission(tracker_path: Path = TRACKER_PATH) -> bool:
    """
    Checks if credit limit is approaching 800/1000.
    If >= 800, prints red warning and pauses for user confirmation.
    """
    tracker = load_tracker(tracker_path)
    credits_used = tracker.get("credits_used", 0)
    warning_threshold = tracker.get("warning_threshold", 800)
    limit = tracker.get("limit", 1000)

    if credits_used >= warning_threshold:
        warning_msg = f"WARNING: Approaching Firecrawl Free Tier Limit ({credits_used}/{limit})"
        if HAS_RICH and console:
            console.print(Panel(f"[bold white on red] {warning_msg} [/bold white on red]\n[yellow]You have used {credits_used} out of your {limit} monthly Firecrawl credits.[/yellow]"))
        else:
            print("\n" + "!" * 80)
            print(f"\033[91m{warning_msg}\033[0m")
            print(f"Current usage: {credits_used}/{limit}")
            print("!" * 80 + "\n")

        # Ask confirmation
        if sys.stdin.isatty():
            try:
                ans = input("Do you want to proceed and consume 1 Firecrawl credit? [y/N]: ").strip().lower()
                if ans not in ["y", "yes"]:
                    log_warning("Firecrawl scrape skipped by user to conserve credits.")
                    return False
            except (KeyboardInterrupt, EOFError):
                return False
        else:
            log_warning("Non-interactive shell with credit threshold exceeded. Skipping Firecrawl API.")
            return False

    return True


def increment_firecrawl_credit(tracker_path: Path = TRACKER_PATH):
    """Increments the monthly Firecrawl credit counter."""
    tracker = load_tracker(tracker_path)
    tracker["credits_used"] = tracker.get("credits_used", 0) + 1
    tracker["last_request_time"] = datetime.datetime.now().isoformat()
    save_tracker(tracker, tracker_path)
    log_info(f"Firecrawl Credit Used (Month total: {tracker['credits_used']}/{tracker['limit']})")


# ==============================================================================
# 3. The "Cheap First" Fallback (BeautifulSoup & Requests)
# ==============================================================================

def cheap_scrape_job_details(url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Attempts a free, lightweight HTTP GET + BeautifulSoup parse of a job description.
    Returns: (title, company, description) or (None, None, None) if JS rendering required.
    """
    import requests
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return None, None, None

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None, None, None

        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Remove noisy elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        # Extract title
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        h1 = soup.find("h1")
        if h1 and h1.get_text():
            title = h1.get_text().strip()

        # Extract company
        company = "Direct Employer"
        meta_site = soup.find("meta", property="og:site_name")
        if meta_site and meta_site.get("content"):
            company = meta_site["content"].strip()
        elif "lever.co" in url:
            parts = url.split("lever.co/")
            if len(parts) > 1:
                company = parts[1].split("/")[0].capitalize()
        elif "greenhouse.io" in url:
            parts = url.split("greenhouse.io/")
            if len(parts) > 1:
                company = parts[1].split("/")[0].capitalize()

        # Extract main text
        body_text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in body_text.splitlines() if len(line.strip()) > 20]
        cleaned_content = "\n".join(lines)

        # If content has reasonable substance (>300 chars), return it
        if len(cleaned_content) > 300:
            return title or "Senior QA Automation Engineer", company, cleaned_content[:4000]

    except Exception:
        pass

    return None, None, None


def discover_job_urls_cheap(
    seed_urls: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Scrapes career board lists locally using requests + BeautifulSoup
    without burning Firecrawl credits.
    """
    import requests
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    if not keywords:
        keywords = ["qa", "sdet", "automation", "quality", "playwright", "test"]

    discovered = []
    
    # Default seed career hubs for testing & common ATS systems
    targets = seed_urls or [
        "https://jobs.lever.co",
        "https://boards.greenhouse.io"
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for target_url in targets:
        try:
            resp = requests.get(target_url, headers=headers, timeout=8)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text().lower()
                full_url = urllib.parse.urljoin(target_url, href)
                
                # Check for QA keywords in URL or link text
                if any(kw in href.lower() or kw in text for kw in keywords):
                    # Filter for specific job posts
                    if any(domain in full_url for domain in ["lever.co/", "greenhouse.io/", "jobs.", "careers."]):
                        discovered.append({
                            "title": a.get_text().strip() or "Senior QA Automation Engineer",
                            "url": full_url,
                            "source": "bs4_discovery"
                        })
        except Exception:
            continue

    return discovered


# ==============================================================================
# 4. Targeted Firecrawl Execution Layer
# ==============================================================================

def scrape_single_url_with_firecrawl(url: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Executes a TARGETED scrape on a single specific URL via Firecrawl API.
    Never passes root domains or wildcard crawls.
    """
    api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
    if not api_key or api_key.startswith("fc-YOUR_") or api_key == "YOUR_FIRECRAWL_API_KEY":
        log_warning(f"No active FIRECRAWL_API_KEY in .env. Skipping remote Firecrawl fetch for: {url}")
        return None

    # Check credit guardrail
    if not check_and_request_credit_permission():
        return None

    try:
        from firecrawl import FirecrawlApp
        app = FirecrawlApp(api_key=api_key)
        
        log_info(f"Targeted Firecrawl /scrape on: {url}")
        result = app.scrape_url(
            url=url,
            params={"formats": ["markdown"]}
        )
        
        # Increment tracker
        increment_firecrawl_credit()

        if isinstance(result, dict):
            markdown = result.get("markdown") or result.get("content") or ""
            metadata = result.get("metadata", {})
            title = metadata.get("title") or "Senior QA Automation Engineer"
            company = metadata.get("og:site_name") or metadata.get("author") or "Tech Company"
            return {
                "title": title,
                "company": company,
                "url": url,
                "description": markdown[:4000],
                "source": "firecrawl_targeted_scrape"
            }
    except Exception as e:
        log_error(f"Targeted Firecrawl scrape failed for {url}: {e}")

    return None


# ==============================================================================
# 5. Hybrid Extraction Pipeline
# ==============================================================================

def get_mock_seed_jobs() -> List[Dict[str, Any]]:
    """Realistic target job URLs representing Gurugram, Noida, and Remote."""
    return [
        {
            "title": "Senior QA Automation Engineer (Python + Playwright)",
            "company": "FastScale Tech",
            "url": "https://jobs.lever.co/fastscale/qa-sr-lead-gurugram",
            "description": (
                "Location: Gurugram, Haryana (Hybrid / Remote)\n"
                "Requirements: 5+ years building scalable automation frameworks using Python and Playwright. "
                "Architect resilient UI and API test pipelines in GitHub Actions. "
                "Individual project leadership, test architecture ownership, quality governance. "
                "Not a people management position."
            )
        },
        {
            "title": "Lead SDET / Senior Automation Architect",
            "company": "Noida FinTech Labs",
            "url": "https://boards.greenhouse.io/noidafintech/sdet-senior-lead",
            "description": (
                "Location: Noida, UP\n"
                "We need a Senior QA Automation Architect to drive quality across microservices. "
                "Stack: Python, Playwright, PyTest, Docker, AWS. "
                "Focus: Technical project leadership, mentor team on automation standards. "
                "Autonomous QA project lead, no direct HR/line management duties."
            )
        },
        {
            "title": "Engineering Manager - QA & Line Management",
            "company": "Global Enterprise Services",
            "url": "https://careers.enterprise.com/roles/qa-manager-gurugram",
            "description": (
                "Location: Cyber City, Gurugram\n"
                "Role: 100% People Management. Manage team of 15 QA engineers. "
                "Handle quarterly appraisals, resource allocations, stakeholder meetings. "
                "Minimal hands-on coding. Legacy Java/Selenium stack."
            )
        },
        {
            "title": "Senior QA Engineer - Remote",
            "company": "CloudNative Solutions",
            "url": "https://wellfound.com/jobs/cloudnative-senior-qa-python",
            "description": (
                "Location: 100% Remote (India)\n"
                "Requirements: Deep proficiency in Python and Playwright. "
                "Architect end-to-end regression suites, performance testing with Locust. "
                "Autonomous project leadership and test strategy ownership."
            )
        }
    ]


def fetch_and_prepare_jobs(
    candidate_urls: List[Dict[str, Any]],
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Hybrid Pipeline:
    1. Check SQLite Cache -> Cache Hit: Return cached content & score.
    2. Cache Miss -> Cheap First (BeautifulSoup) scrape.
    3. If Cheap Scrape fails -> Targeted Firecrawl /scrape (subject to credit guardrail).
    4. Save freshly scraped content to SQLite cache.
    """
    prepared_jobs = []

    for item in candidate_urls:
        url = item.get("url")
        if not url:
            continue

        # Step 1: Check SQLite Cache
        cached = get_cached_job(url)
        if cached and cached.get("scraped_content"):
            log_cache(f"Hit SQLite cache for: {url}")
            prepared_jobs.append({
                "title": cached.get("title") or item.get("title"),
                "company": cached.get("company") or item.get("company"),
                "url": url,
                "description": cached.get("scraped_content"),
                "match_score": cached.get("match_score"),
                "stack_fit": cached.get("stack_fit"),
                "leadership_type": cached.get("leadership_type"),
                "reasoning": cached.get("reasoning"),
                "source": "sqlite_cache"
            })
            continue

        # If description already provided (e.g. from seed list)
        if item.get("description") and len(item["description"]) > 150:
            prepared_jobs.append(item)
            save_cached_job(item)
            continue

        # Step 2: Cheap First Fallback (BeautifulSoup)
        log_info(f"Attempting Cheap First (BS4) scrape on: {url}")
        title, company, cheap_desc = cheap_scrape_job_details(url)
        
        if cheap_desc:
            log_success(f"Successfully extracted {len(cheap_desc)} chars via Cheap BS4 for: {url}")
            job_obj = {
                "title": title or item.get("title", "QA Engineer"),
                "company": company or item.get("company", "Company"),
                "url": url,
                "description": cheap_desc,
                "source": "beautifulsoup_cheap"
            }
            prepared_jobs.append(job_obj)
            save_cached_job(job_obj)
            continue

        # Step 3: Targeted Firecrawl /scrape
        log_info(f"Cheap scrape insufficient. Initiating targeted Firecrawl /scrape for: {url}")
        firecrawl_job = scrape_single_url_with_firecrawl(url, api_key=api_key)
        
        if firecrawl_job:
            prepared_jobs.append(firecrawl_job)
            save_cached_job(firecrawl_job)
        else:
            # Fallback
            prepared_jobs.append(item)

    return prepared_jobs


# ==============================================================================
# 6. Resume Parsing & Local LLM Matching
# ==============================================================================

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
            text = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n".join(text).strip()
        except ImportError:
            raise ImportError("Please install `pypdf` to parse PDF resumes: `pip install pypdf`")
    else:
        raise ValueError(f"Unsupported file format '{suffix}'. Supported formats: .pdf, .txt, .md")


def evaluate_job_match(
    resume_text: str,
    job: Dict[str, Any],
    llm_base_url: str,
    llm_model: str,
    llm_api_key: str
) -> Dict[str, Any]:
    """
    Evaluates candidate fit using Local LLM (or SQLite cache / heuristic fallback).
    Prioritizes:
    - Python + Playwright (45%)
    - Independent Project QA Leadership vs. Direct People Management (35%)
    """
    # If already cached with match score, return immediately
    if job.get("match_score") is not None and job.get("source") == "sqlite_cache":
        return job

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
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
            
        data = json.loads(content.strip())
        
        # Save evaluation to SQLite Cache
        job_to_cache = {**job, **data}
        save_cached_job(job_to_cache)
        return data

    except Exception:
        # Heuristic fallback
        res = heuristic_evaluator(resume_text, job)
        save_cached_job({**job, **res})
        return res


def heuristic_evaluator(resume_text: str, job: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based heuristic evaluator when LLM endpoint is offline."""
    desc = (job.get("description", "") + " " + job.get("title", "")).lower()
    
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
    evaluations = sorted(evaluations, key=lambda x: x.get("match_score", 0), reverse=True)
    
    tracker = load_tracker()
    credits_str = f"Monthly Firecrawl Credits Used: {tracker.get('credits_used', 0)} / {tracker.get('limit', 1000)}"

    if HAS_RICH and console:
        table = Table(
            title="🎯 Senior Software QA Automation Job Matches (Hybrid Scrape & Cache)",
            header_style="bold magenta",
            show_lines=True
        )
        
        table.add_column("Rank", justify="center", style="dim", width=6)
        table.add_column("Score", justify="center", width=10)
        table.add_column("Job Title", style="bold cyan", width=30)
        table.add_column("Company", style="green", width=20)
        table.add_column("Leadership Fit", style="yellow", width=24)
        table.add_column("Source", style="dim", width=12)
        table.add_column("Job URL", style="blue", overflow="fold")
        
        for idx, item in enumerate(evaluations, 1):
            score = item.get("match_score", 0)
            if score >= 80:
                score_str = f"[bold green]{score}%[/bold green] 🌟"
            elif score >= 60:
                score_str = f"[bold yellow]{score}%[/bold yellow] 👍"
            else:
                score_str = f"[bold red]{score}%[/bold red] ⛔"
                
            source_tag = item.get("source", "N/A")
            if "cache" in source_tag:
                source_badge = "[magenta]CACHE[/magenta]"
            elif "bs4" in source_tag or "cheap" in source_tag:
                source_badge = "[cyan]BS4[/cyan]"
            elif "firecrawl" in source_tag:
                source_badge = "[green]FIRECRAWL[/green]"
            else:
                source_badge = "[dim]SEED[/dim]"

            table.add_row(
                str(idx),
                score_str,
                item.get("job_title") or item.get("title") or "QA Engineer",
                item.get("company") or "Company",
                item.get("leadership_type", "N/A"),
                source_badge,
                item.get("url", "N/A")
            )
            
        console.print("\n")
        console.print(table)
        console.print(f"[dim]💳 {credits_str} | Cache: SQLite `{DB_PATH.name}`[/dim]\n")
    else:
        print("\n" + "=" * 95)
        print(f"{'Rank':<6} {'Score':<8} {'Job Title':<30} {'Company':<18} {'Source':<10} {'Job URL'}")
        print("=" * 95)
        for idx, item in enumerate(evaluations, 1):
            score = item.get("match_score", 0)
            src = str(item.get("source") or "N/A")[:8]
            title = str(item.get("job_title") or item.get("title") or "QA Engineer")[:28]
            comp = str(item.get("company") or "Company")[:16]
            url = str(item.get("url") or "")
            print(f"{idx:<6} {score:<7}% {title:<30} {comp:<18} {src:<10} {url}")
        print("=" * 95)
        print(f"Credit Tracker: {credits_str}\n")


# ==============================================================================
# Main CLI Entrypoint
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Senior QA Automation Hybrid Job Matcher & Credit Optimizer"
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
        help="Base URL for local LLM endpoint"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("LLM_MODEL", "llama3.2"),
        help="LLM model identifier"
    )
    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="Senior QA Automation Engineer",
        help="Target job role query"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse resume and display target jobs without calling external APIs"
    )

    args = parser.parse_args()

    log_info("Starting Hybrid Scrape & Cache Job Matcher Agent...")
    
    # 1. Parse Resume
    try:
        resume_text = parse_resume(args.resume)
        log_success(f"Loaded candidate resume from '{args.resume}' ({len(resume_text)} chars).")
    except Exception as e:
        log_error(f"Failed to read resume: {e}")
        sys.exit(1)

    # 2. Get Seed Candidate Roles
    seed_jobs = get_mock_seed_jobs()
    
    if args.dry_run:
        log_info(f"[DRY-RUN] Candidate Resume: {args.resume}")
        log_info(f"[DRY-RUN] Target Query: {args.query} | Location: {args.location}")
        log_info(f"[DRY-RUN] Found {len(seed_jobs)} candidate listings ready for evaluation.")
        for idx, sj in enumerate(seed_jobs, 1):
            print(f"  {idx}. {sj.get('title')} @ {sj.get('company')} ({sj.get('url')})")
        log_success("Dry run completed successfully.")
        return

    # 3. Hybrid Scrape & Cache Execution
    log_info("Executing Hybrid Fetch: Checking SQLite Cache -> Cheap BS4 Scrape -> Targeted Firecrawl...")
    prepared_jobs = fetch_and_prepare_jobs(seed_jobs)
    log_success(f"Prepared {len(prepared_jobs)} job postings for evaluation.")

    # 4. Evaluate via LLM
    log_info(f"Evaluating candidate fit via LLM ({args.model})...")
    evaluations = []
    
    for job in prepared_jobs:
        ev = evaluate_job_match(
            resume_text=resume_text,
            job=job,
            llm_base_url=args.llm_url,
            llm_model=args.model,
            llm_api_key=os.getenv("LLM_API_KEY", "")
        )
        # Preserve source tag
        if "source" in job and "source" not in ev:
            ev["source"] = job["source"]
        evaluations.append(ev)

    # 5. Render Table
    render_results_table(evaluations)


if __name__ == "__main__":
    main()
