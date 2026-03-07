#!/usr/bin/env python3
"""
ResumeCraft - AI-powered resume and cover letter generator.
Tailored to specific job descriptions using local AI (Ollama).

Free tier:  Resume generation only
Premium:    + Cover letter, LinkedIn summary, ATS keyword analysis, multiple formats

Usage:
  resume-craft --job-desc "Software Engineer..." --user-info profile.json
  resume-craft --job-url "https://linkedin.com/jobs/..." --user-info profile.json
  resume-craft --activate YOUR-LICENSE-KEY
"""

__version__ = "1.0.0"

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Install dependencies: pip install requests beautifulsoup4 lxml")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
try:
    from license_gate import LicenseGate
except ImportError:
    class LicenseGate:
        def __init__(self, n): pass
        def check(self, silent=False): return "trial"
        def is_premium(self): return True
        def require_premium(self, f=""): return True
        def handle_activate_flag(self, a=None): return None
        @staticmethod
        def add_activate_arg(p): p.add_argument('--activate', help='License key')

gate = LicenseGate("resume-craft")

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}


def query_ollama(prompt, model='llama3.1'):
    try:
        resp = requests.post('http://localhost:11434/api/generate', json={
            'model': model, 'prompt': prompt, 'stream': False,
            'options': {'temperature': 0.6, 'num_predict': 4096}
        }, timeout=180)
        resp.raise_for_status()
        return resp.json().get('response', '')
    except requests.ConnectionError:
        print("Ollama not running. Start with: ollama serve")
        print("Then pull a model: ollama pull llama3.1")
        sys.exit(1)
    except Exception as e:
        print(f"Ollama error: {e}")
        sys.exit(1)


def fetch_job_description(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'footer']):
            tag.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text[:3000]
    except Exception as e:
        print(f"  Could not fetch job URL: {e}")
        return None


def generate_resume(user_info, job_desc, model='llama3.1'):
    prompt = f"""Create a professional, ATS-optimized resume based on the candidate info and job description below.

CANDIDATE INFORMATION:
{json.dumps(user_info, indent=2) if isinstance(user_info, dict) else user_info}

JOB DESCRIPTION:
{job_desc}

Requirements:
- Format in clean Markdown
- Start with candidate name and contact info
- Include a Professional Summary (3-4 lines tailored to this specific job)
- List relevant Skills (match keywords from job description)
- Work Experience in reverse chronological order with bullet points
- Education section
- Use action verbs and quantified achievements
- Naturally incorporate keywords from the job description
- Keep to 1-2 pages equivalent

Generate the complete resume now:"""

    return query_ollama(prompt, model)


def generate_cover_letter(user_info, job_desc, company='', model='llama3.1'):
    prompt = f"""Write a compelling cover letter for this job application.

CANDIDATE:
{json.dumps(user_info, indent=2) if isinstance(user_info, dict) else user_info}

JOB DESCRIPTION:
{job_desc}

{f'COMPANY: {company}' if company else ''}

Requirements:
- 3-4 paragraphs, approximately 300 words
- Opening: Hook that shows genuine interest and relevant achievement
- Middle: Connect your experience directly to their requirements (2-3 specific examples)
- Closing: Enthusiastic call-to-action
- Professional but personable tone
- Do NOT be generic - reference specific requirements from the job posting
- Format in Markdown

Generate the cover letter now:"""

    return query_ollama(prompt, model)


def generate_linkedin_summary(user_info, model='llama3.1'):
    prompt = f"""Write a compelling LinkedIn "About" section for this professional.

PROFILE:
{json.dumps(user_info, indent=2) if isinstance(user_info, dict) else user_info}

Requirements:
- 200-300 words
- First person, professional but approachable
- Open with a strong hook (not "I am a...")
- Highlight key achievements and specialties
- Include relevant keywords for LinkedIn search
- End with what you're looking for / open to
- Format in plain text (no Markdown headers)

Write the LinkedIn summary now:"""

    return query_ollama(prompt, model)


def analyze_ats_keywords(job_desc, resume_text, model='llama3.1'):
    prompt = f"""Analyze ATS (Applicant Tracking System) keyword match between this job description and resume.

JOB DESCRIPTION:
{job_desc}

RESUME:
{resume_text}

Provide:
1. List of MATCHED keywords (found in both)
2. List of MISSING keywords (in job desc but not in resume)
3. Match percentage estimate
4. Top 5 suggestions to improve keyword match
5. Overall ATS compatibility score (1-10)

Format clearly in Markdown with headers."""

    return query_ollama(prompt, model)


def create_user_template():
    template = {
        "name": "Your Full Name",
        "email": "email@example.com",
        "phone": "+1-555-0000",
        "location": "City, State",
        "linkedin": "linkedin.com/in/yourprofile",
        "website": "",
        "summary": "Brief professional summary",
        "skills": ["Skill 1", "Skill 2", "Skill 3"],
        "experience": [
            {
                "title": "Job Title",
                "company": "Company Name",
                "dates": "2022-Present",
                "achievements": [
                    "Achievement 1 with metrics",
                    "Achievement 2 with metrics"
                ]
            }
        ],
        "education": [
            {
                "degree": "Degree Name",
                "school": "University Name",
                "year": "2020"
            }
        ],
        "certifications": [],
        "languages": []
    }
    return template


def main():
    parser = argparse.ArgumentParser(
        description='ResumeCraft - AI-powered resume & cover letter generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  resume_craft --job-desc "Software Engineer..." --user-info profile.json
  resume_craft --job-url "https://linkedin.com/jobs/..." --user-info profile.json
  resume_craft --job-desc "..." --name "John Doe" --type both
  resume_craft --activate YOUR-KEY""")
    parser.add_argument('--job-desc', help='Job description text')
    parser.add_argument('--job-url', help='URL of job posting to scrape')
    parser.add_argument('--name', help='Candidate name (basic mode)')
    parser.add_argument('--user-info', help='Path to JSON file with candidate info')
    parser.add_argument('--company', default='', help='Company name')
    parser.add_argument('--type', '-t', choices=['resume', 'cover', 'linkedin', 'ats', 'both', 'full'],
                        default='resume', help='Output type')
    parser.add_argument('--output', '-o', default='resume_output.md', help='Output file')
    parser.add_argument('--model', '-m', default='llama3.1', help='Ollama model')
    parser.add_argument('--init', action='store_true', help='Create user info template')
    parser.add_argument('--version', '-v', action='version', version=f'ResumeCraft {__version__}')
    LicenseGate.add_activate_arg(parser)
    args = parser.parse_args()

    gate.handle_activate_flag(args)
    if hasattr(args, 'activate') and args.activate:
        return

    gate.check()

    # Create template
    if args.init:
        template_path = Path('my_profile.json')
        template_path.write_text(json.dumps(create_user_template(), indent=2))
        print(f"  Created template: {template_path}")
        print(f"  Fill it in, then run: resume_craft --job-desc \"...\" --user-info {template_path}")
        return

    # Get job description
    job_desc = args.job_desc
    if args.job_url and not job_desc:
        print(f"  Fetching job description from: {args.job_url}")
        job_desc = fetch_job_description(args.job_url)
    if not job_desc and args.type != 'linkedin':
        print("  Provide --job-desc or --job-url (or use --init to create profile template)")
        parser.print_help()
        return

    # Get user info
    user_info = {}
    if args.user_info:
        user_info = json.loads(Path(args.user_info).read_text())
    elif args.name:
        user_info = {'name': args.name}
    else:
        if not Path('my_profile.json').exists():
            print("  No user info provided. Creating template...")
            Path('my_profile.json').write_text(json.dumps(create_user_template(), indent=2))
            print(f"  Fill in my_profile.json and run again with --user-info my_profile.json")
            return
        user_info = json.loads(Path('my_profile.json').read_text())

    # Premium feature gates
    if args.type == 'cover' and not gate.require_premium("Cover letter generation"):
        args.type = 'resume'
    if args.type == 'linkedin' and not gate.require_premium("LinkedIn summary generation"):
        return
    if args.type == 'ats' and not gate.require_premium("ATS keyword analysis"):
        return
    if args.type == 'full' and not gate.require_premium("Full package (resume + cover + LinkedIn + ATS)"):
        args.type = 'resume'
    if args.type == 'both' and not gate.require_premium("Cover letter generation"):
        args.type = 'resume'

    output_parts = []
    output_parts.append(f"---\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nTool: ResumeCraft v{__version__}\n---\n")

    if args.type in ('resume', 'both', 'full'):
        print("  Generating resume...")
        resume = generate_resume(user_info, job_desc, args.model)
        output_parts.append("# RESUME\n\n" + resume)

    if args.type in ('cover', 'both', 'full'):
        print("  Generating cover letter...")
        cover = generate_cover_letter(user_info, job_desc, args.company, args.model)
        output_parts.append("\n\n---\n\n# COVER LETTER\n\n" + cover)

    if args.type in ('linkedin', 'full'):
        print("  Generating LinkedIn summary...")
        linkedin = generate_linkedin_summary(user_info, args.model)
        output_parts.append("\n\n---\n\n# LINKEDIN SUMMARY\n\n" + linkedin)

    if args.type in ('ats', 'full'):
        print("  Analyzing ATS keyword match...")
        resume_text = output_parts[-1] if 'resume' in args.type or args.type == 'full' else generate_resume(user_info, job_desc, args.model)
        ats = analyze_ats_keywords(job_desc, resume_text, args.model)
        output_parts.append("\n\n---\n\n# ATS KEYWORD ANALYSIS\n\n" + ats)

    Path(args.output).write_text('\n'.join(output_parts), encoding='utf-8')
    print(f"  Saved to {args.output}")


if __name__ == '__main__':
    main()
