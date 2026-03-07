# ResumeCraft

AI-powered resume and cover letter generator. Tailored to specific job descriptions using local AI.

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![License](https://img.shields.io/badge/License-MIT-green) ![Version](https://img.shields.io/badge/Version-1.0.0-orange)

## Features

| Feature | Free | Premium |
|---------|:----:|:-------:|
| ATS-optimized resume | Yes | Yes |
| Job description matching | Yes | Yes |
| Ollama (free local AI) | Yes | Yes |
| Markdown output | Yes | Yes |
| **Cover letter** | - | Yes |
| **LinkedIn summary** | - | Yes |
| **ATS keyword analysis** | - | Yes |
| **Full package (all-in-one)** | - | Yes |

**30-day free trial** includes all Premium features.

## How It Works

1. You provide your profile info (JSON) and a job description
2. AI analyzes the job requirements and tailors your resume
3. Keywords from the job posting are naturally incorporated
4. Output is ATS-optimized Markdown ready to paste into any template

## Install

```bash
pip install requests beautifulsoup4 lxml
# For free local AI:
# Install Ollama from https://ollama.ai
ollama pull llama3.1
```

## Quick Start

```bash
# Create your profile template
python resume_craft.py --init

# Edit my_profile.json with your info, then:

# Generate resume (free)
python resume_craft.py --job-desc "We're hiring a Python developer..." --user-info my_profile.json

# From a job URL
python resume_craft.py --job-url "https://linkedin.com/jobs/view/123" --user-info my_profile.json

# Resume + Cover letter (Premium)
python resume_craft.py --job-desc "..." --user-info my_profile.json --type both

# Full package: resume + cover + LinkedIn + ATS analysis (Premium)
python resume_craft.py --job-desc "..." --user-info my_profile.json --type full

# LinkedIn summary only (Premium)
python resume_craft.py --user-info my_profile.json --type linkedin

# ATS keyword analysis (Premium)
python resume_craft.py --job-desc "..." --user-info my_profile.json --type ats
```

## Output Types

- **resume** - ATS-optimized resume tailored to job description (default, free)
- **cover** - Personalized cover letter (Premium)
- **linkedin** - LinkedIn "About" section (Premium)
- **ats** - ATS keyword match analysis with improvement suggestions (Premium)
- **both** - Resume + cover letter (Premium)
- **full** - All of the above in one file (Premium)

## Activate Premium

```bash
python resume_craft.py --activate YOUR-LICENSE-KEY
```

Get your key at [tirandev.gumroad.com](https://tirandev.gumroad.com)

## License

MIT License - free for personal and commercial use.
Premium features require a license key after the 30-day trial.
