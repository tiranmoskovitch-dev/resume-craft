"""Command-line interface for Resume Craft."""

import argparse
import json
import sys

from resume_craft import __version__
from resume_craft.builder import ResumeBuilder, ResumeData
from resume_craft.licensing import activate_license, get_status


def main():
    parser = argparse.ArgumentParser(
        prog="resume-craft",
        description="Resume Craft - AI-powered resume and cover letter generator",
    )
    parser.add_argument("--version", action="version", version=f"resume-craft {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    # build command
    build_parser = subparsers.add_parser("build", help="Build a resume from JSON data")
    build_parser.add_argument("--input", "-i", required=True, help="JSON file with resume data")
    build_parser.add_argument("--template", default="basic",
                              choices=["basic", "modern", "executive", "creative", "tech"])
    build_parser.add_argument("--role", default=None, help="Target role for tailoring")
    build_parser.add_argument("--jd", default=None, help="Job description file for optimization")
    build_parser.add_argument("--output", "-o", default=None)

    # cover-letter command
    cl_parser = subparsers.add_parser("cover-letter", help="Generate cover letter (Premium)")
    cl_parser.add_argument("--input", "-i", required=True, help="JSON file with resume data")
    cl_parser.add_argument("--company", required=True)
    cl_parser.add_argument("--role", required=True)
    cl_parser.add_argument("--jd", default=None, help="Job description file")
    cl_parser.add_argument("--tone", default="professional")
    cl_parser.add_argument("--output", "-o", default=None)

    # ats-score command
    ats_parser = subparsers.add_parser("ats-score", help="ATS compatibility score (Premium)")
    ats_parser.add_argument("--resume", "-r", required=True, help="Resume text file")
    ats_parser.add_argument("--jd", required=True, help="Job description file")

    # license command
    license_parser = subparsers.add_parser("license", help="Manage license")
    license_parser.add_argument("action", choices=["status", "activate"])
    license_parser.add_argument("--key", default=None)

    args = parser.parse_args()

    if args.command == "build":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        jd = None
        if args.jd:
            with open(args.jd, "r", encoding="utf-8") as f:
                jd = f.read()

        builder = ResumeBuilder()
        try:
            result = builder.build_resume(data, template=args.template,
                                          target_role=args.role, job_description=jd)
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        print(result.content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result.content)
            print(f"\nSaved to: {args.output}")

    elif args.command == "cover-letter":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)

        jd = None
        if args.jd:
            with open(args.jd, "r", encoding="utf-8") as f:
                jd = f.read()

        builder = ResumeBuilder()
        try:
            result = builder.generate_cover_letter(data, args.company, args.role,
                                                   job_description=jd, tone=args.tone)
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        print(result.content)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result.content)

    elif args.command == "ats-score":
        with open(args.resume, "r", encoding="utf-8") as f:
            resume_text = f.read()
        with open(args.jd, "r", encoding="utf-8") as f:
            jd_text = f.read()

        builder = ResumeBuilder()
        try:
            result = builder.score_ats(resume_text, jd_text)
        except PermissionError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        print(result.content)

    elif args.command == "license":
        if args.action == "status":
            print(json.dumps(get_status(), indent=2))
        elif args.action == "activate":
            if not args.key:
                print("Error: --key required", file=sys.stderr)
                sys.exit(1)
            ok, msg = activate_license(args.key)
            print(msg)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
