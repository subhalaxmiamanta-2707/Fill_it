# 🚛 Fill-IT - Smart Logistics Platform

> *Revolutionizing the logistics industry with a modern, multi-role, real-time goods transportation platform.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore%20%26%20RTDB-FFCA28?logo=firebase&logoColor=black)](https://firebase.google.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Architecture & Directory Structure](#-architecture--directory-structure)
- [Getting Started](#-getting-started)
- [Demo Credentials](#-demo-credentials)
- [API Endpoint Reference](#-api-endpoint-reference)
- [Database & Fallback System](#-database--fallback-system)
- [Deployment & Environment Variables](#-deployment--environment-variables)
- [License](#-license)

---

## 🎯 Overview

**Fill-IT** is an end-to-end logistics platform designed to seamlessly connect goods senders (Customers) with vehicle operators (Drivers). Built using **FastAPI** on the backend and modern **Vanilla HTML5/CSS3/JS** on the frontend, Fill-IT provides real-time trip booking, location matching, trip status tracking, and multi-language support for regional logistics across India.

### 🌟 Highlights
- **Multi-Role Dashboards**: Custom-tailored portals for Customers and Drivers.
- **Real-Time Database Sync**: Realtime Database tracking for status transitions (`pending` $\rightarrow$ `driver_assigned` $\rightarrow$ `trip_completed` / `regret`).
- **Multi-Language Support**: Regionalized interface supporting 10+ Indian languages (Odia, Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, English).
- **Resilient Offline/Local Dev Mode**: Built-in fallback database proxies (`LocalFirestore` and `LocalRTDBRef`) allowing development and testing without requiring active GCP cloud credentials.
- **Automated Regret Scheduler**: Background `APScheduler` job automatically updating past pending trips to `regret`.

---

## ✨ Key Features

### 🛍 Customer Features
- **Trip Booking**: Interactive location and date selection (`Bhubaneswar` $\rightarrow$ `Cuttack`).
- **Trip History & Tracking**: Real-time view of assigned driver details, vehicle number, contact phone, and trip status.
- **Edit & Cancel Trips**: Update pickup/drop locations or cancel pending trip requests.
- **Profile Management**: Update contact details and personal preferences.

### 🚛 Driver Features
- **Trip Search**: Search available pending customer trips matching pickup locations and dates.
- **Trip Acceptance**: One-click trip assignment linking driver details to the customer's booking.
- **Assigned Trips Dashboard**: View active assigned journeys, contact customer directly, or release trips back to pending pool.
- **Trip Completion**: Mark journeys completed with automated ISO completion timestamps.

### 🌐 Core Platform
- **Unified FastAPI Server**: API endpoints and static frontend assets served directly at root `/`.
- **Dynamic API Base URL**: Auto-detects local vs production environment (`http://127.0.0.1:8000` vs `https://fill-it.onrender.com`).
- **Contact Us & Email Notifications**: Lead generation endpoint with Resend API backend integration.

---

## 🛠 Tech Stack

### Backend
- **Framework**: Python 3.11 with [FastAPI](https://fastapi.tiangolo.com/) & Uvicorn ASGI Server
- **Database & Auth**: Firebase Admin SDK (Firestore & Realtime Database)
- **Task Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/) for background status updates
- **Security & Utilities**: `pydantic`, `python-dotenv`, `itsdangerous`, `pytz`

### Frontend
- **Structure & Logic**: HTML5, ES6+ JavaScript (`async/await`, Fetch API)
- **Styling**: Vanilla CSS3 (Custom Glassmorphism, CSS Grid, Flexbox, Micro-animations)
- **Fonts & Assets**: Inter font via Google Fonts, custom vector SVG icons and graphics

---

## 🏗 Architecture & Directory Structure

```text
Fill-IT-main/
├── main.py                   # FastAPI Application Entrypoint & Static Server
├── firebase_config.py        # Firebase Admin SDK & Local Fallback Proxies (LocalFirestore/LocalRTDBRef)
├── login.py                  # Authentication Router (/login, /get-role, /get-profile, /update-profile, /logout)
├── signup.py                 # Registration Router (/signup, /update-phone)
├── c_book.py                 # Customer Trip Booking Router (/book-trip)
├── c_triphistory.py          # Customer History Router (/get-trip-history, /edit-trip, /delete-trip)
├── d_book.py                 # Driver Operations Router (/search_trips, /accept_trip, /complete_trip, /release_trip)
├── regret_scheduler.py       # APScheduler Background Service for Regret Updates
├── models.py                 # Pydantic Schemas & Data Transfer Objects
├── requirements.txt          # Python Dependencies
├── venv/                     # Virtual Environment
└── Frontend-Part/            # Frontend Web App Static Directory
    ├── index.html            # Landing Page & Contact Form
    ├── login.html            # Login Interface
    ├── signup.html           # Dual Role Signup Interface
    ├── c_home.html           # Customer Booking Dashboard
    ├── c_triphistrory.html   # Customer Trip History & Management Page
    ├── d_home.html           # Driver Trip Search & Discovery Dashboard
    ├── d_trip.html           # Driver Assigned Trips & Status Management
    ├── *.css                 # Styling Tokens & Component Stylesheets
    └── *.svg / *.png         # SVG Icons, Images & Brand Assets
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.11` or higher
- **pip**: Python package manager

### 1. Setup Virtual Environment & Dependencies

```bash
# Clone repository
git clone https://github.com/yourusername/Fill-IT.git
cd Fill-IT-main

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install jinja2 python-multipart
```

### 2. Launch Local FastAPI Server

```bash
# Run server with Uvicorn
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Open Web Application
Navigate to `http://127.0.0.1:8000` in your web browser.

---

## 👤 Demo Credentials

Pre-configured demo accounts for immediate testing:

### 🛍 Customer Demo Account
- **Role**: Customer
- **Email**: `demo.customer@fillit.com`
- **Password**: `DemoPassword123!`
- **Phone**: `9876543210`

### 🚛 Driver Demo Account
- **Role**: Driver
- **Email**: `demo.driver@fillit.com`
- **Password**: `DemoPassword123!`
- **Phone**: `9123456789`
- **Vehicle Number**: `OD-02-DEMO-9999`
- **Vehicle Chassis**: `CHASSIS-DEMO-12345`

---

## 🔌 API Endpoint Reference

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/api/health` | API Health Check |
| **System** | `POST` | `/api/contact` | Submit Contact Us form |
| **Auth** | `POST` | `/signup` | Register new Customer or Driver |
| **Auth** | `POST` | `/login` | Authenticate user & receive ID Token |
| **Auth** | `GET` | `/get-role` | Get user role (`customer` / `driver`) |
| **Auth** | `GET` | `/get-profile` | Fetch user profile details |
| **Auth** | `POST` | `/update-profile` | Update user profile phone number |
| **Auth** | `POST` | `/logout` | Invalidate user session / token |
| **Customer** | `POST` | `/book-trip` | Create a new trip request |
| **Customer** | `GET` | `/get-trip-history` | Fetch customer trips with live driver details |
| **Customer** | `PUT` | `/edit-trip/{trip_id}` | Edit pending trip pickup/drop/date |
| **Customer** | `DELETE` | `/delete-trip/{trip_id}` | Delete pending trip request |
| **Driver** | `POST` | `/api/driver/search_trips` | Search pending trips by location and date |
| **Driver** | `POST` | `/api/driver/accept_trip` | Accept trip and assign driver details |
| **Driver** | `GET` | `/api/driver/assigned_trips` | Fetch driver's assigned & completed trips |
| **Driver** | `POST` | `/api/driver/complete_trip` | Mark assigned trip as completed |
| **Driver** | `POST` | `/api/driver/release_trip` | Release trip back to pending pool |
| **Driver** | `GET` | `/api/driver/profile` | Fetch driver profile and vehicle details |

---

## 💾 Database & Fallback System

Fill-IT supports both **Cloud Firebase** and **Local Development Mode**:

1. **Cloud Mode**: Provide `serviceAccountKey.json` in project root or set `FIREBASE_SERVICE_ACCOUNT_JSON` in `.env`.
2. **Local Fallback Mode**: If GCP credentials are omitted, `firebase_config.py` automatically initializes `LocalFirestore` and `LocalRTDBRef` tree proxies. All data operates in-memory seamlessly without crashing.

---

## 🌐 Deployment & Environment Variables

### `.env` Configuration
Create a `.env` file in the project root:

```env
FIREBASE_PROJECT_ID=fill-it-19a6e
FIREBASE_SERVICE_ACCOUNT_KEY=serviceAccountKey.json
SESSION_SECRET_KEY=your_secure_session_secret
RESEND_API_KEY=re_your_resend_api_key
```

### Production Deployment (Render / Railway / Heroku)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## 📄 License

This project is licensed under the **MIT License**.

---

*Made with ❤️ for the logistics community.*
