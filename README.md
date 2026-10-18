# 🛡️ AegisLend AI

### Intelligent and Secure Digital Lending Ecosystem

AegisLend AI is a digital lending platform designed to combine secure authentication, loan application management, AI-assisted experiences, and intelligent security monitoring in a unified application.

The project brings together a modern web frontend, a Python backend, relational database management, and an AI-oriented architecture to explore how intelligent automation and cybersecurity can support digital lending workflows.

> **Project status:** Under active development. This repository distinguishes implemented application foundations from AI and security capabilities that require further integration or validation.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Technology Stack](#️-technology-stack)
- [System Architecture](#️-system-architecture)
- [Implemented Functionality](#-implemented-functionality)
- [Planned Enhancements](#-planned-enhancements)
- [Prerequisites](#-prerequisites)
- [Windows Installation and Setup](#️-windows-installation-and-setup)
- [Environment Configuration](#-environment-configuration)
- [Database Migrations](#️-database-migrations)
- [Running the Application](#-running-the-application)
- [Testing](#-testing)
- [Security Considerations](#-security-considerations)
- [Project Structure](#-project-structure)
- [Future Roadmap](#-future-roadmap)
- [Contributing](#-contributing)
- [Author](#-author)
- [License](#-license)

---

## 🌟 Overview

Traditional digital lending workflows involve several interconnected activities, including customer authentication, loan application submission, application review, appointment management, and security monitoring.

AegisLend AI explores a unified approach to these workflows through a modular software architecture.

### Project objectives

- Build a professional digital lending application with a responsive user interface.
- Provide authenticated access to protected application functionality.
- Support loan application and administrative review workflows.
- Use a relational database for structured application data.
- Explore Retrieval-Augmented Generation (RAG) for context-aware AI assistance.
- Develop a hybrid intrusion detection approach combining security rules and machine learning.
- Establish a maintainable foundation for future AI-driven financial services.

## ✨ Key Features

### 🏦 Digital Lending Workflows

- Customer-facing lending dashboard.
- Loan application and application-status workflows.
- Administrative application review.
- Appointment-related functionality.
- Structured backend services for application data.

### 🔐 Authentication and Access Control

- User registration and login functionality.
- Password hashing using Argon2id.
- JWT bearer-token authentication.
- Protected endpoints and administrative access controls.
- Token expiration and authentication validation.

### 🤖 AI and Retrieval-Augmented Generation

The project includes AI/RAG as a development objective for context-aware assistance within the lending ecosystem.

Potential applications include answering questions using an approved knowledge base and assisting users in navigating lending information.

**Note:** The scope of the implemented RAG pipeline, its data sources, retrieval quality, and production readiness must be verified against the current code before treating these as completed capabilities.

### 🛡️ Hybrid Intrusion Detection — Development Goal

The security architecture aims to combine:

- Rule-based detection of suspicious activity.
- Machine-learning-based behavioral analysis.
- Risk assessment and incident management.
- Administrative security monitoring.

The completeness and integration of individual detection components should be assessed against the current implementation and tests.

---

## 🧰 Technology Stack

| Layer               | Technologies                     |
| ------------------- | -------------------------------- |
| Frontend            | React, Vite, TypeScript          |
| Styling             | Tailwind CSS                     |
| Backend             | Python, FastAPI                  |
| Validation          | Pydantic                         |
| ORM                 | SQLAlchemy                       |
| Database migrations | Alembic                          |
| Database            | MySQL                            |
| Authentication      | JWT bearer tokens                |
| Password security   | Argon2id                         |
| Containerization    | Docker, Docker Compose           |
| Testing             | Pytest and frontend test tooling |

AI, RAG, and hybrid intrusion detection components are part of the project's broader architecture and development goals. Their exact libraries and integration status should be confirmed in the repository.

---

## 🏗️ System Architecture

The application follows a frontend–backend architecture with a relational database.

```text
┌──────────────────────────────────────┐
│          React Frontend              │
│       TypeScript + Tailwind CSS      │
└──────────────────┬───────────────────┘
                   │ HTTP / API
                   ▼
┌──────────────────────────────────────┐
│          FastAPI Backend             │
│                                      │
│ Authentication and Access Control    │
│ Request Validation                   │
│ Application and Review Workflows     │
│ AI / RAG Integration Points           │
│ Security Monitoring Integration      │
└──────────────────┬───────────────────┘
                   │ SQLAlchemy
                   ▼
┌──────────────────────────────────────┐
│               MySQL                  │
│       Persistent Application Data    │
└──────────────────────────────────────┘
```

Docker Compose supports local infrastructure management. AI-assisted functionality and hybrid intrusion detection are intended to integrate with the application through appropriate backend components.

This diagram represents the intended logical architecture; it does not imply that every AI or security component is fully integrated.

---

## ✅ Implemented Functionality

The following project foundations have been implemented during development:

- React, Vite, TypeScript, and Tailwind CSS frontend.
- FastAPI backend with Pydantic-based request validation.
- SQLAlchemy database integration and Alembic migration infrastructure.
- MySQL configuration and Docker-based database infrastructure.
- User registration and login flows.
- Argon2id password hashing.
- Expiring JWT bearer tokens.
- Protected current-user and administrative access functionality.
- Frontend and backend automated tests.

Earlier development verification recorded **43 passing backend tests and 6 passing frontend tests**, with two backend tests skipped at that stage. These are historical results, not a guarantee of the current test status.

---

## 🚧 Planned Enhancements

The following items represent areas for continued development and validation, not guaranteed completed features.

### AI and RAG

- Complete and validate document ingestion and retrieval workflows.
- Improve grounding and relevance of AI-generated answers.
- Integrate AI assistance with suitable lending workflows.
- Add evaluation tests for retrieval quality and response reliability.

### Hybrid Intrusion Detection

- Integrate rule-based and machine-learning detection into a unified pipeline.
- Validate behavioral classification against representative test data.
- Add risk scoring and incident lifecycle management.
- Improve administrative security visibility and auditability.

### Platform Improvements

- Expand automated testing and integration coverage.
- Improve monitoring, structured logging, and error handling.
- Strengthen deployment configuration and operational documentation.
- Improve accessibility, responsiveness, and overall user experience.

---

## 📋 Prerequisites

Install the following tools before setting up the project on Windows:

- **Git** — to clone and manage the repository.
- **Node.js and npm** — to install and run the frontend.
- **Python 3.12** — the version used during the documented backend setup.
- **Docker Desktop** — to run the MySQL service through Docker Compose.
- A terminal such as Windows PowerShell.

Check the installed tools:

```powershell
git --version
node --version
npm --version
python --version
docker --version
docker compose version
```

If your Python executable is registered as `py`, you can also check Python using:

```powershell
py --version
```

---

## 🪟 Windows Installation and Setup

### 1. Clone the repository

```powershell
git clone https://github.com/Chiragmohite/AegisLend.git
cd AegisLend
```

If the repository is private, sign in to GitHub or configure Git authentication before cloning.

### 2. Configure the backend environment

From the project root:

```powershell
cd backend
python -m venv ..\.venv
```

Activate the virtual environment:

```powershell
..\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use the virtual environment's Python executable directly instead.

Install the backend dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Return to the project root:

```powershell
cd ..
```

### 3. Configure environment variables

Inspect the environment templates before creating local configuration files.

```powershell
Get-Content .env.example
Get-Content backend\.env.example
Get-Content frontend\.env.example
```

Create the local environment files required by the actual application configuration. For example, if the root template is intended for the root Compose configuration:

```powershell
Copy-Item .env.example .env
```

Only create the backend and frontend files from their respective templates if those files are expected by the current code.

Update local configuration with your own database settings, authentication secrets, and other required values. Do not commit populated `.env` files or real credentials.

Refer to [Environment Configuration](#-environment-configuration) before starting the services.

### 4. Start MySQL using Docker Compose

From the project root, inspect the Compose configuration and identify the service names and environment files:

```powershell
docker compose config --services
```

Start the appropriate database service using the Compose configuration intended for local development:

```powershell
docker compose up -d
```

Check container status:

```powershell
docker compose ps
```

If the repository uses a separate Compose file for development or support services, select that file explicitly after checking its contents.

**Important:** Do not use `docker compose down -v`, remove Docker volumes, or reset the database merely to resolve a startup problem. Those actions can delete persistent database data.

### 5. Run database migrations

From the project root, activate the virtual environment if it is not already active:

```powershell
..\.venv\Scripts\Activate.ps1
```

Inspect the migration configuration and ensure the database connection settings are correct. Then run:

```powershell
cd backend
alembic upgrade head
```

Run this command only if the existing Alembic configuration and migration scripts are set up for the configured database. Review pending migrations before applying them to any database containing important data.

### 6. Start the backend

From the `backend` directory:

```powershell
..\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

The command above matches the project's previously used local development startup command.

If startup fails, verify that the Python dependencies are installed, the required environment variables are present, and the database is reachable.

### 7. Start the frontend

Open a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite will print the local development URL in the terminal. Open that URL in your browser.

### 8. Verify the application

- Confirm that the MySQL container is running and healthy.
- Confirm that the backend starts without configuration errors.
- Open the frontend URL printed by Vite.
- Test the authentication flow.
- Verify protected functionality with an authenticated account.
- Run the available automated tests.

The exact API routes, test commands, and frontend URL should be taken from the current source code and configuration rather than assumed.

---

## 🔑 Environment Configuration

The project uses environment-based configuration for local development.

Depending on the existing application setup, configuration may include:

| Setting                        | Purpose                                  |
| ------------------------------ | ---------------------------------------- |
| Database host and port         | Locate the MySQL service                 |
| Database name                  | Select the application database          |
| Database username and password | Authenticate to MySQL                    |
| JWT signing secret             | Sign and verify authentication tokens    |
| Token lifetime                 | Control authentication-token expiration  |
| Frontend API base URL          | Configure communication with the backend |

These are configuration categories, not verified environment-variable names. Use the actual names defined by the project's settings and Compose files.

### Environment security rules

- Keep populated `.env` files out of Git.
- Use strong, unique secrets for local environments.
- Never reuse development secrets in production.
- Keep database credentials out of frontend code.
- Do not expose JWT signing keys or database passwords in logs.
- Use `.env.example` files only for safe placeholder values.

---

## 🗄️ Database Migrations

AegisLend AI uses SQLAlchemy for database interaction and Alembic for schema migrations.

Common migration commands, when supported by the existing migration configuration:

```powershell
cd backend
alembic current
alembic history
alembic upgrade head
```

- `alembic current` displays the current migration revision.
- `alembic history` lists migration history.
- `alembic upgrade head` applies migrations up to the latest revision.

Review migration scripts before applying schema changes to an existing database. Back up important data before performing potentially destructive schema operations.

---

## 🧪 Testing

Automated tests are part of the development workflow.

### Backend

The project has used Pytest during development. From the backend directory, run:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

### Frontend

From the frontend directory, inspect the available npm scripts:

```powershell
npm run
```

Run the test script defined by the project's `package.json`. For example, use `npm test` only if a `test` script exists.

### Testing goals

- Authentication and token validation.
- Protected-resource access controls.
- Request validation and error handling.
- Database integration and migrations.
- Frontend component and workflow behavior.
- AI retrieval and security-detection correctness as those components are integrated.

Always rely on the latest test run for current results.

---

## 🔒 Security Considerations

Security is an important design consideration for a digital lending platform.

The implemented authentication foundations include Argon2id password hashing, expiring JWT bearer tokens, and protected application access.

However, authentication foundations alone do not establish that the entire application is production-ready.

Before deploying a real financial application, additional work may be required in areas such as:

- HTTPS and secure token handling.
- Rate limiting and abuse prevention.
- Authorization checks on every protected resource.
- Input validation and database access security.
- Audit logging and incident response.
- Secret management and key rotation.
- Data privacy, retention, and access policies.
- Security testing and dependency vulnerability checks.
- Regulatory and compliance requirements applicable to the deployment.

Use synthetic data during development. Do not upload real customer financial information, credentials, or private database backups to a public repository.

---

## 📁 Project Structure

The repository is organized around separate frontend, backend, documentation, and scripts directories.

```text
AegisLend/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── migrations/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── .env.example
├── docs/
├── scripts/
├── .env.example
├── .gitignore
├── README.md
└── compose.yaml
```

This is a conceptual overview of the expected project layout. Directory and file names can vary; refer to the repository for the authoritative structure.

---

## 🗺️ Future Roadmap

- [ ] Validate and complete end-to-end lending workflows.
- [ ] Improve automated integration and regression testing.
- [ ] Complete and evaluate the RAG pipeline.
- [ ] Integrate and validate hybrid intrusion detection.
- [ ] Improve security monitoring and incident management.
- [ ] Add production-oriented deployment documentation.
- [ ] Strengthen accessibility, observability, and performance.

Items should be marked complete only after implementation and verification.

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make focused changes.
4. Run the relevant tests.
5. Open a pull request describing the change and its verification.

For substantial changes, discuss the proposed approach before modifying core authentication, database, or security components.

---

## 👨‍💻 Author

**Chirag Mohite**

GitHub: [@Chiragmohite](https://github.com/Chiragmohite)

Project repository: [AegisLend AI](https://github.com/Chiragmohite/AegisLend)

---

## 📄 License

No license has been specified here. Before distributing or accepting external contributions, add an appropriate `LICENSE` file and update this section to reflect the chosen license.

---
