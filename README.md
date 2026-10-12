cat > README.md <<'EOF'

# AirScope

**Understand the air. See what comes next.**

AirScope is a bilingual air quality forecasting platform
focused on Germany and the United Kingdom.

## What does AirScope do?

- Displays recent air pollution measurements.
- Predicts future PM2.5 pollution levels using machine learning.
- Shows historical trends and monitoring stations on a map.
- Supports English and German.
- Explains air quality using simple, everyday language.

## Technology Stack

- Frontend: React, TypeScript, Material UI
- Backend: Python, FastAPI
- Machine Learning: Scikit-Learn, XGBoost
- Database: PostgreSQL (Supabase)
- Deployment: Cloudflare Pages and scheduled GitHub Actions

## Initial Scope

Countries: Germany and United Kingdom

Initial cities: Berlin and London

Main prediction target: PM2.5

Forecast horizons: 6, 12, and 24 hours

## Project Structure

- frontend/ - Website and user interface
- backend/ - API and backend services
- ml/ - Data processing and machine learning
- database/ - Database schema and migrations
- docs/ - Project documentation
- scripts/ - Commands for running workflows
- data/ - Local datasets
- reports/ - Evaluation results and research findings

## Development

This project is developed phase by phase, with meaningful
Git commits and separate development branches.

## Author

nik
EOF
