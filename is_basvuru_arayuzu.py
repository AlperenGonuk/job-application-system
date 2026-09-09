"""İş Başvuru Sistemi için yerel, Türkçe/İngilizce masaüstü arayüzü."""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import scrolledtext

from cv_ats import get_or_compute
from ilan_tekrar_ayikla import fingerprint
from ayarlar import load_settings, save_settings
from depolama import data_dir, data_file, load_json, write_json
from ilan_haiku_on_ele import is_hermes_available
from ilan_sonnet_esle import is_locked as is_detailed_locked

ROOT = Path(__file__).resolve().parent
HISTORY_DIR = data_dir("tarama-gecmisi")
HAIKU_STATE = data_file("ilan-on-eleme-durumu.json")
MATCH_STATE = data_file("ilan-esleme-durumu.json")
DECISIONS_FILE = data_file("arayuz-cv-secimleri.json")
ATS_SCORES_FILE = data_file("cv-ats-puanlari.json")

TEXT = {
    "TR": {
        "title": "İş Başvuru Sistemi", "language": "Arayüz dili:", "scan_date": "Tarama tarihi:",
        "today": "Bugün", "yesterday": "Dün", "all": "Tümü", "custom_date": "Tarih seç…",
        "status": "Ön eleme:", "detail": "Detaylı eleme:", "refresh": "Yenile", "collect": "Yeni ilanları topla",
        "date": "Tarama", "company": "Şirket", "role": "Pozisyon", "location": "Konum", "cv": "CV",
        "selected": "Seçilen ilan", "open_job": "İlan bağlantısını aç", "cv_language": "CV dili:",
        "save_cv": "CV seçimini kaydet", "open_cv": "Seçili CV'yi görüntüle", "preselect": "Ön eleme",
        "detailed": "Detaylı eleme", "create_cv": "Bu ilan için CV oluştur", "inspect_cv": "Mevcut CV'lerle uyumu incele",
        "not_selected": "Henüz seçilmedi", "not_processed": "Henüz ön elemede değil", "not_reviewed": "Henüz detaylı elemede değil",
        "candidate": "Aday", "manual": "Manuel incele", "outside": "Kapsam dışı", "apply": "Başvur", "do_not_apply": "Başvurma",
        "choose_job": "İlan seçin", "choose_job_text": "Önce listeden bir ilan seçin.", "saved": "Kaydedildi", "saved_text": "CV seçimi yerel takip dosyasına kaydedildi.",
        "collect_confirm": "Kaynaklar taranacak ve yalnız yeni ilanlar kayıt defterine eklenecek. Başlatılsın mı?", "collect_done": "Tarama tamamlandı", "collect_error": "Tarama hatası",
        "scan_summary": "İndirilen kart: {downloaded}\nTercihlerle uyumlu: {matched}\nTercihler nedeniyle elenen: {filtered}\nYeni ilan: {new}\nDaha önce görülen: {seen}",
        "scan_no_cards": "Kaynaklardan ilan kartı alınamadı. Bu bir ağ/kaynak değişikliği olabilir; aşağıdaki kaynak durumlarını kontrol edin.",
        "scan_no_match": "İlanlar indirildi ancak mevcut iş tercihlerinle eşleşen ilan bulunmadı. İş tercihlerini veya ilan kaynaklarını gözden geçirebilirsin.",
        "scan_failures": "Kaynak sorunları:\n{failures}",
        "scan_sources": "Kaynak özeti:\n{sources}",
        "mode_title": "Detaylı eleme modu", "mode_prompt": "Değerlendirme modunu seç", "mode_info": "Katı: temel gereksinim uyumu yüksek olmalı.\nEsnek: junior ilandaki şişirilmiş deneyim beklentileri tek başına red değildir.\nÇok esnek: ilan açıkça junior/new grad ise ilgili alandaki aday için daha toleranslıdır; gerçek olmayan bilgi eklemez.",
        "strict": "Katı", "flexible": "Esnek", "very_flexible": "Çok esnek", "cancel": "Vazgeç", "start": "Değerlendirmeyi başlat",
        "create_confirm": "Seçilen ilan için yalnız doğrulanmış kanıtları kullanan yeni bir DOCX oluşturulacak. Devam edilsin mi?", "match_required": "Detaylı eleme gerekli", "match_required_text": "Önce bu ilanı detaylı elemeden geçirin.",
        "open_error": "CV açılamadı", "cv_missing": "CV bulunamadı", "cv_missing_text": "Bu CV dosyası bulunamadı:", "choose_cv": "CV seçin", "choose_cv_text": "Önce bir CV seçin veya işe özel CV oluşturun.",
        "local_ats": "Yerel ATS tahmini", "ats_wait": "Yerel ATS tahmini: hesaplanıyor (model/token kullanılmaz)…", "ats_none": "Yerel ATS tahmini: henüz hesaplanmadı.",
        "settings": "Ayarlar", "initial_limit": "Her çalıştırmada ön eleme ilan sayısı:", "default_mode": "Varsayılan detaylı eleme modu:", "roles": "Hedef roller:", "sectors": "Hedef sektörler:", "countries": "Hedef ülkeler:", "cities": "Hedef şehirler:", "seniority": "Tercih edilen kıdem:", "search": "Yazarak ara ve listeden seç:", "other": "Ek özel seçenekler (virgülle ayır):", "work_type": "Tercih edilen çalışma biçimi:", "office": "Ofis", "hybrid": "Hibrit", "remote": "Uzaktan", "save": "Kaydet", "settings_saved": "Ayarlar bu cihazda yerel olarak kaydedildi.",
        "ai_tooltip": "Bu işlem yapay zekâ kullanır. Bağlı model hesabının kotası ve kullanımı etkilenebilir.",
        "hermes_missing": "Hermes CLI bulunamadı",
        "hermes_missing_text": "Yapay zeka işlemlerini çalıştırabilmek için sisteminizde 'hermes' CLI aracının kurulu ve PATH'te tanımlı olması gerekir.\n\nYapay zeka olmadan ilan toplama, filtreleme, yerel ATS puanı ve CV yönetimini kullanmaya devam edebilirsiniz.",
        "ai_busy": "Yapay zeka işlemi devam ediyor", "ai_busy_text": "Başka bir yapay zeka işlemi zaten çalışıyor. Lütfen mevcut işlem bitene kadar bekleyin.",
        "help": "Nasıl kullanılır?", "preferences": "İş tercihleri", "confirm_selection": "Seçimi onayla", "confirm_hint": "Seçtiklerini onayladığında hemen kaydedilir. Sektör onayı rol, ülke onayı şehir önerilerini yeniler.", "selection_saved": "Kaydedildi", "selection_save_error": "Seçim kaydedilemedi.", "use_without_ai": "Yapay zeka olmadan kullan", "copy_skill": "Yapay zeka başlangıç yönergesini kopyala", "copy_skill_path": "Yönerge dosyası yolunu kopyala", "skill_copied": "Yönerge panoya kopyalandı. Tercih ettiğin yapay zeka modeline gönderip soruları yanıtlayabilirsin.", "path_copied": "Yerel yönerge dosyası yolu panoya kopyalandı.", "copy_skill_tip": "Bu metni bir yapay zekaya verirsen sana gerekli soruları sırayla sorar ve yerel profil dosyalarını hazırlamana yardım eder.", "copy_path_tip": "Bu yol yalnız bilgisayarındaki dosyalara erişebilen yerel yapay zekalar içindir. Modelden başlamadan önce dosyayı okumasını iste.",
    },
    "EN": {
        "title": "Job Application System", "language": "Interface language:", "scan_date": "Scan date:",
        "today": "Today", "yesterday": "Yesterday", "all": "All", "custom_date": "Choose date…",
        "status": "Initial review:", "detail": "Detailed review:", "refresh": "Refresh", "collect": "Collect new jobs",
        "date": "Scan", "company": "Company", "role": "Role", "location": "Location", "cv": "CV",
        "selected": "Selected job", "open_job": "Open job link", "cv_language": "CV language:",
        "save_cv": "Save CV selection", "open_cv": "View selected CV", "preselect": "Initial review",
        "detailed": "Detailed review", "create_cv": "Create CV for this job", "inspect_cv": "Compare current CVs",
        "not_selected": "Not selected yet", "not_processed": "Not reviewed yet", "not_reviewed": "Not reviewed in detail yet",
        "candidate": "Candidate", "manual": "Manual review", "outside": "Out of scope", "apply": "Apply", "do_not_apply": "Do not apply",
        "choose_job": "Select a job", "choose_job_text": "Select a job from the list first.", "saved": "Saved", "saved_text": "The CV selection was saved locally.",
        "collect_confirm": "Sources will be scanned and only new jobs will be added to the local registry. Start now?", "collect_done": "Scan complete", "collect_error": "Scan error",
        "scan_summary": "Downloaded cards: {downloaded}\nMatching your preferences: {matched}\nFiltered by preferences: {filtered}\nNew jobs: {new}\nPreviously seen: {seen}",
        "scan_no_cards": "No job cards were received from the sources. This may be a network or source-layout change; check the source status below.",
        "scan_no_match": "Jobs were downloaded, but none matched your current preferences. Review your job preferences or job sources.",
        "scan_failures": "Source issues:\n{failures}",
        "scan_sources": "Source summary:\n{sources}",
        "mode_title": "Detailed review mode", "mode_prompt": "Choose an evaluation mode", "mode_info": "Strict: core requirements need strong evidence.\nFlexible: inflated experience requirements in junior roles are not an automatic rejection.\nVery flexible: is more tolerant for clearly junior/new-grad roles, but never invents experience.",
        "strict": "Strict", "flexible": "Flexible", "very_flexible": "Very flexible", "cancel": "Cancel", "start": "Start review",
        "create_confirm": "A new DOCX using only verified evidence will be created for this job. Continue?", "match_required": "Detailed review required", "match_required_text": "Run detailed review for this job first.",
        "open_error": "Could not open CV", "cv_missing": "CV not found", "cv_missing_text": "This CV file could not be found:", "choose_cv": "Choose a CV", "choose_cv_text": "Choose a CV or create a job-specific one first.",
        "local_ats": "Local ATS estimate", "ats_wait": "Local ATS estimate: calculating (no model/tokens used)…", "ats_none": "Local ATS estimate: not calculated yet.",
        "settings": "Settings", "initial_limit": "Jobs per initial-review run:", "default_mode": "Default detailed-review mode:", "roles": "Target roles:", "sectors": "Target sectors:", "countries": "Target countries:", "cities": "Target cities:", "seniority": "Preferred seniority:", "search": "Type to search and select from the list:", "other": "Other custom options (comma-separated):", "work_type": "Preferred work arrangements:", "office": "On-site", "hybrid": "Hybrid", "remote": "Remote", "save": "Save", "settings_saved": "Settings were saved locally on this device.",
        "ai_tooltip": "This action uses AI. It may affect usage and limits on the connected model account.",
        "hermes_missing": "Hermes CLI not found",
        "hermes_missing_text": "To run AI evaluation features, the 'hermes' CLI tool must be installed and available in your PATH.\n\nYou can still use job collection, filtering, local ATS scoring, and CV tracking without AI.",
        "ai_busy": "AI operation in progress", "ai_busy_text": "Another AI operation is already running. Please wait until it finishes.",
        "help": "How to use", "preferences": "Job preferences", "confirm_selection": "Confirm selection", "confirm_hint": "Confirming saves this selection immediately. Sector confirmation refreshes role suggestions; country confirmation refreshes city suggestions.", "selection_saved": "Saved", "selection_save_error": "The selection could not be saved.", "use_without_ai": "Continue without AI", "copy_skill": "Copy AI onboarding instruction", "copy_skill_path": "Copy instruction file path", "skill_copied": "The instruction was copied. Send it to your preferred AI model and answer its questions.", "path_copied": "The local instruction-file path was copied.", "copy_skill_tip": "Give this text to an AI and it will ask for the required details in order and help prepare local profile files.", "copy_path_tip": "This path is for local AIs that can read files on your computer. Ask the model to read it before starting.",
    },
}
STATUS = {"candidate": "aday", "manual": "belirsiz", "outside": "kapsam_dışı"}
DECISIONS = {"apply": "başvur", "manual": "manuel_incele", "do_not_apply": "başvurma"}
MODE_CODES = {"strict": "kati", "flexible": "esnek", "very_flexible": "cok_esnek"}
PREFERENCE_OPTIONS = {
    "target_roles": [
        "Software Engineering Intern", "Data Analyst Intern", "Data Science / Machine Learning Intern", "QA / Test Intern",
        "DevOps / Cloud Intern", "Cybersecurity Intern", "Product Management Intern", "UI/UX Design Intern",
        "Marketing Intern", "Sales Intern", "Finance / Accounting Intern", "Human Resources Intern", "Operations Intern",
        "Business Development Intern", "Legal Intern", "Research Intern", "Healthcare Intern", "Engineering Intern",
        "Junior Software Developer", "Junior Data Analyst", "Junior Data Engineer", "Junior QA Engineer", "Junior DevOps Engineer",
        "Junior Product Manager", "Junior UX/UI Designer", "Junior Marketing Specialist", "Junior Financial Analyst",
        "Junior Accountant", "Junior HR Specialist", "Junior Operations Specialist", "Junior Sales Representative",
        "Junior Business Analyst", "Customer Support Specialist", "Supply Chain Analyst", "Project Coordinator",
    ],
    "target_sectors": [
        "Technology / SaaS", "Artificial Intelligence", "Fintech", "Banking", "Insurance", "E-commerce / Retail",
        "Logistics / Supply Chain", "Manufacturing", "Automotive", "Energy", "Healthcare", "Pharmaceuticals / Biotechnology",
        "Education / EdTech", "Telecommunications", "Media / Entertainment", "Gaming", "Travel / Hospitality", "Real Estate",
        "Consulting", "Government / Public Sector", "Nonprofit", "Legal Services", "Agriculture", "Construction",
        "Aerospace / Defense", "Food & Beverage", "Fashion / Luxury", "Sports", "Climate / Sustainability", "Research",
    ],
    "target_countries": [
        "Worldwide", "All countries", "Türkiye", "United States", "United Kingdom", "Germany", "Netherlands", "Canada",
        "Australia", "Ireland", "France", "Switzerland", "Sweden", "Norway", "Denmark", "Finland", "Austria", "Belgium",
        "Spain", "Italy", "Portugal", "Poland", "Czechia", "Romania", "Greece", "United Arab Emirates", "Saudi Arabia",
        "Qatar", "Israel", "India", "Pakistan", "China", "Japan", "South Korea", "Singapore", "Malaysia", "Indonesia",
        "Thailand", "Vietnam", "Philippines", "Brazil", "Mexico", "Argentina", "Chile", "Colombia", "South Africa", "Egypt",
        "Nigeria", "Kenya", "New Zealand", "Ukraine",
    ],
    "target_cities": [
        "All cities", "All cities in Türkiye", "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya", "Kocaeli", "Eskişehir",
        "New York", "San Francisco", "Seattle", "Boston", "Austin", "Chicago", "London", "Manchester", "Dublin", "Berlin",
        "Munich", "Hamburg", "Amsterdam", "Paris", "Zurich", "Geneva", "Stockholm", "Copenhagen", "Helsinki", "Vienna",
        "Brussels", "Madrid", "Barcelona", "Milan", "Rome", "Lisbon", "Warsaw", "Prague", "Bucharest", "Dubai", "Abu Dhabi",
        "Riyadh", "Doha", "Tel Aviv", "Mumbai", "Bangalore", "Delhi", "Beijing", "Shanghai", "Tokyo", "Osaka", "Seoul",
        "Singapore", "Kuala Lumpur", "Jakarta", "Bangkok", "Ho Chi Minh City", "Manila", "Sydney", "Melbourne", "Auckland",
        "São Paulo", "Mexico City", "Buenos Aires", "Santiago", "Bogotá", "Cape Town", "Johannesburg", "Cairo", "Lagos", "Nairobi",
    ],
    "seniority": ["Intern", "Part-time Intern", "Apprentice", "Graduate", "Entry Level", "Junior", "Mid Level", "Senior"],
}
GENERAL_ROLES = {"Research Intern", "Business Development Intern", "Operations Intern", "Project Coordinator", "Customer Support Specialist"}
SECTOR_ROLE_OPTIONS = {
    "Technology / SaaS": {"Software Engineering Intern", "Data Analyst Intern", "QA / Test Intern", "DevOps / Cloud Intern", "Product Management Intern", "Junior Software Developer", "Junior Data Analyst", "Junior QA Engineer", "Junior DevOps Engineer", "Junior Product Manager", "Customer Support Specialist"},
    "Artificial Intelligence": {"Data Science / Machine Learning Intern", "Data Analyst Intern", "Software Engineering Intern", "Research Intern", "Junior Data Analyst", "Junior Data Engineer", "Junior Software Developer"},
    "Fintech": {"Finance / Accounting Intern", "Data Analyst Intern", "Software Engineering Intern", "Junior Financial Analyst", "Junior Data Analyst", "Junior Software Developer", "Junior Business Analyst"},
    "Banking": {"Finance / Accounting Intern", "Data Analyst Intern", "Operations Intern", "Junior Financial Analyst", "Junior Accountant", "Junior Operations Specialist", "Customer Support Specialist"},
    "Insurance": {"Finance / Accounting Intern", "Data Analyst Intern", "Sales Intern", "Junior Financial Analyst", "Junior Sales Representative", "Junior Operations Specialist"},
    "E-commerce / Retail": {"Marketing Intern", "Sales Intern", "Data Analyst Intern", "Operations Intern", "Junior Marketing Specialist", "Junior Data Analyst", "Junior Sales Representative", "Supply Chain Analyst"},
    "Logistics / Supply Chain": {"Operations Intern", "Data Analyst Intern", "Engineering Intern", "Junior Operations Specialist", "Supply Chain Analyst", "Junior Data Analyst"},
    "Manufacturing": {"Engineering Intern", "Operations Intern", "Finance / Accounting Intern", "Junior Operations Specialist", "Junior Accountant", "Supply Chain Analyst"},
    "Automotive": {"Engineering Intern", "Software Engineering Intern", "Operations Intern", "Junior Software Developer", "Junior Operations Specialist", "Supply Chain Analyst"},
    "Energy": {"Engineering Intern", "Data Analyst Intern", "Operations Intern", "Junior Data Analyst", "Junior Operations Specialist"},
    "Healthcare": {"Healthcare Intern", "Data Analyst Intern", "Marketing Intern", "Operations Intern", "Junior Data Analyst", "Junior Operations Specialist"},
    "Pharmaceuticals / Biotechnology": {"Healthcare Intern", "Research Intern", "Data Analyst Intern", "Junior Data Analyst"},
    "Education / EdTech": {"Marketing Intern", "Product Management Intern", "Software Engineering Intern", "Junior Marketing Specialist", "Junior Product Manager", "Junior Software Developer"},
    "Telecommunications": {"Engineering Intern", "Software Engineering Intern", "Data Analyst Intern", "Junior Software Developer", "Junior Data Analyst"},
    "Media / Entertainment": {"Marketing Intern", "UI/UX Design Intern", "Sales Intern", "Junior Marketing Specialist", "Junior UX/UI Designer"},
    "Gaming": {"Software Engineering Intern", "UI/UX Design Intern", "Data Analyst Intern", "Junior Software Developer", "Junior UX/UI Designer"},
    "Travel / Hospitality": {"Marketing Intern", "Sales Intern", "Operations Intern", "Customer Support Specialist", "Junior Operations Specialist"},
    "Real Estate": {"Sales Intern", "Marketing Intern", "Finance / Accounting Intern", "Junior Sales Representative", "Junior Financial Analyst"},
    "Consulting": {"Business Development Intern", "Data Analyst Intern", "Finance / Accounting Intern", "Junior Business Analyst", "Junior Financial Analyst", "Project Coordinator"},
    "Government / Public Sector": {"Legal Intern", "Research Intern", "Operations Intern", "Project Coordinator"},
    "Nonprofit": {"Marketing Intern", "Operations Intern", "Research Intern", "Project Coordinator"},
    "Legal Services": {"Legal Intern", "Research Intern", "Project Coordinator"},
    "Agriculture": {"Engineering Intern", "Operations Intern", "Data Analyst Intern", "Supply Chain Analyst"},
    "Construction": {"Engineering Intern", "Operations Intern", "Project Coordinator", "Supply Chain Analyst"},
    "Aerospace / Defense": {"Engineering Intern", "Software Engineering Intern", "Cybersecurity Intern", "Junior Software Developer"},
    "Food & Beverage": {"Marketing Intern", "Operations Intern", "Finance / Accounting Intern", "Supply Chain Analyst"},
    "Fashion / Luxury": {"Marketing Intern", "Sales Intern", "UI/UX Design Intern", "Junior Marketing Specialist", "Junior Sales Representative"},
    "Sports": {"Marketing Intern", "Sales Intern", "Operations Intern", "Junior Marketing Specialist"},
    "Climate / Sustainability": {"Engineering Intern", "Research Intern", "Data Analyst Intern", "Junior Data Analyst"},
    "Research": {"Research Intern", "Data Science / Machine Learning Intern", "Data Analyst Intern", "Junior Data Analyst"},
}
COUNTRY_CITY_OPTIONS = {
    "Türkiye": [
        "All cities in Türkiye", "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın", "Balıkesir",
        "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır", "Düzce",
        "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun", "Gümüşhane", "Hakkâri", "Hatay", "Iğdır", "Isparta",
        "Istanbul", "Izmir", "Kahramanmaraş", "Karabük", "Karaman", "Kars", "Kastamonu", "Kayseri", "Kilis", "Kırıkkale", "Kırklareli", "Kırşehir",
        "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa", "Mardin", "Mersin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Osmaniye", "Rize",
        "Sakarya", "Samsun", "Siirt", "Sinop", "Sivas", "Şanlıurfa", "Şırnak", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Uşak", "Van", "Yalova",
        "Yozgat", "Zonguldak",
    ],
    "United States": ["New York", "San Francisco", "Seattle", "Boston", "Austin", "Chicago"],
    "United Kingdom": ["London", "Manchester"], "Germany": ["Berlin", "Munich", "Hamburg"], "Netherlands": ["Amsterdam"],
    "Canada": ["Toronto", "Vancouver", "Montreal"], "Australia": ["Sydney", "Melbourne"], "Ireland": ["Dublin"],
    "France": ["Paris"], "Switzerland": ["Zurich", "Geneva"], "Sweden": ["Stockholm"], "Norway": ["Oslo"],
    "Denmark": ["Copenhagen"], "Finland": ["Helsinki"], "Austria": ["Vienna"], "Belgium": ["Brussels"],
    "Spain": ["Madrid", "Barcelona"], "Italy": ["Milan", "Rome"], "Portugal": ["Lisbon"], "Poland": ["Warsaw"],
    "Czechia": ["Prague"], "Romania": ["Bucharest"], "United Arab Emirates": ["Dubai", "Abu Dhabi"],
    "Saudi Arabia": ["Riyadh"], "Qatar": ["Doha"], "Israel": ["Tel Aviv"], "India": ["Mumbai", "Bangalore", "Delhi"],
    "China": ["Beijing", "Shanghai"], "Japan": ["Tokyo", "Osaka"], "South Korea": ["Seoul"], "Singapore": ["Singapore"],
    "Malaysia": ["Kuala Lumpur"], "Indonesia": ["Jakarta"], "Thailand": ["Bangkok"], "Vietnam": ["Ho Chi Minh City"],
    "Philippines": ["Manila"], "Brazil": ["São Paulo"], "Mexico": ["Mexico City"], "Argentina": ["Buenos Aires"],
    "Chile": ["Santiago"], "Colombia": ["Bogotá"], "South Africa": ["Cape Town", "Johannesburg"], "Egypt": ["Cairo"],
    "Nigeria": ["Lagos"], "Kenya": ["Nairobi"], "New Zealand": ["Auckland"], "Ukraine": ["Kyiv"],
}


def roles_for_sectors(sectors: set[str]) -> list[str]:
    """Seçili sektörlere ait, önceden tanımlı rolleri döndürür."""
    if not sectors:
        return list(PREFERENCE_OPTIONS["target_roles"])
    allowed = set(GENERAL_ROLES)
    for sector in sectors:
        allowed.update(SECTOR_ROLE_OPTIONS.get(sector, set()))
    return [role for role in PREFERENCE_OPTIONS["target_roles"] if role in allowed]


def cities_for_countries(countries: set[str]) -> list[str]:
    """Seçili ülkelere göre şehir seçeneklerini üretir; genel seçenekte tam listeyi açar."""
    if not countries or {"Worldwide", "All countries"} & countries:
        return list(PREFERENCE_OPTIONS["target_cities"])
    cities = ["All cities"]
    for country in sorted(countries):
        cities.extend(COUNTRY_CITY_OPTIONS.get(country, [f"All cities in {country}"]))
    return list(dict.fromkeys(cities))


def cv_options(language: str) -> tuple[str, ...]:
    directory = data_dir("CV-Sürümleri")
    names = sorted(path.stem for path in directory.glob(f"CV-{language}-*.docx")) if directory.exists() else []
    return ("", *names)


class Tooltip:
    def __init__(self, widget, text_provider):
        self.widget, self.text_provider, self.window = widget, text_provider, None
        widget.bind("<Enter>", self.show, add=True)
        widget.bind("<Leave>", self.hide, add=True)

    def show(self, _event=None):
        if self.window:
            return
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{self.widget.winfo_rootx() + 8}+{self.widget.winfo_rooty() + self.widget.winfo_height() + 6}")
        tk.Label(self.window, text=self.text_provider(), justify="left", bg="#26394a", fg="white", padx=9, pady=6, wraplength=330).pack()

    def hide(self, _event=None):
        if self.window:
            self.window.destroy()
            self.window = None


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.app_language = tk.StringVar(value="TR")
        self.jobs, self.filtered, self.decisions, self.matches, self.ats_scores = [], [], {}, {}, {}
        self.selected_key = None
        self.date_filter = tk.StringVar(value="today")
        self.custom_date = tk.StringVar()
        self.status_filter = tk.StringVar(value="all")
        self.detail_filter = tk.StringVar(value="all")
        self.cv_language = tk.StringVar(value="TR")
        self.cv_choice = tk.StringVar()
        self.summary = tk.StringVar()
        self.title("İş Başvuru Sistemi")
        self.geometry("1180x720")
        self.minsize(960, 600)
        self.configure(bg="#f4f7fb")
        self._ai_running = False
        self._build()
        self.reload_data()
        self.after(250, self.show_first_run_help)

    def t(self, key: str) -> str:
        return TEXT[self.app_language.get()][key]

    def label_for_status(self, value: str) -> str:
        return next((self.t(key) for key, code in STATUS.items() if code == value), self.t("not_processed"))

    def label_for_decision(self, value: str) -> str:
        return next((self.t(key) for key, code in DECISIONS.items() if code == value), self.t("not_reviewed"))

    def _build(self) -> None:
        header = tk.Frame(self, bg="#17324d", padx=24, pady=17)
        header.pack(fill="x")
        tk.Label(header, text=self.t("title"), font=("Segoe UI", 19, "bold"), fg="white", bg="#17324d").pack(anchor="w")
        tk.Label(header, textvariable=self.summary, font=("Segoe UI", 10), fg="#dce7f0", bg="#17324d").pack(anchor="w", pady=(4, 0))
        controls = tk.Frame(header, bg="#17324d")
        controls.pack(side="right", padx=(0, 18), anchor="ne")
        tk.Label(controls, text=self.t("language"), fg="#dce7f0", bg="#17324d").pack(side="left", padx=(0, 7))
        language = ttk.Combobox(controls, textvariable=self.app_language, values=("TR", "EN"), state="readonly", width=5)
        language.pack(side="left")
        language.bind("<<ComboboxSelected>>", self.change_interface_language)
        ttk.Button(controls, text="⚙", width=3, command=self.open_settings).pack(side="left", padx=(7, 0))
        ttk.Button(controls, text="?", width=3, command=self.show_help).pack(side="left", padx=(5, 0))
        toolbar = tk.Frame(self, bg="#f4f7fb", padx=20, pady=14)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text=self.t("scan_date"), bg="#f4f7fb", font=("Segoe UI", 10, "bold")).pack(side="left")
        for key in ("today", "yesterday", "all"):
            ttk.Radiobutton(toolbar, text=self.t(key), value=key, variable=self.date_filter, command=self.apply_filters).pack(side="left", padx=8)
        self.date_picker = ttk.Combobox(toolbar, textvariable=self.custom_date, state="readonly", width=15)
        self.date_picker.pack(side="left", padx=(4, 0)); self.date_picker.bind("<<ComboboxSelected>>", self.pick_custom_date)
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=14)
        self.make_filter(toolbar, "status", ("all", "candidate", "manual", "outside", "not_processed"), self.status_filter)
        self.make_filter(toolbar, "detail", ("all", "apply", "manual", "do_not_apply", "not_reviewed"), self.detail_filter)
        ttk.Button(toolbar, text=self.t("refresh"), command=self.reload_data).pack(side="right")
        ttk.Button(toolbar, text=self.t("collect"), command=self.collect_jobs).pack(side="right", padx=8)
        middle = tk.Frame(self, bg="#f4f7fb", padx=20); middle.pack(fill="both", expand=True)
        columns = ("date", "company", "title", "location", "status", "detail", "cv")
        self.tree = ttk.Treeview(middle, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, (92, 155, 275, 135, 130, 140, 165)):
            self.tree.heading(col, text=self.t({"title": "role"}.get(col, col)))
            self.tree.column(col, width=width, anchor="w")
        scroll = ttk.Scrollbar(middle, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y"); self.tree.bind("<<TreeviewSelect>>", self.on_select)
        details = tk.LabelFrame(self, text=self.t("selected"), bg="#f4f7fb", padx=20, pady=12, font=("Segoe UI", 10, "bold")); details.pack(fill="x", padx=20, pady=(12, 18))
        self.detail_text = tk.StringVar(value=self.t("choose_job_text")); tk.Label(details, textvariable=self.detail_text, bg="#f4f7fb", justify="left", anchor="w", font=("Segoe UI", 10)).grid(row=0, column=0, columnspan=7, sticky="w")
        ttk.Button(details, text=self.t("open_job"), command=self.open_link).grid(row=1, column=0, pady=(11, 0), sticky="w")
        tk.Label(details, text=self.t("cv_language"), bg="#f4f7fb").grid(row=1, column=1, padx=(24, 8), pady=(11, 0))
        language = ttk.Combobox(details, textvariable=self.cv_language, values=("TR", "EN"), state="readonly", width=5); language.grid(row=1, column=2, pady=(11, 0)); language.bind("<<ComboboxSelected>>", self.cv_language_changed)
        tk.Label(details, text="CV:", bg="#f4f7fb").grid(row=1, column=3, padx=(20, 8), pady=(11, 0))
        self.cv_picker = ttk.Combobox(details, textvariable=self.cv_choice, state="readonly", width=23); self.cv_picker.grid(row=1, column=4, pady=(11, 0))
        ttk.Button(details, text=self.t("save_cv"), command=self.save_cv).grid(row=1, column=5, padx=10, pady=(11, 0)); ttk.Button(details, text=self.t("open_cv"), command=self.open_selected_cv).grid(row=1, column=6, pady=(11, 0))
        preselection = ttk.Button(details, text=self.t("preselect"), command=self.run_preselection); preselection.grid(row=2, column=0, pady=(10, 0), sticky="w"); Tooltip(preselection, lambda: self.t("ai_tooltip"))
        detailed = ttk.Button(details, text=self.t("detailed"), command=self.run_detailed); detailed.grid(row=2, column=1, columnspan=2, padx=(18, 0), pady=(10, 0), sticky="w"); Tooltip(detailed, lambda: self.t("ai_tooltip"))
        ttk.Button(details, text=self.t("create_cv"), command=self.create_cv).grid(row=2, column=3, columnspan=2, padx=(18, 0), pady=(10, 0), sticky="w")
        inspect = ttk.Button(details, text=self.t("inspect_cv"), command=self.inspect_current_cvs); inspect.grid(row=3, column=0, columnspan=3, pady=(10, 0), sticky="w"); Tooltip(inspect, lambda: self.t("ai_tooltip"))
        self._ai_progress_var = tk.StringVar()
        self._ai_progress_label = tk.Label(details, textvariable=self._ai_progress_var, bg="#f4f7fb", fg="#b26a00", font=("Segoe UI", 9, "italic"))
        self._ai_progress_label.grid(row=3, column=3, columnspan=4, pady=(10, 0), sticky="w")
        self.cv_language_changed()

    def make_filter(self, parent, label_key, choices, variable):
        tk.Label(parent, text=self.t(label_key), bg="#f4f7fb", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(10, 0))
        display = [self.t(key) for key in choices]
        box = ttk.Combobox(parent, values=display, state="readonly", width=18)
        box.set(self.t(variable.get()))
        box.pack(side="left", padx=8)
        box.bind("<<ComboboxSelected>>", lambda event: (variable.set(next(key for key in choices if self.t(key) == event.widget.get())), self.apply_filters()))

    def change_interface_language(self, _event=None) -> None:
        for child in self.winfo_children(): child.destroy()
        self.title(self.t("title")); self._build(); self.apply_filters()

    def open_settings(self):
        current = load_settings()
        dialog = tk.Toplevel(self); dialog.title(self.t("settings")); dialog.transient(self); dialog.grab_set(); dialog.geometry("720x720"); dialog.minsize(620, 560)
        frame = tk.Frame(dialog, padx=22, pady=18); frame.pack(fill="both", expand=True)
        general = tk.LabelFrame(frame, text=self.t("settings"), padx=14, pady=12)
        general.pack(fill="x")
        tk.Label(general, text=self.t("initial_limit"), font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        count = tk.IntVar(value=current["initial_review_limit"])
        ttk.Spinbox(general, from_=1, to=30, textvariable=count, width=6).grid(row=0, column=1, padx=(14, 0), sticky="w")
        tk.Label(general, text=self.t("default_mode"), font=("Segoe UI", 10, "bold")).grid(row=1, column=0, pady=(12, 0), sticky="w")
        mode_key = next(key for key, code in MODE_CODES.items() if code == current["detailed_review_mode"])
        mode = tk.StringVar(value=mode_key)
        choices = [self.t(key) for key in MODE_CODES]
        box = ttk.Combobox(general, values=choices, state="readonly", width=18); box.set(self.t(mode_key)); box.grid(row=1, column=1, padx=(14, 0), pady=(12, 0), sticky="w")
        box.bind("<<ComboboxSelected>>", lambda event: mode.set(next(key for key in MODE_CODES if self.t(key) == event.widget.get())))
        arrangements = set(current.get("work_arrangements", ["ofis", "hibrit", "uzaktan"]))
        office = tk.BooleanVar(value="ofis" in arrangements)
        hybrid = tk.BooleanVar(value="hibrit" in arrangements)
        remote = tk.BooleanVar(value="uzaktan" in arrangements)
        tk.Label(general, text=self.t("work_type"), font=("Segoe UI", 10, "bold")).grid(row=2, column=0, pady=(12, 0), sticky="w")
        work_frame = tk.Frame(general); work_frame.grid(row=2, column=1, padx=(14, 0), pady=(12, 0), sticky="w")
        ttk.Checkbutton(work_frame, text=self.t("office"), variable=office).pack(side="left")
        ttk.Checkbutton(work_frame, text=self.t("hybrid"), variable=hybrid).pack(side="left", padx=(10, 0))
        ttk.Checkbutton(work_frame, text=self.t("remote"), variable=remote).pack(side="left", padx=(10, 0))

        preferences = ttk.Notebook(frame)
        preferences.pack(fill="both", expand=True, pady=(14, 0))
        selected_values, custom_values, option_sources, controllers = {}, {}, {key: list(values) for key, values in PREFERENCE_OPTIONS.items()}, {}

        def search_key(value):
            return value.casefold().translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))

        def unique_clean(values):
            result, seen = [], set()
            for value in values:
                cleaned = str(value).strip()
                marker = search_key(cleaned)
                if cleaned and marker not in seen:
                    result.append(cleaned)
                    seen.add(marker)
            return result

        def selected_with_custom(key):
            controllers[key]["remember"]()
            typed = custom_values[key].get().split(",")
            return unique_clean([*sorted(selected_values[key], key=search_key), *typed])

        def refresh_dependent_options(key):
            if key == "target_sectors":
                option_sources["target_roles"] = roles_for_sectors(set(selected_values[key]))
                controllers["target_roles"]["refresh"]()
            elif key == "target_countries":
                option_sources["target_cities"] = cities_for_countries(set(selected_values[key]))
                controllers["target_cities"]["refresh"]()

        def confirm_selection(key):
            values = selected_with_custom(key)
            selected_values[key] = set(values)
            custom_values[key].set("")
            try:
                save_settings({key: values})
            except (OSError, TypeError, ValueError):
                controllers[key]["status"].set(self.t("selection_save_error"))
                return
            refresh_dependent_options(key)
            controllers[key]["refresh"]()
            controllers[key]["status"].set(self.t("selection_saved"))

        def add_multi_choice(key, height):
            labels = {"target_roles": "roles", "target_sectors": "sectors", "target_countries": "countries", "target_cities": "cities", "seniority": "seniority"}
            page = tk.Frame(preferences, padx=18, pady=14)
            preferences.add(page, text=self.t(labels[key]))
            page.columnconfigure(0, weight=1)
            holder = tk.Frame(page)
            holder.grid(row=0, column=0, sticky="nsew")
            search = tk.StringVar()
            tk.Label(holder, text=self.t("search")).pack(anchor="w")
            ttk.Entry(holder, textvariable=search, width=47).pack(fill="x", pady=(2, 4))
            list_holder = tk.Frame(holder); list_holder.pack(fill="both", expand=True)
            listbox = tk.Listbox(list_holder, selectmode=tk.MULTIPLE, exportselection=False, height=height, width=47)
            scroll = ttk.Scrollbar(list_holder, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scroll.set)
            listbox.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
            selected_values[key] = set(unique_clean(current.get(key, [])))
            visible = []
            refreshing = [False]
            def refresh_options(*_args):
                refreshing[0] = True
                try:
                    query = search_key(search.get())
                    selected_first = sorted(selected_values[key], key=search_key)
                    remaining = [option for option in option_sources[key] if option not in selected_values[key]]
                    all_options = unique_clean([*selected_first, *remaining])
                    visible[:] = [option for option in all_options if query in search_key(option)]
                    listbox.delete(0, "end")
                    for index, option in enumerate(visible):
                        listbox.insert("end", option)
                        if option in selected_values[key]:
                            listbox.selection_set(index)
                finally:
                    refreshing[0] = False
            def remember_selection(_event=None):
                if refreshing[0]:
                    return
                selected_values[key].difference_update(visible)
                selected_values[key].update(listbox.get(index) for index in listbox.curselection())
                controller = controllers.get(key)
                if controller:
                    controller["status"].set("")
            listbox.bind("<<ListboxSelect>>", remember_selection)
            search.trace_add("write", refresh_options)
            custom = tk.StringVar()
            custom_values[key] = custom
            tk.Label(page, text=self.t("other")).grid(row=1, column=0, sticky="w", pady=(12, 2))
            ttk.Entry(page, textvariable=custom, width=48).grid(row=2, column=0, sticky="ew")
            action_row = tk.Frame(page)
            action_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
            ttk.Button(action_row, text=self.t("confirm_selection"), command=lambda chosen_key=key: confirm_selection(chosen_key)).pack(side="left")
            status = tk.StringVar()
            tk.Label(action_row, textvariable=status, fg="#257942").pack(side="left", padx=(10, 0))
            tk.Label(page, text=self.t("confirm_hint"), justify="left", wraplength=610, fg="#4a6072").grid(row=4, column=0, sticky="w", pady=(8, 0))
            controllers[key] = {"refresh": refresh_options, "remember": remember_selection, "page": page, "status": status}
            custom.trace_add("write", lambda *_args, status_var=status: status_var.set(""))
            refresh_options()

        add_multi_choice("target_sectors", 11)
        add_multi_choice("target_roles", 11)
        add_multi_choice("target_countries", 11)
        add_multi_choice("target_cities", 11)
        add_multi_choice("seniority", 8)

        option_sources["target_roles"] = roles_for_sectors(set(selected_values["target_sectors"]))
        option_sources["target_cities"] = cities_for_countries(set(selected_values["target_countries"]))
        controllers["target_roles"]["refresh"]()
        controllers["target_cities"]["refresh"]()

        def save():
            try:
                chosen = {key: selected_with_custom(key) for key in selected_values}
                work = [name for name, selected in (("ofis", office.get()), ("hibrit", hybrid.get()), ("uzaktan", remote.get())) if selected]
                save_settings({"initial_review_limit": count.get(), "detailed_review_mode": MODE_CODES[mode.get()], **chosen, "work_arrangements": work, "remote_ok": "uzaktan" in work or "hibrit" in work})
            except (tk.TclError, ValueError):
                return
            dialog.destroy(); messagebox.showinfo(self.t("settings"), self.t("settings_saved"))
        ttk.Button(frame, text=self.t("save"), command=save).pack(anchor="e", pady=(14, 0))

    def help_text(self) -> str:
        skill_path = ROOT / "AI-ONBOARDING-SKILL.md"
        if self.app_language.get() == "EN":
            return f"""Using the system without AI

1. Install Python 3.11+, then run: pip install -r requirements.txt
2. Create a data folder, then copy ilan-kaynaklari.ornek.json as data/ilan-kaynaklari.json and adjust your search.
3. Start the application. Collect jobs, filter them, and record the CV you used.

The collector, duplicate check, filters, and local records work without AI or a CLI. LibreOffice is only needed to open generated DOCX files.

For users who want to use AI

Initial review, detailed review, and current-CV comparison use AI and can consume the connected model account's quota. This version includes the Hermes CLI adapter for automated AI actions.

For another model, use the model-neutral onboarding instruction below and configure a compatible local CLI adapter before enabling automated AI actions. A browser/chat-only model can still be used manually: copy the instruction, answer its questions, then place the resulting private JSON files beside this app.

First personal setup

Before detailed evaluation, give your preferred AI the onboarding instruction. It asks for target roles, locations, education, real experience/projects, skills, languages and existing CV links. Save its verified outputs as data/profil.json and data/aday-kanitlari.json. These files remain local and are ignored by Git.

Using a local AI

If you have an AI running locally, you can copy and send this file path to it. Ask the model to read the file before it starts: {skill_path}

If your local AI cannot access files directly, use “Copy AI onboarding instruction” below and paste the copied text into the model.
"""
        return f"""Yapay zeka olmadan sistemi kullanmak

1. Python 3.11+ kur, sonra: pip install -r requirements.txt
2. data klasörünü oluştur; ilan-kaynaklari.ornek.json dosyasını data/ilan-kaynaklari.json adıyla kopyala ve aramanı düzenle.
3. Uygulamayı aç. İlanları topla, filtrele ve kullandığın CV'yi kaydet.

İlan toplama, tekrar ayıklama, filtreler ve yerel kayıtlar yapay zeka veya CLI olmadan çalışır. Oluşturulan DOCX dosyalarını açmak için LibreOffice isteğe bağlıdır.

Yapay zeka kullanmak isteyenler için

Ön eleme, detaylı eleme ve mevcut CV karşılaştırması yapay zeka kullanır; bağlı model hesabının kotasını tüketebilir. Bu sürüm otomatik yapay zeka işlemleri için Hermes CLI bağdaştırıcısını içerir.

Bu sürüm Hermes CLI bağdaştırıcısını içerir. Başka bir model için aşağıdaki model-bağımsız başlangıç yönergesini kullan; otomatik yapay zeka düğmelerini açmadan önce uyumlu bir yerel CLI bağdaştırıcısı yapılandır. Sadece tarayıcı/sohbet modeli de manuel kullanılabilir: yönergeyi kopyala, soruları yanıtla, oluşan özel JSON dosyalarını uygulamanın yanına koy.

İlk kişisel kurulum

Detaylı elemeye başlamadan önce tercih ettiğin yapay zeka modeline başlangıç yönergesini ver. Model; hedef roller, konum, eğitim, gerçek deneyim/projeler, beceriler, dil seviyesi ve mevcut CV bağlantılarını sorar. Doğrulanmış çıktıları data/profil.json ve data/aday-kanitlari.json olarak kaydet. Bu dosyalar yerelde kalır ve Git'e eklenmez.

Yerelde çalışan yapay zeka kullanıyorsan

Yerel yapay zekan varsa bu dosya yolunu kopyalayıp modele atabilirsin. Modelden başlamadan önce bu dosyayı okumasını iste: {skill_path}

Yerel yapay zeka dosya okuyamıyorsa aşağıdaki “Yapay zeka başlangıç yönergesini kopyala” düğmesine bas; kopyalanan metni doğrudan modele yapıştır.
"""

    def show_first_run_help(self):
        if not load_settings().get("welcome_shown"):
            self.show_help(first_run=True)

    def show_help(self, first_run=False):
        dialog = tk.Toplevel(self); dialog.title(self.t("help")); dialog.transient(self); dialog.resizable(False, False)
        if first_run:
            dialog.grab_set()
        frame = tk.Frame(dialog, padx=22, pady=18); frame.pack(fill="both", expand=True)
        text = scrolledtext.ScrolledText(frame, width=74, height=22, wrap="word", font=("Segoe UI", 10))
        text.insert("1.0", self.help_text()); text.configure(state="disabled"); text.pack(fill="both", expand=True)
        def copy_skill():
            skill = (ROOT / "AI-ONBOARDING-SKILL.md").read_text(encoding="utf-8")
            self.clipboard_clear(); self.clipboard_append(skill); self.update()
            messagebox.showinfo(self.t("help"), self.t("skill_copied"), parent=dialog)
        def copy_skill_path():
            self.clipboard_clear(); self.clipboard_append(str(ROOT / "AI-ONBOARDING-SKILL.md")); self.update()
            messagebox.showinfo(self.t("help"), self.t("path_copied"), parent=dialog)
        copy_text_button = ttk.Button(frame, text=self.t("copy_skill"), command=copy_skill)
        copy_text_button.pack(anchor="e", pady=(12, 0)); Tooltip(copy_text_button, lambda: self.t("copy_skill_tip"))
        copy_path_button = ttk.Button(frame, text=self.t("copy_skill_path"), command=copy_skill_path)
        copy_path_button.pack(anchor="e", pady=(7, 0)); Tooltip(copy_path_button, lambda: self.t("copy_path_tip"))
        def use_without_ai():
            if first_run:
                save_settings({"welcome_shown": True})
            dialog.destroy()
        ttk.Button(frame, text=self.t("use_without_ai"), command=use_without_ai).pack(anchor="w", pady=(12, 0))
        if first_run:
            original_close = dialog.destroy
            def close():
                save_settings({"welcome_shown": True}); original_close()
            dialog.protocol("WM_DELETE_WINDOW", close)


    def load_jobs(self) -> list[dict]:
        jobs = {}
        for file in sorted(HISTORY_DIR.glob("tarama-*.json")):
            record = load_json(file, {}); scan_date = record.get("scan_date") or record.get("ran_at", "")[:10]
            for job in record.get("new_jobs", []): jobs.setdefault(fingerprint(job), {**job, "scan_date": scan_date, "key": fingerprint(job)})
        state = load_json(HAIKU_STATE, {})
        for key, job in jobs.items(): job["haiku"] = state.get(key, {})
        return list(jobs.values())

    def reload_data(self) -> None:
        self.jobs = self.load_jobs(); self.decisions = load_json(DECISIONS_FILE, {})
        self.matches = load_json(MATCH_STATE, {}); self.ats_scores = load_json(ATS_SCORES_FILE, {})
        dates = sorted({job["scan_date"] for job in self.jobs if job.get("scan_date")}, reverse=True); self.date_picker.configure(values=(self.t("custom_date"), *dates)); self.custom_date.set(self.t("custom_date")); self.apply_filters()

    def apply_filters(self) -> None:
        local_today = datetime.now().strftime("%Y-%m-%d")
        local_yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        wanted = {"today": local_today, "yesterday": local_yesterday}.get(self.date_filter.get())
        if self.date_filter.get() == "custom": wanted = self.custom_date.get() if self.custom_date.get() != self.t("custom_date") else None
        self.tree.delete(*self.tree.get_children()); self.filtered = []
        for job in self.jobs:
            h_code = job.get("haiku", {}).get("etiket", ""); d_code = self.matches.get(job["key"], {}).get("karar", "")
            if wanted and job["scan_date"] != wanted: continue
            sf = self.status_filter.get()
            if sf == "not_processed":
                if h_code: continue
            elif sf != "all":
                if h_code != STATUS.get(sf, ""): continue
            df = self.detail_filter.get()
            if df == "not_reviewed":
                if d_code: continue
            elif df != "all":
                if d_code != DECISIONS.get(df, ""): continue
            cv = self.decisions.get(job["key"], {}).get("cv") or self.t("not_selected")
            self.filtered.append(job); self.tree.insert("", "end", iid=job["key"], values=(job["scan_date"], job["company"], job["title"], job["location"], self.label_for_status(h_code), self.label_for_decision(d_code), cv))
        reviewed, waiting = sum(job["key"] in self.matches for job in self.jobs), sum(not job.get("haiku") for job in self.jobs)
        self.summary.set(f"{len(self.jobs)} {'unique jobs' if self.app_language.get() == 'EN' else 'benzersiz ilan'} · {len(self.filtered)} {'shown' if self.app_language.get() == 'EN' else 'görünümde'} · {reviewed} {'reviewed in detail' if self.app_language.get() == 'EN' else 'detaylı incelendi'} · {waiting} {'awaiting initial review' if self.app_language.get() == 'EN' else 'ön eleme bekliyor'}")
        self.selected_key = None; self.detail_text.set(self.t("choose_job_text")); self.cv_language_changed()

    def pick_custom_date(self, _event=None):
        if self.custom_date.get() != self.t("custom_date"): self.date_filter.set("custom"); self.apply_filters()

    def cv_language_changed(self, _event=None):
        options = cv_options(self.cv_language.get()); self.cv_picker.configure(values=options)
        if self.cv_choice.get() not in options: self.cv_choice.set(options[0])

    def on_select(self, _event=None):
        chosen = self.tree.selection()
        if not chosen: return
        self.selected_key = chosen[0]; job = next(job for job in self.jobs if job["key"] == self.selected_key); self.set_detail(job, True); self.calculate_ats(job)

    def set_detail(self, job, calculating=False):
        match = self.matches.get(job["key"], {}); mode = next((self.t(key) for key, code in MODE_CODES.items() if code == match.get("mode")), self.t("strict"))
        detail = self.t("not_reviewed") if not match else f"{self.label_for_decision(match.get('karar', ''))} ({mode}) · {match.get('uyum_puani', '?')}/100 · {match.get('cv_tipi', 'genel')}"
        ats = self.ats_scores.get(job["key"])
        ats_line = f"{self.t('local_ats')} ({ats.get('basis', 'job text')}): " + " · ".join(f"{row['cv']}: {row['puan']}/100" for row in ats.get("rows", [])) if ats else (self.t("ats_wait") if calculating else self.t("ats_none"))
        self.detail_text.set(f"{job['company']} · {job['title']}\n{job['location']} · {self.t('date')}: {job['scan_date']} · {self.t('status')} {self.label_for_status(job.get('haiku', {}).get('etiket', ''))}\n{self.t('detail')} {detail}\n{ats_line}")
        saved = self.decisions.get(job["key"], {}); self.cv_language.set(saved.get("language", match.get("cv_dili", "TR"))); self.cv_language_changed(); self.cv_choice.set(saved.get("cv", cv_options(self.cv_language.get())[0]))

    def calculate_ats(self, job):
        def run():
            try: result = get_or_compute(job["key"], job)
            except Exception as error: result = {"error": str(error)}
            self.after(0, lambda: self.after_ats(job["key"], result))
        threading.Thread(target=run, daemon=True).start()

    def after_ats(self, key, result):
        if result.get("error"): return
        self.ats_scores[key] = result
        if self.selected_key == key: self.set_detail(next(job for job in self.jobs if job["key"] == key))

    def require_job(self):
        if self.selected_key: return True
        messagebox.showinfo(self.t("choose_job"), self.t("choose_job_text")); return False

    def open_link(self):
        if self.require_job(): webbrowser.open(next(job for job in self.jobs if job["key"] == self.selected_key)["source_url"])

    def save_cv(self):
        if not self.require_job(): return
        self.decisions[self.selected_key] = {"cv": self.cv_choice.get(), "language": self.cv_language.get(), "saved_at": datetime.now().isoformat()}
        write_json(DECISIONS_FILE, self.decisions); self.apply_filters(); messagebox.showinfo(self.t("saved"), self.t("saved_text"))

    def open_selected_cv(self):
        if not self.require_job(): return
        saved = self.decisions.get(self.selected_key, {}); path = Path(saved["generated_file"]) if saved.get("generated_file") else data_dir("CV-Sürümleri") / f"{self.cv_choice.get()}.docx"
        if not saved.get("generated_file") and not self.cv_choice.get(): messagebox.showinfo(self.t("choose_cv"), self.t("choose_cv_text")); return
        try:
            path.resolve().relative_to(data_dir("CV-Sürümleri").resolve())
        except ValueError:
            messagebox.showerror(self.t("open_error"), "CV dosyası uygulamanın CV-Sürümleri klasörü dışında olamaz."); return
        if not path.exists(): messagebox.showerror(self.t("cv_missing"), f"{self.t('cv_missing_text')}\n{path}"); return
        soffice = Path(r"C:\Program Files\LibreOffice\program\soffice.exe")
        try:
            if soffice.exists(): subprocess.Popen([str(soffice), "--view", str(path)])
            else:
                import os; os.startfile(path)
        except OSError as error: messagebox.showerror(self.t("open_error"), str(error))

    def run_script(self, script, title, *args):
        is_ai_script = script in {"ilan_haiku_on_ele.py", "ilan_sonnet_esle.py", "cv_uyum_incele.py"}
        if is_ai_script and self._ai_running:
            messagebox.showinfo(self.t("ai_busy"), self.t("ai_busy_text")); return
        if is_ai_script:
            self._ai_running = True
        def run():
            result = subprocess.run([sys.executable, str(ROOT / script), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.after(0, lambda: self.after_script(result, title, script, is_ai_script))
        threading.Thread(target=run, daemon=True).start()

    def format_scan_result(self, stdout: str) -> str:
        """Ham teknik JSON yerine, sıfır sonucun nedenini de söyleyen kısa özet."""
        try:
            report = json.loads(stdout)
        except (TypeError, json.JSONDecodeError):
            return stdout.strip() or "Done."
        downloaded = report.get("downloaded_cards", report.get("raw_cards", 0))
        matched = report.get("preference_matched", report.get("raw_cards", 0))
        message = self.t("scan_summary").format(
            downloaded=downloaded, matched=matched, filtered=report.get("filtered_out", 0),
            new=report.get("new", len(report.get("new_jobs", []))), seen=report.get("previously_seen", 0),
        )
        if downloaded == 0:
            message += "\n\n" + self.t("scan_no_cards")
        elif matched == 0:
            reasons = report.get("filter_reasons", {})
            details = ", ".join(f"{key}: {value}" for key, value in reasons.items())
            message += "\n\n" + self.t("scan_no_match") + (f"\n({details})" if details else "")
        failures = report.get("source_failures", [])
        if failures:
            source_lines = "\n".join(f"• {item.get('source', '?')}: {item.get('error', '?')}" for item in failures)
            message += "\n\n" + self.t("scan_failures").format(failures=source_lines)
        source_stats = report.get("source_stats", [])
        if source_stats and (downloaded == 0 or matched == 0):
            source_lines = "\n".join(
                f"• {item.get('source', '?')}: {item.get('downloaded_cards', 0)} / {item.get('preference_matched', 0)}"
                for item in source_stats
            )
            message += "\n\n" + self.t("scan_sources").format(sources=source_lines)
        return message

    def after_script(self, result, title, script, was_ai=False):
        if was_ai:
            self._ai_running = False
        self.reload_data()
        if result.returncode == 0:
            message = self.format_scan_result(result.stdout) if script == "ilan_topla.py" else result.stdout.strip() or "Done."
            messagebox.showinfo(title, message)
        else:
            messagebox.showerror(self.t("collect_error") if script == "ilan_topla.py" else title, result.stderr.strip() or "Operation failed.")

    def collect_jobs(self):
        if messagebox.askyesno(self.t("collect"), self.t("collect_confirm")): self.run_script("ilan_topla.py", self.t("collect_done"))

    def check_hermes(self) -> bool:
        if not is_hermes_available():
            messagebox.showwarning(self.t("hermes_missing"), self.t("hermes_missing_text"))
            return False
        return True

    def run_preselection(self):
        if not self.check_hermes(): return
        self.run_script("ilan_haiku_on_ele.py", self.t("preselect"))

    def run_detailed(self):
        if not self.check_hermes(): return
        if self._ai_running or is_detailed_locked():
            messagebox.showinfo(self.t("ai_busy"), self.t("ai_busy_text")); return
        dialog = tk.Toplevel(self); dialog.title(self.t("mode_title")); dialog.transient(self); dialog.grab_set(); dialog.resizable(False, False)
        frame = tk.Frame(dialog, padx=22, pady=18); frame.pack(fill="both", expand=True)
        tk.Label(frame, text=self.t("mode_prompt"), font=("Segoe UI", 12, "bold")).pack(anchor="w"); tk.Label(frame, text=self.t("mode_info"), justify="left", wraplength=510).pack(anchor="w", pady=(8, 12))
        configured_mode = load_settings()["detailed_review_mode"]
        selected = tk.StringVar(value=next(key for key, code in MODE_CODES.items() if code == configured_mode)); box = ttk.Combobox(frame, values=[self.t(key) for key in MODE_CODES], state="readonly", width=18); box.set(self.t(selected.get())); box.pack(anchor="w")
        box.bind("<<ComboboxSelected>>", lambda event: selected.set(next(key for key in MODE_CODES if self.t(key) == event.widget.get())))
        buttons = tk.Frame(frame); buttons.pack(anchor="e", pady=(16, 0)); ttk.Button(buttons, text=self.t("cancel"), command=dialog.destroy).pack(side="right")
        def start(): dialog.destroy(); self.run_script("ilan_sonnet_esle.py", self.t("detailed"), "--mode", MODE_CODES[selected.get()])
        ttk.Button(buttons, text=self.t("start"), command=start).pack(side="right", padx=(0, 8))

    def create_cv(self):
        if not self.require_job(): return
        if self.selected_key not in self.matches: messagebox.showinfo(self.t("match_required"), self.t("match_required_text")); return
        if messagebox.askyesno(self.t("create_cv"), self.t("create_confirm")): self.run_script("cv_ilan_olustur.py", self.t("create_cv"), self.selected_key)

    def inspect_current_cvs(self):
        if not self.check_hermes(): return
        if self.require_job(): self.run_script("cv_uyum_incele.py", self.t("inspect_cv"), self.selected_key)


if __name__ == "__main__":
    Application().mainloop()
