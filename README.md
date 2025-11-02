# Health Economics Research App

A Streamlit application with MongoDB backend for health economics research and bill management.

## Features

- 🔍 **Research Query**: AI-powered health economics research using OpenAI GPT-4
- 📄 **Bills Manager**: Upload and manage bill files
- 📊 **Query History**: View past research queries and results
- 🗄️ **MongoDB Integration**: Persistent storage for queries and bills

## Prerequisites

- Docker
- Docker Compose
- OpenAI API Key

## Setup

1. Clone the repository and navigate to the project directory:
```bash
cd /Users/ignacio/agi-house-111 
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=your_actual_openai_api_key_here
```

## Running the Application

Start the application with Docker Compose:

```bash
docker-compose up --build
```

The application will be available at:
- **Streamlit App**: http://localhost:8501
- **MongoDB**: localhost:27017

## Services

### Streamlit Application
- Port: 8501
- Auto-reloads when code changes (volume mounted)
- Connected to MongoDB for data persistence

### MongoDB
- Port: 27017
- Persistent data storage with Docker volumes
- Database name: `app_database`

## Stopping the Application

```bash
docker-compose down
```

To remove volumes (deletes all data):
```bash
docker-compose down -v
```

## Development

The application code is mounted as a volume, so you can make changes to the code without rebuilding the container. Simply refresh your browser to see the changes.

## Project Structure

```
.
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Streamlit app container definition
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── oai_client.py          # OpenAI client example
├── .env.example           # Environment variables template
├── .dockerignore          # Docker ignore patterns
└── api/
    └── openapi.yaml       # API specification
```

## Database Collections

- **queries**: Stores research queries and their results
- **bills**: Stores uploaded bill metadata

## Troubleshooting

If MongoDB connection fails, ensure:
1. Docker containers are running: `docker ps`
2. Check logs: `docker-compose logs`
3. Verify network connectivity: `docker network ls`

If Streamlit doesn't load:
1. Check if port 8501 is available
2. Review container logs: `docker-compose logs streamlit`

