# Budget-Voyage

Budget-Voyage is a full-stack travel planning web application that helps users explore travel options, compare flights, find hotels and restaurants, plan itineraries, and manage saved bookings from one place. The project combines a React frontend with a FastAPI backend and uses travel datasets and recommendation logic to support budget-friendly trip planning.

## Live Demo

Deployed on Vercel using the Vercel CLI: https://virtual-tour-buddy.vercel.app

## Features

- Search and compare flights by source, destination, price, stops, and travel date.
- Explore hotels, restaurants, attractions, trains, and city-based travel options.
- Generate trip recommendations based on city, budget, dates, number of people, travel mode, and interests.
- Save itinerary items, bookings, reviews, wallet details, and travel buddy posts.
- Backend API built with FastAPI and MongoDB, with structured models for users, trips, bookings, reviews, and recommendations.
- React frontend with reusable UI components and responsive travel-planning screens.

## Tech Stack

- Frontend: React, CRACO, Tailwind CSS
- Backend: FastAPI, Python, Pydantic
- Database: MongoDB
- Deployment: Vercel
- Tools: Node.js, npm, Uvicorn

## Project Structure

```text
budgetVoyage/
├── api/              # Vercel serverless entry point
├── backend/          # FastAPI backend, services, and travel datasets
├── frontend/         # React frontend application
├── tests/            # Test files and reports
├── requirements.txt  # Python dependencies for deployment
└── vercel.json       # Vercel deployment configuration
```

## Running Locally

Install frontend dependencies:

```bash
cd frontend
npm install --legacy-peer-deps
```

Start the frontend:

```bash
npm start
```

Start the backend from the project root:

```bash
cd backend
uvicorn server:app --reload --port 8000
```

## Deployment

The project is deployed to Vercel with a custom `vercel.json` configuration. The frontend is built from the `frontend` directory, while the FastAPI backend is exposed through the `api/index.py` serverless entry point.
