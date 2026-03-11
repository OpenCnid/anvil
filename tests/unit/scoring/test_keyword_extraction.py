"""Tests for keyword extraction, matching, and job parsing.

Why:
    Keyword matching is the bridge between job descriptions and scoring.
    We test taxonomy matching, alias deduplication, requirement parsing,
    section detection, and the full keyword scoring pipeline.
"""

import pathlib

import pytest

from anvilcv.schema.job_description import JobDescription, JobRequirements
from anvilcv.scoring.ats_scorer import score_extracted_document
from anvilcv.scoring.keyword_extractor import (
    categorize_skills,
    extract_experience_years,
    extract_skills,
)
from anvilcv.scoring.keyword_matcher import (
    check_k01_required_skills,
    check_k02_preferred_skills,
    check_k03_job_title,
    check_k04_industry_terms,
    check_k05_action_verbs,
    run_keyword_checks,
)
from anvilcv.scoring.text_extractor import ExtractedDocument

# --- Keyword Extraction ---


class TestSkillExtraction:
    def test_extracts_known_skills(self):
        text = "Experience with Python, Kubernetes, and Docker"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "Kubernetes" in skills
        assert "Docker" in skills

    def test_alias_matching(self):
        text = "Proficient in golang and k8s"
        skills = extract_skills(text)
        assert "Go" in skills
        assert "Kubernetes" in skills

    def test_deduplication(self):
        text = "Python python3 py — all the same"
        skills = extract_skills(text)
        # Should only have "Python" once
        assert skills.count("Python") == 1

    def test_no_false_positives_for_short_aliases(self):
        # "R" should only match as word boundary, not inside other words
        text = "Are you ready for this role?"
        skills = extract_skills(text)
        # "R" shouldn't match inside "Are" or "ready"
        assert "R" not in skills

    def test_case_insensitive(self):
        text = "PYTHON and KUBERNETES"
        skills = extract_skills(text)
        assert "Python" in skills
        assert "Kubernetes" in skills

    def test_empty_text(self):
        assert extract_skills("") == []

    def test_no_matches(self):
        text = "A nice day for a walk in the park"
        skills = extract_skills(text)
        assert len(skills) == 0


class TestExperienceYears:
    def test_extracts_years(self):
        assert extract_experience_years("5+ years of experience") == 5
        assert extract_experience_years("3 years experience") == 3
        assert extract_experience_years("10+ yrs of experience") == 10

    def test_no_match(self):
        assert extract_experience_years("Great opportunity") is None


class TestSkillCategorization:
    def test_separates_required_and_preferred(self):
        text = (
            "Requirements:\n"
            "- Python\n"
            "- Kubernetes\n"
            "\n"
            "Nice to have:\n"
            "- Terraform\n"
            "- Rust\n"
        )
        required, preferred = categorize_skills(text)
        assert "Python" in required
        assert "Kubernetes" in required
        assert "Terraform" in preferred

    def test_all_required_when_no_sections(self):
        text = "We need Python, Go, and Docker"
        required, preferred = categorize_skills(text)
        assert len(required) > 0
        assert len(preferred) == 0

    def test_deduplication_across_sections(self):
        text = (
            "Requirements: Python\n"
            "Nice to have: Python, Rust\n"
        )
        required, preferred = categorize_skills(text)
        assert "Python" in required
        # Python should NOT be in preferred since it's required
        assert "Python" not in preferred


# --- Keyword Matching Rules ---


class TestK01RequiredSkills:
    def test_all_matched_passes(self):
        check, matched, missing = check_k01_required_skills(
            ["Python", "Go", "Docker"],
            ["Python", "Go"],
        )
        assert check.status == "pass"
        assert len(matched) == 2
        assert len(missing) == 0

    def test_partial_match_warns(self):
        check, matched, missing = check_k01_required_skills(
            ["Python"],
            ["Python", "Go"],
        )
        assert check.status == "warn"
        assert "Go" in missing

    def test_no_match_fails(self):
        check, matched, missing = check_k01_required_skills(
            ["Ruby"],
            ["Python", "Go", "Kubernetes"],
        )
        assert check.status == "fail"
        assert len(missing) == 3

    def test_no_required_skills(self):
        check, _, _ = check_k01_required_skills(["Python"], [])
        assert check.status == "pass"


class TestK02PreferredSkills:
    def test_half_matched_passes(self):
        check = check_k02_preferred_skills(
            ["Python", "Terraform"],
            ["Terraform", "Rust"],
        )
        assert check.status == "pass"  # 1/2 = 50% >= threshold

    def test_no_preferred_passes(self):
        check = check_k02_preferred_skills(["Python"], [])
        assert check.status == "pass"


class TestK03JobTitle:
    def test_exact_title_found(self):
        check = check_k03_job_title(
            "Senior Software Engineer at Acme Corp",
            "Software Engineer",
        )
        assert check.status == "pass"

    def test_title_not_found(self):
        check = check_k03_job_title(
            "Data Analyst at Acme Corp",
            "Software Engineer",
        )
        assert check.status == "fail"

    def test_empty_title(self):
        check = check_k03_job_title("some text", "")
        assert check.status == "pass"


class TestK04IndustryTerms:
    def test_good_overlap(self):
        resume = "Python Docker Kubernetes AWS"
        job = "Looking for Python Docker Kubernetes"
        check = check_k04_industry_terms(resume, job)
        assert check.status == "pass"

    def test_poor_overlap(self):
        resume = "Java Spring Hibernate"
        job = "Python Django FastAPI Kubernetes"
        check = check_k04_industry_terms(resume, job)
        assert check.status in ("warn", "fail")


class TestK05ActionVerbs:
    def test_strong_verbs_pass(self):
        text = (
            "Built scalable systems. Designed API. "
            "Led team of 5. Shipped product. "
            "Deployed to production. Optimized queries."
        )
        check = check_k05_action_verbs(text)
        assert check.status == "pass"

    def test_weak_phrases_warn(self):
        text = (
            "Responsible for building. Helped with deployment. "
            "Built one thing."
        )
        check = check_k05_action_verbs(text)
        assert check.status in ("warn", "fail")

    def test_no_verbs_fail(self):
        check = check_k05_action_verbs("A nice resume about a person.")
        assert check.status == "fail"


class TestKeywordRunner:
    def test_full_pipeline(self):
        doc = ExtractedDocument(
            full_text=(
                "John Doe\njohn@example.com\n"
                "Senior Software Engineer\n"
                "Experience\n"
                "Built scalable Python microservices with Docker\n"
                "Led migration to Kubernetes on AWS\n"
                "Designed RESTful APIs with FastAPI\n"
                "Skills\n"
                "Python, Docker, Kubernetes, AWS, FastAPI\n"
            ),
        )
        checks, section = run_keyword_checks(
            doc,
            job_text="We need Python, Kubernetes, Terraform",
            job_title="Software Engineer",
            required_skills=["Python", "Kubernetes", "Terraform"],
            preferred_skills=["Docker"],
        )
        assert len(checks) == 5
        assert section.score > 0
        assert "Python" in section.matched
        assert "Terraform" in section.missing


# --- Job Parser ---


class TestJobParser:
    def test_parse_text_job(self):
        from anvilcv.tailoring.job_parser import parse_job_from_text

        text = (
            "Senior SRE\nAcme Corp\n\n"
            "Requirements:\n"
            "- 5+ years of experience\n"
            "- Python and Kubernetes\n"
            "\n"
            "Nice to have:\n"
            "- Terraform\n"
        )
        job = parse_job_from_text(text)
        assert job.title == "Senior SRE"
        assert job.company == "Acme Corp"
        assert job.requirements.experience_years == 5
        assert "Python" in job.requirements.required_skills
        assert "Kubernetes" in job.requirements.required_skills

    def test_parse_yaml_job(self, tmp_path: pathlib.Path):
        from anvilcv.tailoring.job_parser import parse_job_from_file

        yaml_file = tmp_path / "job.yaml"
        yaml_file.write_text(
            "job:\n"
            "  title: SRE\n"
            "  company: Acme\n"
            "  requirements:\n"
            "    required_skills: [Python, Kubernetes]\n"
            "    preferred_skills: [Terraform]\n"
            "    experience_years: 5\n"
            "  raw_text: Looking for an SRE with Python\n"
        )
        job = parse_job_from_file(yaml_file)
        assert job.title == "SRE"
        assert job.company == "Acme"
        assert "Python" in job.requirements.required_skills

    def test_parse_missing_file(self, tmp_path: pathlib.Path):
        from anvilcv.tailoring.job_parser import parse_job_from_file

        with pytest.raises(Exception, match="not found"):
            parse_job_from_file(tmp_path / "nope.txt")


# --- End-to-End Score with Job ---


class TestScoreWithJob:
    def test_score_with_job_description(self):
        doc = ExtractedDocument(
            full_text=(
                "John Doe\njohn@example.com | (555) 123-4567\n"
                "Experience\n"
                "Built Python microservices with Docker\n"
                "Led Kubernetes deployments on AWS\n"
                "Education\n"
                "MIT - BS Computer Science\n"
                "Skills\n"
                "Python, Docker, Kubernetes, AWS\n"
            ),
            elements=[],
            page_count=1,
            source_type="html",
        )
        job = JobDescription(
            title="SRE",
            company="Acme",
            requirements=JobRequirements(
                required_skills=["Python", "Kubernetes", "Terraform"],
            ),
            raw_text="We need Python, Kubernetes, Terraform expertise",
        )
        report = score_extracted_document(doc, file_path="test.html", job=job)
        assert report.keyword_match is not None
        assert report.keyword_match.score > 0
        assert len(report.recommendations) > 0  # Terraform missing
        assert report.overall_score > 0
