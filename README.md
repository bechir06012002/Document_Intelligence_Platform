<div align="center">

# 🧾 Document Review System

**AI-assisted invoice and receipt review for facilities management.**

Extract, classify, validate, and review supplier documents in **English, Dutch, German, and French** before they reach bookkeeping.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python\&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi\&logoColor=white)](#)
[![Azure](https://img.shields.io/badge/Azure-AI%20Services-0078D4?logo=microsoftazure\&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?logo=streamlit\&logoColor=white)](#)
[![Docker](https://img.shields.io/badge/Docker-Deployment-2496ED?logo=docker\&logoColor=white)](#)

**[🌐 Live Demo](https://invoice-review-ui.blacktree-b3a09823.westeurope.azurecontainerapps.io)**

</div>

---

## 📖 Table of Contents

* [✨ Features](#-features)
* [🧠 How It Works](#-how-it-works)
* [🛠️ Tech Stack](#️-tech-stack)
* [📁 Project Structure](#-project-structure)
* [⚙️ Getting Started](#️-getting-started)
* [🚀 Deployment](#-deployment)
* [🎬 Demo](#-demo)

---

## ✨ Features

|                                |                                                                                |
| ------------------------------ | ------------------------------------------------------------------------------ |
| 📄 **Document Extraction**     | Extracts structured fields from PDF, PNG, and JPEG invoices and receipts       |
| 🤖 **AI Classification**       | Identifies document type and suggests a general ledger account                 |
| ✅ **Deterministic Validation** | Checks VAT formats, totals, required fields, and duplicate invoices            |
| 👤 **Human Review**            | Reviewers can correct fields, categorize documents, and approve or reject them |
| ✉️ **Correction Emails**       | Generates AI-drafted emails for supplier-caused errors                         |
| 🌍 **Multilingual**            | Supports English, Dutch, German, and French                                    |

---

## 🧠 How It Works

```text
Upload Invoice / Receipt
          │
          ▼
Azure AI Document Intelligence
          │
          ▼
   Structured Fields
          │
          ▼
    Azure OpenAI
   ┌──────┴──────┐
   │ Classification│
   │  + GL Account │
   └──────┬──────┘
          │
          ▼
 Deterministic Validation
          │
          ▼
     Human Review
     ┌────┴────┐
     ▼         ▼
  Approve    Reject
     │
     ▼
Correction Email
```

1. 📤 **Upload** — submit a PDF, PNG, or JPEG invoice or receipt.
2. 🔍 **Extract** — Azure AI Document Intelligence extracts vendors, VAT IDs, dates, totals, and line items.
3. 🤖 **Classify** — Azure OpenAI identifies the document type and suggests a GL account.
4. ✅ **Validate** — deterministic rules check the extracted data and flag policy issues.
5. 👤 **Review** — a human verifies the evidence, corrects fields, and approves or rejects the document.

---

## 🛠️ Tech Stack

| Layer       | Technology                     |
| ----------- | ------------------------------ |
| Backend     | FastAPI, SQLAlchemy, SQLite    |
| Document AI | Azure AI Document Intelligence |
| LLM         | Azure OpenAI, PydanticAI       |
| Frontend    | Streamlit                      |
| Deployment  | Docker, Azure Container Apps   |

---

## 📁 Project Structure

```text
backend/
├── ...
├── Dockerfile.api
└── .env.example

streamlit_app/
├── ...
└── Dockerfile.ui

run-dev.bat
```

---

## ⚙️ Getting Started

### Prerequisites

* Python 3.12+
* [uv](https://docs.astral.sh/uv/)
* Azure AI Document Intelligence resource
* Azure OpenAI resource

### Install Dependencies

```bash
cd backend
uv sync --locked

cd ../streamlit_app
uv sync --locked
```

Copy `backend/.env.example` to `backend/.env` and configure your Azure endpoint and credentials.

Then, from the repository root:

```bash
run-dev.bat
```

The API runs on `http://127.0.0.1:8000` and the UI on `http://127.0.0.1:8501`.

---

## 🚀 Deployment

The backend and frontend are built as separate Docker images and deployed as two **Azure Container Apps** within the same environment.

Azure credentials are provided through **Container Apps secrets** and are never baked into the Docker images.

> ⚠️ **Demo data:** All data is fictional. The demo database is ephemeral and may reset after redeployment.

---

## 🎬 Demo

https://github.com/user-attachments/assets/c79b5758-c5d8-4a30-9c91-669a3cedc29d

---

**[❤️ API Health Check](https://invoice-review.blacktree-b3a09823.westeurope.azurecontainerapps.io/health)**

</div>
