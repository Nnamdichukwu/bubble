# Twitter Sentiment Analysis Pipeline

This project implements a data pipeline that:
1. Extracts tweets using Twitter API
2. Performs sentiment analysis using OpenAI
3. Publishes data to Kafka
4. Loads and transforms data in Apache Pinot
5. Visualizes results using Apache Superset

## Running with Docker

1. Copy the environment template and fill in your credentials:
```bash
cp .env.template .env
```

2. Build and start all services:
```bash
docker-compose up -d
```

3. Create Pinot schema and table (after services are up):
```bash
# Create schema
curl -X POST -H "Content-Type: application/json" -d @config/pinot/schema.json http://localhost:9000/schemas

# Create table
curl -X POST -H "Content-Type: application/json" -d @config/pinot/table-config.json http://localhost:9000/tables
```

4. Access services:
- Dagster UI: http://localhost:3000
- Pinot Controller UI: http://localhost:9000
- Pinot Broker: http://localhost:8099

## Local Development Setup

1. Install Poetry (if not already installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Run the Dagster pipeline:
```bash
poetry run dagster dev
```

## Project Structure

```
.
├── config/
│   └── pinot/
│       ├── schema.json           # Pinot schema definition
│       ├── table-config.json     # Pinot table configuration
│       └── pinot-controller.conf # Pinot controller configuration
├── extract/
│   └── tweetloader.py           # Twitter API and sentiment analysis
├── orchestration/
│   └── pipeline.py              # Dagster pipeline definition
├── docker-compose.yml           # Docker services configuration
├── Dockerfile                   # Application container definition
├── pyproject.toml              # Poetry dependency management
└── README.md
```

## Apache Pinot Schema

The Twitter sentiment data is stored with the following schema:

```json
{
  "id": "LONG",
  "text": "STRING",
  "created_at": "TIMESTAMP",
  "lang": "STRING",
  "sentiment": "STRING",
  "public_metrics": "JSON"
}
```

## Development

This project uses Poetry for dependency management. Common commands:

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Activate virtual environment
poetry shell
```

## Docker Commands

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild a specific service
docker-compose build app

# Restart a specific service
docker-compose restart app
