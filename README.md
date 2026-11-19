# Market Databank Generation and Sharing Platform

[![Python Version](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey.svg)](https://www.sqlite.org/)
[![Frontend](https://img.shields.io/badge/Frontend-Bootstrap_5.3.3-purple.svg)](https://getbootstrap.com/)
[![Charts](https://img.shields.io/badge/Charts-Chart.js_4.4-orange.svg)](https://www.chartjs.org/)

An academic research data-sharing web application built with Python and Django. Designed for students, researchers, and data analysts to collect, upload, validate, curate, preview, and exchange market-oriented datasets across multiple economic sectors.

---

## 📌 Project Features

### 1. User Authentication & Profile Governance
- User registration with validation for email uniqueness and minimum password length.
- Session-based authentication (Login, Logout) with protected views (`@login_required`).
- Personalized user profile management displaying researcher bio, institutional affiliation, and activity statistics.
- Strict ownership controls: only authors can edit or delete their datasets.

### 2. Personalized Research Dashboard
- Aggregations based on real database records (Total accessible, personal contributions, public pool, active categories).
- **Chart.js** bar chart illustrating dataset distributions across active market sectors.
- **Chart.js** doughnut chart showing personal public vs. private dataset ratio.
- Quick navigation shortcuts and dual recent activity streams (Personal uploads vs. Community activity).

### 3. CSV Ingestion & Validation Pipeline
- Validates `.csv` file format and limits file size to 10MB to avoid denial-of-service risks.
- Character stream decoding across `UTF-8`, `UTF-8-SIG` (Excel BOM), and `Latin-1`.
- Dialect and delimiter detection using standard library `csv.Sniffer`.
- Header row detection and automatic row/column indexing.

### 4. Tabular Data Preview & Visualization
- Instant tabular preview of the first 15–20 rows of any dataset.
- Automatic column schema listing with a single-click "Copy Headers" clipboard feature.
- Empirical sample trend line graph powered by **Chart.js** for candidate numeric fields (prices, yields, volumes).

### 5. Fine-Grained Access Control & Secure Streaming
- **Public Datasets:** Discoverable and downloadable by all registered community members.
- **Private Datasets:** Isolated at the ORM query level (`Q(is_public=True) | Q(owner=request.user)`). Unauthorized requests to inspect or download trigger an HTTP 403 `PermissionDenied` response.
- **Secure File Streaming:** CSV downloads are handled via Django's `FileResponse` attachment stream instead of exposing unauthenticated media directory URLs.

### 6. Search, Filter & Sector Navigation
- Real-time keyword search across dataset title, description, source, and column names.
- Multi-dimensional filters: by market sector, upload timeline (today, past week, past month, past year), and visibility.
- Sorting by newest, oldest, row count, file size, and download popularity.

---

## 📂 Market Sectors

1. **Stock Market** (Equities, indices, daily trading volumes, valuation metrics)
2. **Agriculture** (Commodity spot prices, crop production, seasonal yields)
3. **Real Estate** (Housing affordability indices, mortgage benchmarks, inventory absorption)
4. **Cryptocurrency** (Digital asset time series, liquidity depth, market capitalization)
5. **Business & Economics** (Macroeconomic indicators, GDP growth, inflation, employment)
6. **Other** (Alternative data, cross-sector surveys, exploratory research)

---

## 🏗️ Project Architecture

```
market_databank/
├── market_databank/          # Project configuration & root URL routing
│   ├── settings.py           # Installed apps, templates, auth, security
│   ├── urls.py               # Root URL configuration & media serving
│   ├── wsgi.py
│   └── asgi.py
├── databank/                 # Core application
│   ├── models.py             # Category, Dataset, and UserProfile models
│   ├── forms.py              # Registration, Login, Profile & Dataset upload forms
│   ├── utils.py              # CSV validator, dialect sniffer, row preview parser
│   ├── tests.py              # Automated test suite (13 unit tests)
│   ├── urls.py               # 12 application view endpoints
│   ├── views/                # Modular view controllers
│   │   ├── auth_views.py
│   │   ├── dashboard_views.py
│   │   └── dataset_views.py
│   └── management/commands/
│       └── seed_data.py      # Automated database seeder
├── templates/                # Responsive HTML5 Django templates
│   ├── base.html             # Reusable header, navbar, messages, and footer
│   ├── core/                 # Home (/) and About (/about/)
│   ├── accounts/             # Register, Login, and Profile
│   └── datasets/             # Dashboard, Explore, Detail, Upload, Edit, etc.
├── static/                   # Static assets
│   ├── css/style.css         # Academic research portal theme
│   └── js/main.js            # Client-side validation, alert auto-dismiss, clipboard
├── media/                    # Uploaded CSV dataset storage
└── sample_data/              # Seed CSV datasets for quick evaluation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git

### 2. Clone Repository
```bash
git clone https://github.com/<your-username>/market-databank.git
cd market-databank
```

### 3. Create & Activate Virtual Environment
**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Seed Demo Data & Categories
Populates the 6 categories, demo users, and sample market CSVs:
```bash
python manage.py seed_data
```

### 7. Run Test Suite
```bash
python manage.py test
```

### 8. Start the Local Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🔑 Demo Evaluation Credentials

| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Student Researcher** | `researcher` | `Student@123` | Owns a public stock dataset and a private research survey |
| **Administrator** | `admin` | `Admin@123` | Full superuser access to Django admin at `/admin/` |

---

## 🛡️ Security & Privacy Practices

1. **CSRF Defense**: All POST requests are guarded with Django's CSRF middleware tokens.
2. **Access Control**: Public datasets are open for browsing; private datasets strictly require authentication and ownership verification before allowing view, preview, or download.
3. **Safe File Uploads**: Reject files lacking `.csv` extension, exceeding 10MB, containing binary junk, or failing delimiter validation.
4. **No Direct Media Exposure**: Private files cannot be accessed via static URL scraping; file downloads are authenticated through a dedicated controller view.

---

## 📜 Academic Project Information
- **Course**: B.Tech in Computer Science & Engineering
- **Focus**: Full-Stack Web Development, Data Governance, Relational Schema Design, and Interactive Data Visualization.
