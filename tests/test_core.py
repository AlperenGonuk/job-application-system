"""Çekirdek iş kuralları için ağ/model kullanmayan hızlı kontroller."""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from docx import Document

from job_app import ai_agents, collect_jobs, migration
from job_app import review_detailed as detailed
from job_app import review_initial as initial
from job_app.collect_jobs import matches_preferences, preference_mismatches, preference_sources
from job_app.cv_match import cv_text
from job_app.dedupe import fingerprint
from job_app.privacy import has_pii, scrub_text
from job_app.process import hidden_process_options
from job_app.ui_app import cities_for_countries, roles_for_sectors
from job_app.url_guard import URLValidationError, validate_url


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
            review = {key: {"label": "candidate", "needs_detail": True}}
            self.assertEqual(len(detailed.build_queue(review, {}, "flexible")), 1)
            self.assertEqual(len(detailed.build_queue(review, {key: {"mode": "flexible"}}, "flexible")), 0)
            self.assertEqual(len(detailed.build_queue(review, {key: {"mode": "strict"}}, "flexible")), 1)
        finally:
            detailed.all_jobs = original

    def test_out_of_scope_job_never_enters_detailed_queue(self):
        job = {"id": "x", "company": "Example", "title": "Senior Chef", "location": "İzmir",
               "source_url": "https://www.linkedin.com/jobs/view/2"}
        key = fingerprint(job)
        original = detailed.all_jobs
        detailed.all_jobs = lambda: [job]
        try:
            review = {key: {"label": "out_of_scope", "needs_detail": False}}
            self.assertEqual(detailed.build_queue(review, {}, "flexible"), [])
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
        settings = {"target_roles": [], "target_cities": [], "seniority": [], "work_arrangements": ["remote"]}
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
        with patch.object(collect_jobs, "safe_fetch", return_value=page):
            cards = collect_jobs.linkedin_cards({"name": "Example", "url": "https://www.linkedin.com/jobs/search"})
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["company"], "Example Ltd")
        self.assertEqual(cards[0]["source_url"], "https://www.linkedin.com/jobs/view/42")

    def test_first_run_creates_private_source_config_from_template(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target, template = root / "data" / "job-sources.json", root / "job-sources.example.json"
            template.write_text(json.dumps({"max_raw_cards": 5, "sources": []}), encoding="utf-8")
            with patch.object(collect_jobs, "SOURCES_FILE", target), patch.object(collect_jobs, "SOURCES_TEMPLATE", template):
                self.assertEqual(collect_jobs.load_source_config()["max_raw_cards"], 5)
            self.assertTrue(target.exists())

    def test_initial_review_persists_only_valid_mocked_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history, results = root / "history", root / "results"
            history.mkdir()
            results.mkdir()
            job = {"id": "stable-job", "company": "Example", "title": "Junior Backend Engineer", "location": "İstanbul", "source_url": "https://www.linkedin.com/jobs/view/42", "published_at": "2026-09-09"}
            (history / "scan-1.json").write_text(json.dumps({"new_jobs": [job]}), encoding="utf-8")
            state_file = root / "state.json"
            model_output = json.dumps([{"id": "stable-job", "label": "candidate", "needs_detail": True}])
            with patch.object(initial, "HISTORY_DIR", history), patch.object(initial, "RESULT_DIR", results), patch.object(initial, "STATE_FILE", state_file), patch.object(initial, "is_agent_available", return_value=True), patch.object(initial, "run_agent", return_value=model_output), patch.object(sys, "argv", ["initial-review", "--limit", "1"]):
                with redirect_stdout(io.StringIO()):
                    initial.main()
            persisted = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(persisted[fingerprint(job)]["label"], "candidate")
            self.assertIs(persisted[fingerprint(job)]["needs_detail"], True)

    def test_initial_review_rejects_out_of_schema_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history, results = root / "history", root / "results"
            history.mkdir()
            results.mkdir()
            job = {"id": "stable-job", "company": "Example", "title": "Junior Backend Engineer", "location": "İstanbul", "source_url": "https://www.linkedin.com/jobs/view/42", "published_at": "2026-09-09"}
            (history / "scan-1.json").write_text(json.dumps({"new_jobs": [job]}), encoding="utf-8")
            state_file = root / "state.json"
            model_output = json.dumps([{"id": "stable-job", "label": "aday", "needs_detail": "evet"}])
            with patch.object(initial, "HISTORY_DIR", history), patch.object(initial, "RESULT_DIR", results), patch.object(initial, "STATE_FILE", state_file), patch.object(initial, "is_agent_available", return_value=True), patch.object(initial, "run_agent", return_value=model_output), patch.object(sys, "argv", ["initial-review", "--limit", "1"]):
                with self.assertRaises(ValueError):
                    initial.main()
            self.assertFalse(state_file.exists())

    def test_candidate_facts_excludes_identity_even_if_user_added_it(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory) / "evidence.json"
            evidence.write_text(json.dumps({"name": "Ada Örnek", "email": "ada@example.com", "projects": ["Python API"]}), encoding="utf-8")
            with patch.object(detailed, "EVIDENCE_FILE", evidence):
                self.assertEqual(detailed.candidate_facts(), {"projects": ["Python API"]})


class AgentRegistryTest(unittest.TestCase):
    def test_argument_agent_puts_prompt_on_command_line(self):
        command, stdin_text = ai_agents.build_command("hermes", "merhaba", task="fast", settings={})
        self.assertIsNone(stdin_text)
        self.assertIn("merhaba", command)
        self.assertIn("claude-haiku-4-5-20251001", command)

    def test_stdin_agent_keeps_prompt_out_of_command_line(self):
        command, stdin_text = ai_agents.build_command("claude", "merhaba", task="deep", settings={})
        self.assertEqual(stdin_text, "merhaba")
        self.assertNotIn("merhaba", command)
        self.assertIn("sonnet", command)

    def test_empty_model_drops_the_model_flag(self):
        command, _ = ai_agents.build_command("agy", "merhaba", task="fast", settings={})
        self.assertNotIn("--model", command)

    def test_user_model_override_wins_over_profile_default(self):
        command, _ = ai_agents.build_command("hermes", "merhaba", task="fast", settings={"ai_model_fast": "kendi-modelim"})
        self.assertIn("kendi-modelim", command)
        self.assertNotIn("claude-haiku-4-5-20251001", command)

    def test_recommended_models_cover_fast_and_deep_for_known_agents(self):
        for agent, models in ai_agents.RECOMMENDED_MODELS.items():
            self.assertIn(agent, ai_agents.AGENT_PROFILES, agent)
            self.assertEqual(set(models), {"fast", "deep"}, agent)
            self.assertTrue(all(name.strip() for name in models.values()), agent)

    def test_unknown_agent_has_no_invented_recommendation(self):
        # Doğrulanmamış model adı uydurulmamalı; boş sözlük arayüzde genel öneriye düşer.
        self.assertEqual(ai_agents.recommended_models("gemini"), {})
        self.assertEqual(ai_agents.recommended_models("cursor-agent"), {})

    def test_list_models_commands_point_at_known_agents(self):
        for agent in ai_agents.LIST_MODELS_COMMAND:
            self.assertIn(agent, ai_agents.AGENT_PROFILES, agent)

    def test_custom_command_substitutes_prompt_placeholder(self):
        settings = {"ai_agent": "custom", "ai_custom_command": "myagent run --text {prompt}"}
        command, stdin_text = ai_agents.build_command("custom", "merhaba", task="fast", settings=settings)
        self.assertEqual(command, ["myagent", "run", "--text", "merhaba"])
        self.assertIsNone(stdin_text)

    def test_custom_command_without_placeholder_uses_stdin(self):
        settings = {"ai_agent": "custom", "ai_custom_command": "myagent run"}
        command, stdin_text = ai_agents.build_command("custom", "merhaba", task="fast", settings=settings)
        self.assertEqual(command, ["myagent", "run"])
        self.assertEqual(stdin_text, "merhaba")

    def test_explicit_but_missing_agent_does_not_silently_fall_back(self):
        with patch.object(ai_agents, "is_installed", return_value=False):
            self.assertIsNone(ai_agents.resolve_agent({"ai_agent": "codex"}))

    def test_auto_choice_picks_first_installed_agent(self):
        with patch.object(ai_agents, "available_agents", return_value=["agy", "pi"]):
            self.assertEqual(ai_agents.resolve_agent({"ai_agent": "auto"}), "agy")


class PrivacyTest(unittest.TestCase):
    def test_public_job_url_survives_scrubbing(self):
        # LinkedIn ilan numarası 10 hanelidir; telefon sanılıp maskelenirse
        # modelin döndürdüğü id hiçbir ilanla eşleşmez.
        url = "https://tr.linkedin.com/jobs/view/game-developer-at-loop-games-4452573928"
        cleaned = scrub_text(f"{url} iletisim: ada@example.com +90 555 123 45 67")
        self.assertIn(url, cleaned)
        self.assertIn("TELEFON GİZLİ", cleaned)
        self.assertIn("E-POSTA GİZLİ", cleaned)
        self.assertFalse(has_pii(cleaned))


class HiddenProcessTest(unittest.TestCase):
    def test_windows_gets_no_console_window(self):
        options = hidden_process_options()
        if sys.platform.startswith("win"):
            self.assertEqual(options["creationflags"], subprocess.CREATE_NO_WINDOW)
            self.assertIn("startupinfo", options)
        else:
            self.assertEqual(options, {})


class MigrationTest(unittest.TestCase):
    def test_turkish_keys_and_values_become_english(self):
        old = {
            "url:x": {"etiket": "aday", "sonnet": "evet"},
            "url:y": {"karar": "başvurma", "uyum_puani": 40, "cv_tipi": "genel", "cv_dili": "TR",
                      "gerekce": "kısa not", "mode": "cok_esnek"},
        }
        new = migration.translate(old)
        self.assertEqual(new["url:x"], {"label": "candidate", "needs_detail": True})
        self.assertEqual(new["url:y"]["decision"], "skip")
        self.assertEqual(new["url:y"]["match_score"], 40)
        self.assertEqual(new["url:y"]["cv_focus"], "general")
        self.assertEqual(new["url:y"]["cv_language"], "TR")
        self.assertEqual(new["url:y"]["reason"], "kısa not")
        self.assertEqual(new["url:y"]["mode"], "very_flexible")

    def test_free_text_is_not_translated_by_accident(self):
        # "başvur" serbest metin alanında geçse bile yalnız karar alanı çevrilir.
        translated = migration.translate({"gerekce": "başvur", "karar": "başvur"})
        self.assertEqual(translated["reason"], "başvur")
        self.assertEqual(translated["decision"], "apply")

    def test_work_arrangements_list_is_translated(self):
        translated = migration.translate({"work_arrangements": ["ofis", "uzaktan"], "detailed_review_mode": "esnek"})
        self.assertEqual(translated["work_arrangements"], ["onsite", "remote"])
        self.assertEqual(translated["detailed_review_mode"], "flexible")

    def test_profile_cv_variant_is_renamed(self):
        profile = {"cv_profiles": {"TR": {"genel": {"headline": "x"}, "python_backend": {"headline": "y"}}}}
        renamed = migration.translate_profile(profile)
        self.assertIn("general", renamed["cv_profiles"]["TR"])
        self.assertIn("python_backend", renamed["cv_profiles"]["TR"])
        self.assertNotIn("genel", renamed["cv_profiles"]["TR"])


if __name__ == "__main__":
    unittest.main()
