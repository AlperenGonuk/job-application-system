"""Çekirdek iş kuralları için ağ/model kullanmayan hızlı kontroller."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ilan_sonnet_esle as detailed
import ilan_haiku_on_ele as initial
import ilan_topla
from is_basvuru_arayuzu import cities_for_countries, roles_for_sectors
from cv_uyum_incele import cv_text
from docx import Document
from ilan_tekrar_ayikla import fingerprint
from ilan_topla import matches_preferences, preference_mismatches, preference_sources
from pii_temizle import has_pii, scrub_text
from url_dogrula import URLValidationError, validate_url


class CoreRulesTest(unittest.TestCase):
    def test_candidate_enters_detailed_queue_once_per_mode(self):
        job = {
            "id": "stable-id",
            "company": "Example",
            "title": "Junior Backend Developer",
            "location": "İstanbul",
            "source_url": "https://www.linkedin.com/jobs/view/1",
        }
        key = fingerprint(job)
        original = detailed.all_jobs
        detailed.all_jobs = lambda: [job]
        try:
            review = {key: {"etiket": "aday", "sonnet": "evet"}}
            self.assertEqual(len(detailed.build_queue(review, {}, "esnek")), 1)
            self.assertEqual(len(detailed.build_queue(review, {key: {"mode": "esnek"}}, "esnek")), 0)
            self.assertEqual(len(detailed.build_queue(review, {key: {"mode": "kati"}}, "esnek")), 1)
        finally:
            detailed.all_jobs = original

    def test_sensitive_cv_header_is_not_sent_to_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CV-TR-test.docx"
            document = Document()
            document.add_paragraph("Ada Örnek")
            document.add_paragraph("ada@example.com | +90 555 123 45 67")
            document.add_paragraph("PROJELER")
            document.add_paragraph("Python ile REST API geliştirdim.")
            document.save(path)
            text = cv_text(path)
        self.assertIn("REST API", text)
        self.assertNotIn("Ada Örnek", text)
        self.assertFalse(has_pii(text))

    def test_pii_masking_and_https_guard(self):
        self.assertFalse(has_pii(scrub_text("mail: ada@example.com, +90 555 123 45 67")))
        with self.assertRaises(URLValidationError):
            validate_url("http://localhost:8000/secret")

    def test_role_preference_keeps_relevant_title_variants(self):
        settings = {"target_roles": ["Junior Backend Developer"], "target_cities": ["İstanbul"], "seniority": ["junior"], "remote_ok": True}
        self.assertTrue(matches_preferences({"title": "Junior Python Backend Engineer", "location": "İstanbul"}, settings))
        self.assertFalse(matches_preferences({"title": "Senior Backend Engineer", "location": "İstanbul"}, settings))
        self.assertFalse(matches_preferences({"title": "Junior Backend Engineer", "location": "İzmir"}, settings))

    def test_work_arrangement_filter_respects_remote_choice(self):
        settings = {"target_roles": [], "target_cities": [], "seniority": [], "work_arrangements": ["uzaktan"]}
        self.assertTrue(matches_preferences({"title": "Backend Engineer", "location": "Remote"}, settings))
        self.assertFalse(matches_preferences({"title": "Backend Engineer", "location": "İstanbul"}, settings))

    def test_preference_managed_legacy_source_uses_saved_role_and_location(self):
        config = {"sources": [{"name": "LinkedIn örnek arama", "url": "https://www.linkedin.com/jobs/search?keywords=Junior%20Backend%20Developer"}]}
        settings = {"target_roles": ["Software Engineering Intern", "Data Analyst Intern"], "target_countries": ["Türkiye"], "target_cities": ["Ankara"]}
        generated = preference_sources(config, settings)
        self.assertEqual(len(generated), 2)
        self.assertTrue(all("Ankara%2C%20Turkey" in source["url"] for source in generated))
        self.assertIn("Software%20Engineering%20Intern", generated[0]["url"])

    def test_preference_mismatch_explains_true_conflicts_but_keeps_district(self):
        settings = {"target_roles": ["Software Engineering Intern"], "target_countries": ["Türkiye"], "target_cities": ["Istanbul"], "seniority": [], "work_arrangements": []}
        self.assertEqual(preference_mismatches({"title": "Software Engineer - New Grad", "location": "Sarıyer, Turkey"}, settings), [])
        reasons = preference_mismatches({"title": "Senior Accountant", "location": "Ankara, Turkey"}, settings)
        self.assertIn("role", reasons)
        self.assertIn("city", reasons)

    def test_country_and_city_filters_support_global_options_and_turkey_alias(self):
        turkey = {"target_roles": [], "target_countries": ["Türkiye"], "target_cities": ["All cities"], "seniority": [], "work_arrangements": []}
        self.assertTrue(matches_preferences({"title": "Intern", "location": "Istanbul, Turkey"}, turkey))
        world = {"target_roles": [], "target_countries": ["Worldwide"], "target_cities": ["All cities"], "seniority": [], "work_arrangements": []}
        self.assertTrue(matches_preferences({"title": "Intern", "location": "Tokyo, Japan"}, world))

    def test_sector_and_country_confirmation_sources_are_dependent(self):
        technology_roles = roles_for_sectors({"Technology / SaaS"})
        self.assertIn("Software Engineering Intern", technology_roles)
        self.assertNotIn("Legal Intern", technology_roles)
        turkey_cities = cities_for_countries({"Türkiye"})
        self.assertIn("All cities in Türkiye", turkey_cities)
        self.assertIn("İstanbul" if "İstanbul" in turkey_cities else "Istanbul", turkey_cities)
        self.assertNotIn("Tokyo", turkey_cities)

    def test_public_card_parser_uses_only_card_fields(self):
        page = '''<div class="base-search-card"><h3 class="base-search-card__title">Junior Backend Engineer</h3><h4 class="base-search-card__subtitle"><a>Example Ltd</a></h4><span class="job-search-card__location">Istanbul, Turkey</span><a class="base-card__full-link" href="https://www.linkedin.com/jobs/view/42"></a><time datetime="2026-09-09"></time></li>'''
        with patch.object(ilan_topla, "safe_fetch", return_value=page):
            cards = ilan_topla.linkedin_cards({"name": "Example", "url": "https://www.linkedin.com/jobs/search"})
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["company"], "Example Ltd")
        self.assertEqual(cards[0]["source_url"], "https://www.linkedin.com/jobs/view/42")

    def test_first_run_creates_private_source_config_from_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, template = root / "data" / "ilan-kaynaklari.json", root / "ilan-kaynaklari.ornek.json"
            template.write_text(json.dumps({"max_raw_cards": 5, "sources": []}), encoding="utf-8")
            with patch.object(ilan_topla, "SOURCES_FILE", target), patch.object(ilan_topla, "SOURCES_TEMPLATE", template):
                self.assertEqual(ilan_topla.load_source_config()["max_raw_cards"], 5)
            self.assertTrue(target.exists())

    def test_initial_review_persists_only_valid_mocked_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history, results = root / "history", root / "results"
            history.mkdir(); results.mkdir()
            job = {"id": "stable-job", "company": "Example", "title": "Junior Backend Engineer", "location": "İstanbul", "source_url": "https://www.linkedin.com/jobs/view/42", "published_at": "2026-09-09"}
            (history / "tarama-1.json").write_text(json.dumps({"new_jobs": [job]}), encoding="utf-8")
            state_file = root / "state.json"
            model_output = json.dumps([{"id": "stable-job", "etiket": "aday", "sonnet": "evet"}])
            with patch.object(initial, "HISTORY_DIR", history), patch.object(initial, "RESULT_DIR", results), patch.object(initial, "STATE_FILE", state_file), patch.object(initial, "is_hermes_available", return_value=True), patch.object(initial, "hermes_run", return_value=model_output), patch.object(sys, "argv", ["ilan_haiku_on_ele.py", "--limit", "1"]):
                with redirect_stdout(io.StringIO()):
                    initial.main()
            persisted = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(persisted[fingerprint(job)]["etiket"], "aday")

    def test_candidate_facts_excludes_identity_even_if_user_added_it(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "evidence.json"
            evidence.write_text(json.dumps({"name": "Ada Örnek", "email": "ada@example.com", "projects": ["Python API"]}), encoding="utf-8")
            with patch.object(detailed, "EVIDENCE_FILE", evidence):
                self.assertEqual(detailed.candidate_facts(), {"projects": ["Python API"]})


if __name__ == "__main__":
    unittest.main()
