"""Seed script to populate 30 realistic international scholarship, fellowship, and internship opportunities."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.opportunity import (
    FundingType,
    Opportunity,
    OpportunityKind,
    OpportunityStatus,
    Source,
    Tag,
)
from app.services.ingestion.engine import IngestionEngine

SAMPLE_SOURCES: list[dict[str, Any]] = [
    {
        "name": "Erasmus Mundus Catalogue",
        "source_type": "rss",
        "url": "https://www.eacea.ec.europa.eu/node/253/rss_en",
        "config": {
            "default_organization": "European Education and Culture Executive Agency",
            "default_country": "BE",
            "headers": {},
        },
        "is_active": True,
        "fetch_interval_minutes": 720,
    },
    {
        "name": "CERN Student and Career Programmes",
        "source_type": "rss",
        "url": "https://careers.cern/programmes/feed/",
        "config": {
            "default_organization": "CERN",
            "default_country": "CH",
            "headers": {},
        },
        "is_active": True,
        "fetch_interval_minutes": 720,
    },
    {
        "name": "Commonwealth Scholarship Commission",
        "source_type": "rss",
        "url": "https://cscuk.fcdo.gov.uk/feed/",
        "config": {
            "default_organization": "Commonwealth Scholarship Commission",
            "default_country": "GB",
            "headers": {},
        },
        "is_active": True,
        "fetch_interval_minutes": 720,
    },
]

SAMPLE_TAGS: list[dict[str, Any]] = [
    {"name": "STEM", "category": "field"},
    {"name": "Full Tuition", "category": "benefit"},
    {"name": "Monthly Stipend", "category": "benefit"},
    {"name": "Travel Allowance", "category": "benefit"},
    {"name": "Women in Tech", "category": "diversity"},
    {"name": "Developing Countries", "category": "eligibility"},
    {"name": "Research", "category": "type"},
    {"name": "Undergraduate", "category": "degree"},
    {"name": "Master's Degree", "category": "degree"},
    {"name": "PhD", "category": "degree"},
]

NOW = datetime.now(UTC)

SAMPLE_OPPORTUNITIES: list[dict[str, Any]] = [
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "DAAD Helmut-Schmidt-Programme for Public Policy and Good Governance",
        "organization": "German Academic Exchange Service (DAAD)",
        "description": "Master’s degree scholarships at select German universities for future leaders from developing and emerging countries wishing to actively promote democracy and social justice.",
        "country": "DE",
        "fields": ["Public Policy", "Economics", "Political Science", "International Relations"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("934.00"),
        "stipend_amount_max": Decimal("1200.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=75),
        "source_url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/helmut-schmidt/",
        "canonical_url": "https://www.daad.de/en/helmut-schmidt-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Master's Degree", "Monthly Stipend", "Developing Countries"],
    },
    {
        "kind": OpportunityKind.FELLOWSHIP.value,
        "title": "ETH Zurich Excellence Scholarship & Opportunity Programme (ESOP)",
        "organization": "ETH Zurich",
        "description": "Full study scholarship covering living and tuition costs as well as a supervision fee for students wishing to pursue a Master's degree at ETH Zurich with an outstanding academic record.",
        "country": "CH",
        "fields": ["Computer Science", "Mechanical Engineering", "Biotechnology", "Physics"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("12000.00"),
        "stipend_amount_max": Decimal("12000.00"),
        "stipend_currency": "CHF",
        "deadline": NOW + timedelta(days=40),
        "source_url": "https://ethz.ch/students/en/studies/financial/scholarships/excellencescholarship.html",
        "canonical_url": "https://ethz.ch/esop-2026-spring",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Master's Degree", "Full Tuition", "Research"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Chevening International Master's Scholarships",
        "organization": "UK Foreign, Commonwealth and Development Office",
        "description": "Global scholarship program that enables emerging leaders to pursue a one-year Master's degree at any UK university with all living, flight, and tuition expenses covered.",
        "country": "GB",
        "fields": ["Public Health", "Climate Science", "Law", "Data Science", "Public Policy"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("1500.00"),
        "stipend_amount_max": Decimal("1850.00"),
        "stipend_currency": "GBP",
        "deadline": NOW + timedelta(days=90),
        "source_url": "https://www.chevening.org/scholarships/",
        "canonical_url": "https://www.chevening.org/apply-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Master's Degree", "Full Tuition", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.FELLOWSHIP.value,
        "title": "Fulbright Foreign Student Program",
        "organization": "U.S. Department of State",
        "description": "Enables graduate students, young professionals, and artists from abroad to research and study in the United States for one year or longer.",
        "country": "US",
        "fields": ["All Fields", "Humanities", "Social Sciences", "Engineering", "Medicine"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("2000.00"),
        "stipend_amount_max": Decimal("2800.00"),
        "stipend_currency": "USD",
        "deadline": NOW + timedelta(days=60),
        "source_url": "https://foreign.fulbrightonline.org/",
        "canonical_url": "https://foreign.fulbrightonline.org/apply-cohort-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Full Tuition", "Monthly Stipend", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "CERN Summer Student Programme in Computing and Physics",
        "organization": "European Organization for Nuclear Research (CERN)",
        "description": "8 to 13 weeks of hands-on work with state-of-the-art physics experiments and massive distributed computing infrastructure in Geneva.",
        "country": "CH",
        "fields": ["Computer Science", "Physics", "Electrical Engineering", "Applied Mathematics"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("3400.00"),
        "stipend_amount_max": Decimal("3400.00"),
        "stipend_currency": "CHF",
        "deadline": NOW + timedelta(days=25),
        "source_url": "https://careers.cern/summer-student-programme",
        "canonical_url": "https://careers.cern/summer-student-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Monthly Stipend", "Research"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Swedish Institute Scholarships for Global Professionals (SISGP)",
        "organization": "Swedish Institute",
        "description": "Full scholarships for master’s degree studies in Sweden, covering tuition fees, living expenses, health insurance, and travel grants.",
        "country": "SE",
        "fields": ["Sustainability", "Renewable Energy", "Global Health", "Computer Science"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("12000.00"),
        "stipend_amount_max": Decimal("12000.00"),
        "stipend_currency": "SEK",
        "deadline": NOW + timedelta(days=50),
        "source_url": "https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/",
        "canonical_url": "https://si.se/sisgp-call-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Master's Degree", "Full Tuition", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "Google DeepMind Student Research Mentorship",
        "organization": "Google DeepMind",
        "description": "Paid 16-week research internship pairing undergraduate and master's students with leading researchers in artificial intelligence and deep learning.",
        "country": "GB",
        "fields": ["Artificial Intelligence", "Machine Learning", "Computer Science"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("3800.00"),
        "stipend_amount_max": Decimal("4200.00"),
        "stipend_currency": "GBP",
        "deadline": NOW + timedelta(days=20),
        "source_url": "https://deepmind.google/careers/internships/",
        "canonical_url": "https://deepmind.google/research-intern-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Women in Tech", "Research"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Monbukagakusho (MEXT) Research Scholarship",
        "organization": "Ministry of Education, Culture, Sports, Science and Technology, Japan",
        "description": "Graduate level research scholarships for international students wishing to study at Japanese universities under embassy recommendation.",
        "country": "JP",
        "fields": ["Engineering", "Biomedical Sciences", "Japanese Studies", "Robotics"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("145000.00"),
        "stipend_amount_max": Decimal("148000.00"),
        "stipend_currency": "JPY",
        "deadline": NOW + timedelta(days=80),
        "source_url": "https://www.studyinjapan.go.jp/en/planning/scholarships/mext-scholarships/",
        "canonical_url": "https://www.studyinjapan.go.jp/mext-research-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Master's Degree", "Full Tuition", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.GRANT.value,
        "title": "Horizon Europe Marie Skłodowska-Curie Postdoctoral Fellowship",
        "organization": "European Research Council",
        "description": "Funding for excellent researchers undertaking international mobility to develop innovative skills through advanced training and research projects.",
        "country": "FR",
        "fields": ["Quantum Physics", "Computational Biology", "Materials Science"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("5000.00"),
        "stipend_amount_max": Decimal("6500.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=120),
        "source_url": "https://marie-sklodowska-curie-actions.ec.europa.eu/",
        "canonical_url": "https://ec.europa.eu/msca-postdoc-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Research"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Australia Awards Master's Scholarships",
        "organization": "Australian Department of Foreign Affairs and Trade (DFAT)",
        "description": "Long-term development awards administered to citizens from Indo-Pacific nations to undertake full-time master's study at participating Australian institutions.",
        "country": "AU",
        "fields": ["Environmental Management", "Public Health", "Agriculture", "Cybersecurity"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("3000.00"),
        "stipend_amount_max": Decimal("3000.00"),
        "stipend_currency": "AUD",
        "deadline": NOW + timedelta(days=65),
        "source_url": "https://www.dfat.gov.au/people-to-people/australia-awards",
        "canonical_url": "https://www.dfat.gov.au/australia-awards-intake-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Developing Countries", "Full Tuition", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Eiffel Excellence Scholarship Programme",
        "organization": "Campus France & French Ministry for Europe and Foreign Affairs",
        "description": "Designed to enable French higher education institutions to attract top foreign students for enrollment in their master’s and PhD programs.",
        "country": "FR",
        "fields": ["Engineering", "Economics", "Management", "Law"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("1181.00"),
        "stipend_amount_max": Decimal("1700.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=35),
        "source_url": "https://www.campusfrance.org/en/the-eiffel-scholarship-program",
        "canonical_url": "https://www.campusfrance.org/eiffel-award-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Master's Degree", "PhD", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "Max Planck Institute for Software Systems Summer Internship",
        "organization": "Max Planck Society",
        "description": "Fully paid 10-week summer research internship for undergraduate and master's students to collaborate with world-class faculty in computer systems and privacy.",
        "country": "DE",
        "fields": ["Software Engineering", "Cybersecurity", "Distributed Systems"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("1200.00"),
        "stipend_amount_max": Decimal("1400.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=15),
        "source_url": "https://www.mpi-sws.org/summer-internships/",
        "canonical_url": "https://www.mpi-sws.org/intern-call-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Research", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "University of Waterloo International Master's Award of Excellence",
        "organization": "University of Waterloo",
        "description": "Merit-based partial funding awarded to incoming international students enrolling in research-based Master's programs.",
        "country": "CA",
        "fields": ["Computer Science", "Applied Mathematics", "Mechanical Engineering"],
        "funding_type": FundingType.PARTIALLY_FUNDED.value,
        "stipend_amount_min": Decimal("2500.00"),
        "stipend_amount_max": Decimal("2500.00"),
        "stipend_currency": "CAD",
        "deadline": NOW + timedelta(days=45),
        "source_url": "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/awards/international-masters-award-excellence",
        "canonical_url": "https://uwaterloo.ca/imae-fall-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Master's Degree"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Amsterdam Merit Scholarship (AMS)",
        "organization": "University of Amsterdam",
        "description": "Outstanding students from outside the European Economic Area can apply for an Amsterdam Merit Scholarship to pursue Master's programs.",
        "country": "NL",
        "fields": ["Artificial Intelligence", "Cognitive Science", "Law", "Economics"],
        "funding_type": FundingType.PARTIALLY_FUNDED.value,
        "stipend_amount_min": Decimal("5000.00"),
        "stipend_amount_max": Decimal("25000.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=30),
        "source_url": "https://www.uva.nl/en/education/master-s/scholarships/ams.html",
        "canonical_url": "https://uva.nl/ams-2026-entry",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Master's Degree"],
    },
    {
        "kind": OpportunityKind.FELLOWSHIP.value,
        "title": "Rotary Peace Fellowship for Master's and Certificate Programs",
        "organization": "The Rotary Foundation",
        "description": "Full funding covering tuition and fees, room and board, round-trip transportation, and internship and field-study expenses for peace and development leaders.",
        "country": "US",
        "fields": ["Peace and Conflict Studies", "International Relations", "Human Rights"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("1800.00"),
        "stipend_amount_max": Decimal("2200.00"),
        "stipend_currency": "USD",
        "deadline": NOW + timedelta(days=110),
        "source_url": "https://www.rotary.org/en/our-programs/peace-fellowships",
        "canonical_url": "https://rotary.org/peace-fellow-2026-2027",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Full Tuition", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "KAIST International Undergraduate Scholarship",
        "organization": "Korea Advanced Institute of Science and Technology (KAIST)",
        "description": "Full tuition waiver and monthly stipend for undergraduate international applicants admitted with excellent high school standing.",
        "country": "KR",
        "fields": ["Aerospace Engineering", "Computer Science", "Bioengineering"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("350000.00"),
        "stipend_amount_max": Decimal("350000.00"),
        "stipend_currency": "KRW",
        "deadline": NOW + timedelta(days=55),
        "source_url": "https://admission.kaist.ac.kr/intl-undergraduate/scholarships",
        "canonical_url": "https://kaist.ac.kr/intl-ug-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Undergraduate", "Full Tuition", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "RIKEN Summer Student Programme in Brain Science",
        "organization": "RIKEN Center for Brain Science (CBS)",
        "description": "8 to 10 weeks of intensive research training in cognitive and computational neuroscience in Wako, Japan, with roundtrip flights and lodging provided.",
        "country": "JP",
        "fields": ["Neuroscience", "Computational Biology", "Psychology"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("120000.00"),
        "stipend_amount_max": Decimal("120000.00"),
        "stipend_currency": "JPY",
        "deadline": NOW + timedelta(days=18),
        "source_url": "https://cbs.riken.jp/en/summer/",
        "canonical_url": "https://riken.jp/cbs-summer-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Research", "Travel Allowance"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Gates Cambridge Scholarship",
        "organization": "Bill and Melinda Gates Foundation & University of Cambridge",
        "description": "Full-cost scholarship for outstanding applicants from countries outside the UK to pursue a full-time postgraduate degree in any subject at Cambridge.",
        "country": "GB",
        "fields": ["All Fields", "Genomics", "Philosophy", "Engineering", "Law"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("20000.00"),
        "stipend_amount_max": Decimal("20000.00"),
        "stipend_currency": "GBP",
        "deadline": NOW + timedelta(days=85),
        "source_url": "https://www.gatescambridge.org/",
        "canonical_url": "https://gatescambridge.org/apply-2026-cohort",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Master's Degree", "Full Tuition", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.GRANT.value,
        "title": "Swiss Government Excellence Research Scholarships",
        "organization": "Federal Commission for Scholarships for Foreign Students (FCS)",
        "description": "Postgraduate researchers and PhD holders in any academic discipline are supported for research stays at Swiss public universities.",
        "country": "CH",
        "fields": ["Life Sciences", "Civil Engineering", "Data Science", "Chemistry"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("1920.00"),
        "stipend_amount_max": Decimal("3500.00"),
        "stipend_currency": "CHF",
        "deadline": NOW + timedelta(days=70),
        "source_url": "https://www.sbfi.admin.ch/sbfi/en/home/education/scholarships-and-grants/swiss-government-excellence-scholarships.html",
        "canonical_url": "https://sbfi.admin.ch/fcs-scholarships-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Research", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Singapore International Graduate Award (SINGA)",
        "organization": "Agency for Science, Technology and Research (A*STAR)",
        "description": "Collaboration between A*STAR and top Singapore universities offering PhD training in biomedical sciences, computing, and physical sciences.",
        "country": "SG",
        "fields": ["Artificial Intelligence", "Nanotechnology", "Bioinformatics"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("2200.00"),
        "stipend_amount_max": Decimal("2700.00"),
        "stipend_currency": "SGD",
        "deadline": NOW + timedelta(days=48),
        "source_url": "https://www.a-star.edu.sg/Scholarships/for-graduate-studies/singapore-international-graduate-award-singa",
        "canonical_url": "https://a-star.edu.sg/singa-august-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "PhD", "Full Tuition", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "TUM International Graduate School Scholarship",
        "organization": "Technical University of Munich",
        "description": "Tuition grants and partial research subsidies for international students enrolled in master's and doctoral programs in engineering.",
        "country": "DE",
        "fields": ["Mechanical Engineering", "Robotics", "Automotive Systems"],
        "funding_type": FundingType.PARTIALLY_FUNDED.value,
        "stipend_amount_min": Decimal("500.00"),
        "stipend_amount_max": Decimal("900.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=62),
        "source_url": "https://www.tum.de/en/studies/fees-and-financial-aid/scholarships",
        "canonical_url": "https://tum.de/scholarships-2026-term",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Master's Degree"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "OECD Young Associates Programme",
        "organization": "Organisation for Economic Co-operation and Development",
        "description": "Two-year paid professional internship program for recent undergraduates to work alongside senior policy analysts in Paris.",
        "country": "FR",
        "fields": ["Economics", "Public Policy", "Statistics", "Environmental Studies"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("3500.00"),
        "stipend_amount_max": Decimal("3800.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=22),
        "source_url": "https://www.oecd.org/careers/young-associates-programme/",
        "canonical_url": "https://oecd.org/yap-intake-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Undergraduate", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "King Abdullah University of Science and Technology (KAUST) Fellowship",
        "organization": "KAUST",
        "description": "General fellowship supporting all admitted MS and PhD students with full tuition, monthly living allowance, private on-campus housing, and medical coverage.",
        "country": "SA",
        "fields": ["Computer Science", "Marine Science", "Chemical Engineering", "Solar Energy"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("20000.00"),
        "stipend_amount_max": Decimal("30000.00"),
        "stipend_currency": "USD",
        "deadline": NOW + timedelta(days=95),
        "source_url": "https://www.kaust.edu.sa/en/study/fellowship",
        "canonical_url": "https://kaust.edu.sa/fellowship-admissions-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "Master's Degree", "PhD", "Full Tuition", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.GRANT.value,
        "title": "Mitacs Globalink Research Award (GRA)",
        "organization": "Mitacs Canada",
        "description": "$6,000 grant for senior undergraduate, graduate students, and postdoctoral fellows in Canada to conduct 12-to-24-week research projects abroad.",
        "country": "CA",
        "fields": ["All Fields", "Engineering", "Natural Sciences", "Health"],
        "funding_type": FundingType.PARTIALLY_FUNDED.value,
        "stipend_amount_min": Decimal("6000.00"),
        "stipend_amount_max": Decimal("6000.00"),
        "stipend_currency": "CAD",
        "deadline": NOW + timedelta(days=105),
        "source_url": "https://www.mitacs.ca/en/programs/globalink/globalink-research-award",
        "canonical_url": "https://mitacs.ca/gra-call-round-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["Research"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Vanier Canada Graduate Scholarships",
        "organization": "Government of Canada",
        "description": "Prestigious scholarship to attract and retain world-class doctoral students who demonstrate leadership skills and a high standard of scholarly achievement.",
        "country": "CA",
        "fields": ["Health Research", "Natural Sciences", "Engineering", "Social Sciences"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("50000.00"),
        "stipend_amount_max": Decimal("50000.00"),
        "stipend_currency": "CAD",
        "deadline": NOW + timedelta(days=115),
        "source_url": "https://vanier.gc.ca/en/home-accueil.html",
        "canonical_url": "https://vanier.gc.ca/competition-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Monthly Stipend"],
    },
    # Items with different statuses for admin moderation testing
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Bavarian Government Scholarship for Developing Nations",
        "organization": "Bavarian Ministry of Science and the Arts",
        "description": "Scholarships for master's students at state universities in Bavaria needing financial aid.",
        "country": "DE",
        "fields": ["Humanities", "Social Sciences"],
        "funding_type": FundingType.PARTIALLY_FUNDED.value,
        "stipend_amount_min": Decimal("861.00"),
        "stipend_amount_max": Decimal("861.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=42),
        "source_url": "https://www.uni-bayreuth.de/en/bavarian-grant",
        "canonical_url": "https://uni-bayreuth.de/bavarian-grant-2026",
        "status": OpportunityStatus.PENDING_REVIEW.value,
        "tags": ["Master's Degree", "Developing Countries"],
    },
    {
        "kind": OpportunityKind.INTERNSHIP.value,
        "title": "UNEP Environmental Data Science Internship",
        "organization": "United Nations Environment Programme",
        "description": "Six-month research internship assisting with global biodiversity indicators and satellite mapping.",
        "country": "KE",
        "fields": ["Data Science", "Environmental Studies"],
        "funding_type": FundingType.UNFUNDED.value,
        "stipend_amount_min": None,
        "stipend_amount_max": None,
        "stipend_currency": None,
        "deadline": NOW + timedelta(days=28),
        "source_url": "https://www.unep.org/internships",
        "canonical_url": "https://unep.org/internship-call-2026-data",
        "status": OpportunityStatus.PENDING_REVIEW.value,
        "tags": ["Research"],
    },
    {
        "kind": OpportunityKind.FELLOWSHIP.value,
        "title": "Alexander von Humboldt Research Fellowship",
        "organization": "Alexander von Humboldt Foundation",
        "description": "Enables postdoctoral researchers of all nationalities and disciplines to carry out long-term research in Germany.",
        "country": "DE",
        "fields": ["Theoretical Physics", "Chemistry", "Archaeology"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("2670.00"),
        "stipend_amount_max": Decimal("3170.00"),
        "stipend_currency": "EUR",
        "deadline": NOW + timedelta(days=150),
        "source_url": "https://www.humboldt-foundation.de/en/apply/sponsorship-programmes/humboldt-research-fellowship",
        "canonical_url": "https://humboldt-foundation.de/fellowship-2026",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["PhD", "Research", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "CERN Doctoral Student Programme in Applied Computing",
        "organization": "CERN",
        "description": "36-month doctoral thesis program for students wishing to prepare a PhD in physics, computing, or engineering.",
        "country": "CH",
        "fields": ["Computer Science", "High Energy Physics", "Microelectronics"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("3800.00"),
        "stipend_amount_max": Decimal("3800.00"),
        "stipend_currency": "CHF",
        "deadline": NOW + timedelta(days=32),
        "source_url": "https://careers.cern/doctoral-student-programme",
        "canonical_url": "https://careers.cern/doc-student-2026-call",
        "status": OpportunityStatus.PUBLISHED.value,
        "tags": ["STEM", "PhD", "Monthly Stipend"],
    },
    {
        "kind": OpportunityKind.SCHOLARSHIP.value,
        "title": "Expired Sample: Rhodes Scholarship 2025",
        "organization": "The Rhodes Trust",
        "description": "Old opportunity included for verification of include_expired filter logic.",
        "country": "GB",
        "fields": ["All Fields"],
        "funding_type": FundingType.FULLY_FUNDED.value,
        "stipend_amount_min": Decimal("18000.00"),
        "stipend_amount_max": Decimal("18000.00"),
        "stipend_currency": "GBP",
        "deadline": NOW - timedelta(days=60),  # expired
        "source_url": "https://www.rhodeshouse.ox.ac.uk/scholarships/the-rhodes-scholarship/",
        "canonical_url": "https://rhodeshouse.ox.ac.uk/rhodes-2025-cycle",
        "status": OpportunityStatus.ARCHIVED.value,
        "tags": ["Master's Degree", "PhD"],
    },
]


async def seed_data() -> None:
    async with AsyncSessionLocal() as session:
        print("🌱 Seeding sources...")
        sources_map: dict[str, Source] = {}
        for src_data in SAMPLE_SOURCES:
            src_stmt = select(Source).where(Source.name == src_data["name"])
            existing_src = (await session.execute(src_stmt)).scalar_one_or_none()
            if not existing_src:
                src = Source(**src_data)
                session.add(src)
                await session.flush()
                sources_map[src.name] = src
                print(f"  + Added source: {src.name}")
            else:
                sources_map[existing_src.name] = existing_src

        print("🌱 Seeding tags...")
        tags_map: dict[str, Tag] = {}
        for tag_data in SAMPLE_TAGS:
            tag_stmt = select(Tag).where(Tag.name == tag_data["name"])
            existing_tag = (await session.execute(tag_stmt)).scalar_one_or_none()
            if not existing_tag:
                t = Tag(**tag_data)
                session.add(t)
                await session.flush()
                tags_map[t.name] = t
                print(f"  + Added tag: {t.name}")
            else:
                tags_map[existing_tag.name] = existing_tag

        print("🌱 Seeding 30 sample opportunities...")
        created_count = 0
        for opp_item in SAMPLE_OPPORTUNITIES:
            opp_dict = dict(opp_item)
            tag_names = opp_dict.pop("tags", [])
            opp_stmt = select(Opportunity).where(Opportunity.canonical_url == opp_dict["canonical_url"])
            existing_opp = (await session.execute(opp_stmt)).scalar_one_or_none()
            if not existing_opp:
                opp = Opportunity(**opp_dict)
                for tname in tag_names:
                    if tname in tags_map:
                        opp.tags.append(tags_map[tname])
                session.add(opp)
                created_count += 1
            else:
                print(f"  ~ Skipped existing opportunity: {existing_opp.title[:40]}...")

        await session.commit()
        print(f"✨ Successfully seeded {created_count} new opportunities! (Total: {len(SAMPLE_OPPORTUNITIES)})")

        print("🌐 Running configured online sources...")
        for source in sources_map.values():
            try:
                run = await IngestionEngine.run_ingestion_for_source(session, source)
                print(
                    f"  {source.name}: {run.status} "
                    f"(found={run.items_found}, created={run.items_created}, failed={run.items_failed})"
                )
            except Exception as exc:
                print(f"  {source.name}: ingestion unavailable ({type(exc).__name__})")


def main() -> None:
    asyncio.run(seed_data())


if __name__ == "__main__":
    main()
