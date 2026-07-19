#  University Library Self-Service System

Welcome to the **University Library Self-Service System**, a complete software ecosystem designed to modernize library operations. It pairs a sophisticated FastAPI backend powered by hybrid semantic search with a sleek, intuitive frontend Kiosk interface built for touch interactions on self-service library terminals.

##  Overview

The University Library Self-Service System transforms how students interact with the academic library. Students can authenticate seamlessly via their NFC student ID cards, discover literature through state-of-the-art semantic searches, track down physical copies via integrated location guidance, and autonomously checkout or return NFC-tagged books. No circulation desk queues—just a fluid, modern experience!
Originally developed as a simple AI-powered book search application, the system has evolved into a complete library management backend featuring:

NFC-based student identification
NFC-tagged physical book copies
Self-service borrowing and returning
AI-powered semantic book search using BGE-M3 embeddings
Vector search with Qdrant
Physical library location management
Automatic overdue fine generation
Student account blocking and unblocking
Complete RESTful API with Swagger documentation


This repository is split primarily into two domains:
- **`app/` (Backend API)**: The brains of the operation—a resilient, modular FastAPI application.
- **`Frontend/` (Kiosk App)**: A single-page, light-themed, purely Vanilla JS interactive kiosk interface.



##  The Backend: High-Performance API System

The backend provides all the computational power, data persistence, and intelligence for the library network. Built with Python and **FastAPI**, it strictly follows a domain-driven architectural pattern to ensure robust scalability and easy maintainability.

###  Key Backend Features
- **Smart Book Search (Hybrid & Semantic)**: Integrated with a Vector Database (Qdrant) and powered by BGE-M3 ML embeddings. This allows students to search for books by conceptual themes, exact titles, or even partial author names (`ILIKE` matches).
- **NFC-Driven Tap-and-Go**: Endpoints are designed specifically for NFC hardware operations. Students tap to sign in, and check out specific physical inventory copies each tagged with distinct NFC signatures.
- **Fines & Returns Management**: Fully automated ledgers monitoring due dates, applying late fines dynamically, and seamlessly transitioning physical copies back into circulation status when returned.
- **Modular Routers**: Endpoints for `students`, `books`, `copies`, `location`, `borrows`, `fines`, and the `catalog` are perfectly chunked inside `app/routers/`.
- **Swagger Documentation**: Live, interactive API documentation is automatically generated.

###  Backend Architecture
- **`app/main.py`**: The entrypoint mapping routers, managing CORS permissions (so the terminal can connect without friction), and executing async database lifespans.
- **`app/services/`**: The intelligence layer. Directly manages integrations with machine learning pipelines (`embedding.py`) and standardizes queries to semantic vector clusters (`vector_db.py`).
- **`app/database.py` & `app/schemas.py`**: Strong data typing mapping Pydantic validations explicitly directly against SQL models.

---

##  The Frontend: Interactive Kiosk Interface

The frontend is intentionally designed to run natively as a **Self-Service Kiosk Terminal**. It sidesteps heavy reactive frameworks in favor of a lightning-fast, state-driven Vanilla JS stack accompanied by a custom light-theme Tailwind CSS aesthetic (emphasizing clean whites and soft library greens). 

### 🎨 Frontend Highlights
- **True Touch Kiosk Mode**: Traditional desktop interactions (right-click, pinch-to-zoom context menus) are disabled out-of-the-box (`e.preventDefault()` via `app.js`). It expects human fingers, not mouse points.
- **Seamless State Navigation**: Uses a robust custom view-routing history buffer (`home`, `identify`, `dashboard`, `search`, `borrow`, `return`). Views transition fluidly natively without hard browser reloads.
- **Idle Security**: Idle timers actively monitor touch events. If a student walks away mid-session, the kiosk automatically securely clears their `STATE` and returns to the home page.
- **Minimalist Aesthetic**: Features a highly accessible, fast-rendering light mode with crisp typography perfectly suited to brightly lit campus library floors.

### 📂 Frontend Flow
- **`js/app.js` & `js/state.js`**: The foundational controllers tracking the globally logged-in `student` context, managing the view stack, preventing interface deadends, and clocking the top bar UI.
- **`js/views/` folder**: Visual layout modules managing discrete states (e.g., `identify.js` prompts the user for their NFC scan; `search.js` hits the API to display semantic book cards; `borrow.js` manages cart checkout logistics).
- **`js/api.js`**: A centralized, asynchronous fetch wrapper mapping all visual requests back to the FastAPI `/search/standard`, `/users/login`, or `/fines` endpoints cleanly.



## Core Modules

### Students

**Handles student registration and identification.**

- Features
- Register students
- NFC card identification
- Student profile retrieval
- Borrow history
- Fine history
- Active borrow tracking
- Automatic account blocking

### Books

**Manages the digital catalog.**

- Features
- Create books
- Update metadata
- Book details
- Physical copy listing
- AI semantic search
- Hybrid keyword + vector search

### Book Copies

**Every physical book inside the library is represented as an individual copy.**

Each copy contains

- NFC Tag
- Physical location
- Availability status
- Creation date

Supported statuses

- Available
- Borrowed
- Lost
- Damaged

### Borrow Management

**Handles the complete borrowing lifecycle.**

- Borrow
- Validate student
- Validate copy
- Create borrow record
- Update copy status
- Increase student's active borrow count
- Return
- Close borrow record
- Update copy status
- Decrease active borrow count
- Generate overdue fine if necessary

### Fine Management

**Automatically manages overdue penalties.**

Features include

- Automatic fine calculation
- Fine payment
- Fine waiver
- Automatic student blocking
- Automatic account unblocking after payment

## Catalog

Provides CRUD operations for

- Authors
- Book Categories



## Library Location

**The system models the physical layout of the library.**

        Floor
            │
            ▼
        Section
            │
            ▼
        Bookshelf
            │
            ▼
        Shelf Row
            │
            ▼
        Book Copy


##  Getting Started

### 1. Booting up the Backend API
You will need Python 3.11+ and pip. Ensure you have your relational database / Qdrant vector database spun up to accept connections via standard environments.

```bash
# Navigate to the repository root
# Install requirements
pip install -r requirements.txt

# Start the local ASGI development server via Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Once the log reads that the system is fully booted, check out the interactive documentation at `http://127.0.0.1:8000/docs`.

### 2. Turning on the Terminal Kiosk (Frontend)
Because it relies entirely on local HTML and Javascript, serving it is incredibly lightweight. 

```bash
# Navigate to the Frontend folder and localhost the javascript
cd Frontend

# The repository contains dummy data and backup databases for PostgreSQL and Qdrant testing.

          
##  Design Philosophy & Scale
By keeping the Kiosk Framework-less, the software footprint is minimized, perfectly facilitating operations on locked-down or cost-efficient terminal hardware (such as Raspberry Pi touchscreen pods). Meanwhile, the backend’s integration of semantic machine-learning ensures that discovery always feels modern and intuitive.

*Engineered natively for the academic campus of the future.*
