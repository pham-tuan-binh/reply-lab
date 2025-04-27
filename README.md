# Aeron - Autonomous Drone Mapping via Natural Language

**Submission for the Reply Challenge @ TUM.ai Makeathon 2025**

Aeron is a system developed during the TUM.ai Makeathon 2025 that enables autonomous drone mapping generation using natural language commands. Given a voice prompt and a set of drone-captured images, Aeron calculates the necessary 3D coordinates for the drone to navigate to specified points of interest.

https://github.com/user-attachments/assets/30bfbee1-e394-4eeb-8693-658ccf7d4a9c

---

## Table of Contents

* [Team](#team)
* [Features](#features)
* [Project Structure](#project-structure)
* [Prerequisites](#prerequisites)
* [Getting Started](#getting-started)
    * [Backend Setup](#backend-setup)
    * [Frontend Setup](#frontend-setup)
* [Notebooks](#notebooks)
* [License](#license)

---

## Team

* **Binh**: 3D Mapping (SfM, COLMAP, Triangulation), Web App (Next.js), Server (FastAPI), KMZ File Generation (DJI).
* **Akshay**: MLOps Pipeline, Object Detection (RT-DETR), Object Matching (Hungarian Algorithm).
* **Isha**: Natural Language Processing Pipeline, Data Annotation, KMZ File Generation.
* *(Initial UI scaffolding generated using Vercel v0, subsequently integrated and extended.)*

---

## Features

* **Natural Language Interface:** Control drone mapping tasks using voice commands.
* **3D Mapping Pipeline:** Utilizes Structure from Motion (SfM) and point triangulation (COLMAP, custom linear algebra) for sparse reconstruction.
* **Object Detection:** Identifies relevant objects in drone imagery using RT-DETR.
* **Coordinate Generation:** Maps local world coordinates to ECEF and generates KMZ files for DJI drone navigation.
* **Web Interface:** Provides a user interface for interaction (image upload, prompt input).
* **Real-time Communication:** Uses FastAPI backend with WebSocket for seamless interaction.

---

## Project Structure
```
.
├── back_end/         # FastAPI server application
│   ├── main.py       # Main execution point (FastAPI app)
│   ├── test.py       # Script for testing the 3D pipeline
│   └── modules/      # Core pipeline modules (NLP, CV, 3D, etc.)
├── front_end/        # React.js web application
│   └── ...           # Next.js project files
├── notebooks/        # Research, experiments, and pipeline development
│   └── path_gen/     # Jupyter notebook detailing 3D triangulation pipeline
│       └── ...       # Notebook and associated data
├── results/          # Stores final output files (e.g., KMZ) for the challenge
└── README.md         # This file
```
---

## Prerequisites

Ensure you have the following installed on your system:

1.  **uv:** A fast Python package installer and resolver.
    * Installation guide: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
2.  **Node.js and npm:** Required for running the frontend application.
    * Installation guide: [https://docs.npmjs.com/downloading-and-installing-node-js-and-npm](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm)

---

## Getting Started

Follow these steps to set up and run the project:

### Backend Setup

The backend is a FastAPI server managed with `uv`.

1.  **Navigate to the backend directory:**
    ```bash
    cd back_end
    ```
2.  **Create a virtual environment and install dependencies (uv handles this):**
    *(Assuming a `pyproject.toml` file exists defining dependencies)*
    ```bash
    uv venv  # Create virtual environment (if not already done)
    uv pip install -r requirements.txt # Or install based on pyproject.toml if configured
    ```
    *(Note: Adjust the install command based on how dependencies are defined, e.g., `uv pip install .` if defined in `pyproject.toml`)*

3.  **Run the FastAPI server:**
    ```bash
    uv run main.py
    # Or if using uvicorn directly within the uv environment:
    # uv run uvicorn main:app --reload
    ```
    The server will start, typically on `http://127.0.0.1:8000`.

### Frontend Setup

The frontend is a React.js application (initially scaffolded with Vercel v0).

1.  **Navigate to the frontend directory:**
    ```bash
    cd front_end
    ```
2.  **Install dependencies:**
    * *Due to potential dependency conflicts inherited from the v0 generation, the `--force` flag might be necessary.*
    ```bash
    npm install --force
    ```
3.  **Run the development server:**
    ```bash
    npm run dev
    ```
    The application should open in your browser, typically at `http://localhost:3000`.

---

## Notebooks

The `/notebooks` directory contains research and development artifacts.

* **/notebooks/path_gen:** Includes a Jupyter Notebook developed by Binh, detailing the 3D triangulation pipeline. This covers SfM sparse reconstruction and mapping local world coordinates to ECEF, providing insights into the 3D mapping process used in Aeron.

---

## License

This project adheres to the rules and regulations set forth by the TUM.ai Makeathon 2025 challenge.
