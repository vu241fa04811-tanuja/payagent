# PayAgent 🤖💳
> **Autonomous AI Agentic Commerce powered by Razorpay Test Mode APIs**  
> *Razorpay AI Buildathon — Track 1: AI Growth & Agentic Commerce*

---

## 📌 Problem Statement & Vision
In the emerging era of agentic commerce, AI assistants are transitioning from search engines to **autonomous buyers**. However, traditional e-commerce checkouts rely on human clicks, OTPs, and manual form fills.

**PayAgent** demonstrates how a merchant catalog can be made **100% transactable end-to-end by an AI buyer**. Given a natural language user intent (e.g., *"Buy a wireless mouse under ₹1000"*), PayAgent:
1. Discovers and inspects merchant product catalogs using structured tool calls (`search_products`, `get_product_details`).
2. Evaluates pricing, stock levels, and budget constraints autonomously.
3. Creates Razorpay Test Mode Orders (`create_order` via Razorpay Orders API).
4. Generates Razorpay Test Mode Payment Links (`generate_payment_link` via Payment Links API).
5. Settle transactions autonomously using Razorpay Test Credentials (`confirm_payment`).
6. Maintains a real-time, step-by-step decision audit trail and handles realistic failures (e.g., out-of-stock recovery).

---

## 🏗️ Architecture Diagram

```
                 +-------------------------------------------------------+
                 |                      USER / DEMO                      |
                 |      "Buy noise cancelling headphones under ₹4000"     |
                 +---------------------------+---------------------------+
                                             |
                                             v
                 +-------------------------------------------------------+
                 |                 PAYAGENT FRONTEND UI                  |
                 |  - Merchant Dashboard (Catalog & Orders)              |
                 |  - Agent Playground & Stepper Execution Timeline      |
                 +---------------------------+---------------------------+
                                             |  POST /api/agent/run
                                             v
                 +-------------------------------------------------------+
                 |                FASTAPI BACKEND SERVER                 |
                 |  - Catalog API: GET /api/products                     |
                 |  - Orders API:  GET /api/orders                       |
                 +---------------------------+---------------------------+
                                             |
                                             v
                 +-------------------------------------------------------+
                 |               AUTONOMOUS AGENT ENGINE                 |
                 |  - Intent Parser & Budget Constraint Evaluator        |
                 |  - Tool Calling Loop (OpenAI / Anthropic / Built-in)  |
                 |  - Decision Audit Logger & Error Recovery Manager     |
                 +----+----------------------+---------------------+-----+
                      |                      |                     |
     (1) search_products|     (2) create_order| (3) generate_link   | (4) confirm_payment
                      v                      v                     v                     v
            +-------------------+  +-------------------+  +-------------------+  +-------------------+
            | Merchant Catalog  |  | Razorpay Test API |  | Razorpay Test API |  | Razorpay Test Mode|
            |   (SQLite DB)     |  |   (Orders API)    |  | (Payment Links)   |  | Payment Settlement|
            +-------------------+  +-------------------+  +-------------------+  +-------------------+
```

---

## 🛠️ Tech Stack & Directory Structure

- **Backend**: Python 3.13 + FastAPI + Pydantic v2 + Uvicorn
- **Frontend**: HTML5 / CSS3 (Bootstrap 5 + Custom Glassmorphism Theme) / Vanilla JavaScript
- **Database**: SQLite / In-Memory Merchant Database (`payagent.db`)
- **Payments Integration**: Official Razorpay Test Mode APIs (`Orders API` + `Payment Links API`)
- **Agent Architecture**: Function/Tool-Calling pattern with OpenAI/Anthropic LLM adapter + zero-dependency autonomous decision engine fallback

```
payagent/
├── .env.example              # Environment template for Razorpay keys & LLM keys
├── README.md                 # Project documentation & Buildathon submission
├── requirements.txt          # Python dependencies
├── run.py                    # One-click application runner
├── backend/
│   ├── main.py               # FastAPI application entrypoint
│   ├── config.py             # App settings & env configuration
│   ├── db.py                 # SQLite database & merchant product catalog store
│   ├── models.py             # Pydantic data schemas
│   ├── catalog.py            # Merchant seed product catalog
│   ├── razorpay_client.py    # Razorpay REST API / Test Mode client
│   └── routes/
│       ├── catalog_routes.py # Catalog discovery & stock endpoints
│       ├── order_routes.py   # Merchant incoming order endpoints
│       └── agent_routes.py   # Autonomous agent execution endpoint
├── agent/
│   ├── core.py               # Main agent execution loop runner
│   ├── tools.py              # Callable tool implementations & OpenAI tool schemas
│   ├── llm_adapter.py        # Intent parser, tool executor & stock recovery manager
│   └── logger.py             # Step-by-step reasoning audit logger
└── frontend/
    ├── index.html            # Combined Merchant & Agent Dashboard UI
    ├── style.css             # Glassmorphism dark-theme stylesheet
    └── app.js                # Frontend state & visual timeline renderer
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Set Up Environment
```bash
# Navigate to payagent directory
cd payagent

# Create python virtual environment (optional)
py -m venv venv
# On Windows: venv\Scripts\activate
# On Linux/macOS: source venv/bin/activate

# Install dependencies
py -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your Razorpay Test Mode API keys from [Razorpay Dashboard -> Settings -> API Keys](https://dashboard.razorpay.com/app/keys):
```env
RAZORPAY_KEY_ID=rzp_test_YourTestKeyIdHere
RAZORPAY_KEY_SECRET=YourTestKeySecretHere
```
*(Note: If test keys are omitted, PayAgent gracefully operates in local simulation mode).*

### 3. Launch PayAgent
```bash
py run.py
```
Open your browser at:
- **Dashboard UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 💡 "What Broke & How I Fixed It" (Buildathon Writeup)

During development and live testing of PayAgent, we encountered and resolved key edge cases required for reliable agentic commerce:

### 1. The Out-of-Stock Trap (Failure Mode 1)
- **What Broke**: When an AI buyer attempts to purchase a high-preference item that is out of stock (e.g., *Active Noise Cancelling Headphones*, stock=0), naive agent implementations crash or repeatedly attempt failed Razorpay order creations.
- **How We Fixed It**: We implemented an **Autonomous Pivot & Recovery Mechanism** inside `agent/llm_adapter.py`. When `create_order` or stock evaluation returns `stock=0` / `OUT_OF_STOCK`, the agent logs a `RECOVERING` status, inspects alternative catalog candidates matching the budget, pivots to an available product (e.g., *Ergonomic Wireless Mouse* or *Bluetooth Speaker*), and successfully completes the Razorpay transaction without human intervention.

### 2. Console Encoding Mismatch on Windows Terminals
- **What Broke**: Printing Unicode emojis in stdout caused Windows console cp1252 `UnicodeEncodeError`.
- **How We Fixed It**: Cleaned server startup logging in `run.py` to use ASCII-safe characters, preventing process crashes on Windows environments.

### 3. Strict Budget Enforcement
- **What Broke**: Users specifying constraints like *"under ₹1000"* would occasionally match items with higher price points if price parameters weren't strictly parsed.
- **How We Fixed It**: Standardized budget parsing regex in `parse_intent` and enforced hard filter bounds in `AgentTools.search_products` so the agent strictly rejects items exceeding the specified threshold.

---

## 🎬 Live Demo Walkthrough Guide

To present PayAgent in a demo video or panel review:

1. **Standard Purchase Flow**:
   - In the Agent Playground tab, click preset: **"Buy a wireless mouse under ₹1000"**.
   - Watch the live execution stepper invoke `search_products` ➔ `create_order` ➔ `generate_payment_link` ➔ `confirm_payment`.
   - Observe the generated Razorpay Test Order ID and Payment Link URL.

2. **Out-of-Stock Error Recovery Flow (Key Feature!)**:
   - Click preset: **"Buy noise cancelling headphones under ₹4000"**.
   - The primary headphones item is intentionally seeded with `stock = 0`.
   - Watch PayAgent detect the out-of-stock condition, log a `RECOVERING` audit step explaining its reasoning, pivot to an available candidate, and complete the order cleanly!

3. **Merchant Inventory Real-Time Sync**:
   - Switch to the **Merchant Dashboard & Catalog** tab.
   - Click **"Set Stock=0"** on any item or view the incoming Razorpay orders updating live as PayAgent completes purchases.
