"""Core resume and cover letter generation engine."""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

from resume_craft.licensing import check_limit, get_tier


@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    website: str = ""
    summary: str = ""
    experience: list = field(default_factory=list)
    education: list = field(default_factory=list)
    skills: list = field(default_factory=list)
    certifications: list = field(default_factory=list)
    projects: list = field(default_factory=list)


@dataclass
class ResumeResult:
    format: str
    content: str
    word_count: int
    ats_score: Optional[int] = None
    ats_feedback: list = field(default_factory=list)


TEMPLATES = {
    "basic": {
        "sections": ["contact", "summary", "experience", "education", "skills"],
        "style": "clean",
    },
    "modern": {
        "sections": ["contact", "summary", "skills", "experience", "education", "projects"],
        "style": "two-column",
    },
    "executive": {
        "sections": ["contact", "executive_summary", "experience", "achievements", "education"],
        "style": "formal",
    },
    "creative": {
        "sections": ["contact", "about_me", "skills", "experience", "projects", "education"],
        "style": "visual",
    },
    "tech": {
        "sections": ["contact", "summary", "skills", "experience", "projects", "certifications"],
        "style": "technical",
    },
}


class ResumeBuilder:
    """Build resumes, cover letters, and optimize for ATS."""

    def __init__(self, api_key=None, provider="openai"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.provider = provider
        self._ai_available = bool(self.api_key)

    def build_resume(self, data, template="basic", target_role=None, job_description=None):
        """Generate a resume from structured data.

        Args:
            data: ResumeData or dict with resume fields.
            template: Template name (basic, modern, executive, creative, tech).
            target_role: Target job title for tailoring.
            job_description: Job description to optimize against.

        Returns:
            ResumeResult with formatted resume content.
        """
        allowed, msg = check_limit("template", template)
        if not allowed:
            raise PermissionError(msg)

        if isinstance(data, dict):
            data = ResumeData(**{k: v for k, v in data.items() if hasattr(ResumeData, k)})

        if self._ai_available and (target_role or job_description):
            content = self._ai_build_resume(data, template, target_role, job_description)
        else:
            content = self._template_build_resume(data, template)

        return ResumeResult(
            format="markdown",
            content=content,
            word_count=len(content.split()),
        )

    def generate_cover_letter(self, data, company, role, job_description=None, tone="professional"):
        """Generate a tailored cover letter (Premium feature).

        Args:
            data: ResumeData or dict with personal info.
            company: Target company name.
            role: Target role/position.
            job_description: Job description for tailoring.
            tone: Writing tone.

        Returns:
            ResumeResult with cover letter content.
        """
        allowed, msg = check_limit("cover_letter")
        if not allowed:
            raise PermissionError(msg)

        if isinstance(data, dict):
            data = ResumeData(**{k: v for k, v in data.items() if hasattr(ResumeData, k)})

        if self._ai_available:
            content = self._ai_cover_letter(data, company, role, job_description, tone)
        else:
            content = self._template_cover_letter(data, company, role)

        return ResumeResult(
            format="markdown",
            content=content,
            word_count=len(content.split()),
        )

    def optimize_linkedin(self, data, target_role=None):
        """Generate optimized LinkedIn profile sections (Premium feature).

        Args:
            data: ResumeData or dict.
            target_role: Target role for optimization.

        Returns:
            Dict with headline, about, experience sections.
        """
        allowed, msg = check_limit("linkedin_optimization")
        if not allowed:
            raise PermissionError(msg)

        if isinstance(data, dict):
            data = ResumeData(**{k: v for k, v in data.items() if hasattr(ResumeData, k)})

        if self._ai_available:
            return self._ai_linkedin(data, target_role)
        return self._template_linkedin(data, target_role)

    def score_ats(self, resume_text, job_description):
        """Score a resume against a job description for ATS compatibility (Premium).

        Args:
            resume_text: The resume text to score.
            job_description: The job description to match against.

        Returns:
            ResumeResult with ATS score and feedback.
        """
        allowed, msg = check_limit("ats_scoring")
        if not allowed:
            raise PermissionError(msg)

        # Keyword matching analysis
        resume_words = set(re.findall(r'\b\w+\b', resume_text.lower()))
        jd_words = set(re.findall(r'\b\w+\b', job_description.lower()))

        # Filter out common stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "shall", "can", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
            "neither", "each", "every", "all", "any", "few", "more", "most",
            "other", "some", "such", "no", "only", "same", "than", "too", "very",
            "this", "that", "these", "those", "i", "me", "my", "we", "our", "you",
            "your", "he", "him", "his", "she", "her", "it", "its", "they", "them",
        }

        jd_keywords = jd_words - stop_words
        matched = resume_words & jd_keywords
        match_rate = len(matched) / max(len(jd_keywords), 1) * 100

        feedback = []
        missing = jd_keywords - resume_words
        if missing:
            top_missing = sorted(missing)[:20]
            feedback.append(f"Missing keywords: {', '.join(top_missing)}")

        # Scoring
        score = min(100, int(match_rate * 1.5))

        # Format checks
        if len(resume_text) < 200:
            score -= 10
            feedback.append("Resume appears too short")
        if not re.search(r'\b(experience|work history|employment)\b', resume_text, re.I):
            score -= 5
            feedback.append("Missing clear 'Experience' section header")
        if not re.search(r'\b(education|degree|university|college)\b', resume_text, re.I):
            score -= 5
            feedback.append("Missing clear 'Education' section")
        if not re.search(r'\b(skills|technologies|tools)\b', resume_text, re.I):
            score -= 5
            feedback.append("Missing clear 'Skills' section")

        score = max(0, min(100, score))

        return ResumeResult(
            format="ats_report",
            content=f"ATS Compatibility Score: {score}/100\n\n" + "\n".join(f"- {f}" for f in feedback),
            word_count=len(resume_text.split()),
            ats_score=score,
            ats_feedback=feedback,
        )

    def _template_build_resume(self, data, template):
        tmpl = TEMPLATES.get(template, TEMPLATES["basic"])
        sections = []

        sections.append(f"# {data.name}")
        contact_parts = [p for p in [data.email, data.phone, data.location, data.linkedin, data.website] if p]
        if contact_parts:
            sections.append(" | ".join(contact_parts))
        sections.append("")

        if data.summary:
            sections.append("## Summary")
            sections.append(data.summary)
            sections.append("")

        if data.experience:
            sections.append("## Experience")
            for exp in data.experience:
                title = exp.get("title", "")
                company = exp.get("company", "")
                dates = exp.get("dates", "")
                sections.append(f"### {title} at {company}")
                sections.append(f"*{dates}*")
                for bullet in exp.get("bullets", []):
                    sections.append(f"- {bullet}")
                sections.append("")

        if data.education:
            sections.append("## Education")
            for edu in data.education:
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                year = edu.get("year", "")
                sections.append(f"**{degree}** - {school} ({year})")
            sections.append("")

        if data.skills:
            sections.append("## Skills")
            sections.append(", ".join(data.skills))
            sections.append("")

        if data.certifications:
            sections.append("## Certifications")
            for cert in data.certifications:
                sections.append(f"- {cert}")
            sections.append("")

        if data.projects:
            sections.append("## Projects")
            for proj in data.projects:
                name = proj.get("name", "")
                desc = proj.get("description", "")
                sections.append(f"**{name}**: {desc}")
            sections.append("")

        return "\n".join(sections)

    def _template_cover_letter(self, data, company, role):
        return (
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my interest in the {role} position at {company}. "
            f"With my background in {', '.join(data.skills[:3]) if data.skills else 'relevant technologies'}, "
            f"I am confident I can contribute to your team.\n\n"
            f"{data.summary or '[Add your professional summary]'}\n\n"
            f"I would welcome the opportunity to discuss how my experience aligns with "
            f"your needs. Thank you for your consideration.\n\n"
            f"Sincerely,\n{data.name}\n"
            f"{data.email}\n{data.phone}"
        )

    def _template_linkedin(self, data, target_role):
        role_str = target_role or "Professional"
        skills_str = " | ".join(data.skills[:5]) if data.skills else ""
        return {
            "headline": f"{role_str} | {skills_str}",
            "about": data.summary or f"[Configure AI API key for auto-generated LinkedIn About section targeting {role_str}]",
            "experience": data.experience,
        }

    def _ai_build_resume(self, data, template, target_role, job_description):
        prompt = (
            f"Create a professional resume in markdown format.\n"
            f"Template style: {template}\n"
            f"Target role: {target_role or 'general'}\n"
            f"Data: {json.dumps(self._data_to_dict(data))}\n"
        )
        if job_description:
            prompt += f"Optimize for this job description:\n{job_description}\n"
        return self._call_ai(prompt)

    def _ai_cover_letter(self, data, company, role, job_description, tone):
        prompt = (
            f"Write a {tone} cover letter for {role} at {company}.\n"
            f"Candidate info: {json.dumps(self._data_to_dict(data))}\n"
        )
        if job_description:
            prompt += f"Job description:\n{job_description}\n"
        return self._call_ai(prompt)

    def _ai_linkedin(self, data, target_role):
        prompt = (
            f"Generate optimized LinkedIn profile sections for a {target_role or 'professional'}.\n"
            f"Data: {json.dumps(self._data_to_dict(data))}\n"
            f"Return JSON with keys: headline, about, experience_bullets"
        )
        result = self._call_ai(prompt)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"headline": result[:200], "about": result, "experience": []}

    def _call_ai(self, prompt):
        if self.provider == "openai":
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional resume writer and career coach."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        raise ValueError(f"Unsupported provider: {self.provider}")

    def _data_to_dict(self, data):
        return {
            "name": data.name, "email": data.email, "phone": data.phone,
            "location": data.location, "summary": data.summary,
            "experience": data.experience, "education": data.education,
            "skills": data.skills, "certifications": data.certifications,
            "projects": data.projects,
        }
