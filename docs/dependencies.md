# Project Dependencies Overview

This document lists all the core dependencies and libraries required for the **Transcriber** RAG & STT Voice Query System.

---

## 🚀 Quick Installation

To set up the backend virtual environment and install all dependencies:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment if not already created
python -m venv .venv

# Activate virtual environment
# On Windows PowerShell:
.venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install fastapi uvicorn python-dotenv numpy pandas tqdm datasets sentence-transformers faiss-cpu torch transformers httpx pydantic
```

---

## 📋 Installed & Required Dependencies

### 1. Web & API Framework
| Package Name | Minimum Version / Note | Description & Usage |
| :--- | :--- | :--- |
| **`fastapi`** | `^0.100.0` | Modern, fast web framework for building backend REST APIs. |
| **`uvicorn`** | `^0.20.0` | High-performance ASGI server for hosting the FastAPI application. |
| **`python-dotenv`** | `^1.0.0` | Reads key-value pairs from `.env` file and sets them as environment variables. |
| **`httpx`** | `^0.28.0` | Asynchronous HTTP client for communicating with external APIs (e.g., Sarvam STT). |
| **`pydantic`** | `^2.0.0` | Data validation and settings management using Python type annotations. |

### 2. Data Processing & Retrieval (RAG Pipeline)
| Package Name | Minimum Version / Note | Description & Usage |
| :--- | :--- | :--- |
| **`datasets`** | `^3.0.0` | Hugging Face library to load and stream benchmark datasets like MSMARCO-XI. |
| **`sentence-transformers`** | `^3.0.0` | Framework for generating dense semantic vector embeddings. |
| **`faiss-cpu`** | `^1.8.0` | Facebook AI Similarity Search library for fast vector indexing and sub-200ms retrieval. |
| **`numpy`** | `^1.24.0` | Fundamental library for array computing, embedding manipulations, and vector operations. |
| **`pandas`** | `^2.0.0` | Data analysis and data frame manipulation for handling benchmark corpora. |
| **`tqdm`** | `^4.65.0` | Extensible progress bar for tracking dataset chunking, embedding generation, and indexing. |

### 3. Machine Learning & Transformer Models
| Package Name | Minimum Version / Note | Description & Usage |
| :--- | :--- | :--- |
| **`torch`** | `^2.0.0` | PyTorch tensor library used as the backbone for transformer models and vector computations. |
| **`transformers`** | `^4.40.0` | State-of-the-art Natural Language Processing library for tokenizers and LLM interfaces. |

### 4. Speech-to-Text (STT) & Generation (Planned / Integration)
| Package Name | Minimum Version / Note | Description & Usage |
| :--- | :--- | :--- |
| **`requests`** | `^2.31.0` | HTTP library for synchronous REST API calls to Sarvam AI STT service. |
| **`litellm`** | `^1.0.0` (Optional) | Unified SDK for calling fast LLM APIs with fallback capabilities. |

---

## 🛠️ Development & Testing Dependencies

| Package Name | Usage |
| :--- | :--- |
| **`pytest`** | Test runner for executing unit and integration test suites. |
| **`black`** | Code formatter ensuring PEP 8 style adherence. |
| **`ruff`** / **`flake8`** | Fast linter for static code analysis. |

---

## 📄 Dependency File Location
The raw requirements file for the backend application is maintained at [`backend/requirements.txt`](file:///c:/transcriber/backend/requirements.txt).
