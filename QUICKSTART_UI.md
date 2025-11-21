# Weather-Aware Scheduler - Web UI Quick Start

This guide will help you get the Web UI up and running for manual testing.

## Prerequisites

- Python 3.11+
- Node.js 18+
- `uv` (Python package manager)

## 1. Backend Setup

The backend is a FastAPI application that acts as an adapter to the scheduling logic.

```bash
# Install Python dependencies
uv sync

# Start the Backend Server
# Runs on http://127.0.0.1:8000
uv run uvicorn src.adapters.primary.api.server:app --reload --port 8000
```

## 2. Frontend Setup

The frontend is a React application built with Vite.

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the Frontend Development Server
# Runs on http://localhost:5173
npm run dev
```

## 3. Manual Testing

1.  Open your browser and navigate to `http://localhost:5173`.
2.  You should see the "Weather Scheduler" interface.
3.  Try entering a natural language request:
    > "Tomorrow 2pm Taipei meet Alice 60min"
4.  Click **Schedule Meeting**.
5.  Verify that the result card appears with:
    - **City**: Taipei
    - **Time**: Correct date/time
    - **Attendees**: Alice
    - **Status**: Confirmed (or similar)

## Troubleshooting

- **Backend not connecting?**
    - Ensure the backend is running on port `8000`.
    - Check the console logs for any CORS errors (though CORS is configured to allow all origins for dev).
- **Empty page?**
    - Check the browser console (F12) for any React errors.
    - Ensure you are using a modern browser.
