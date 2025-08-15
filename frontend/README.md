# Agent Hub Frontend

A modern React TypeScript frontend for the Agent2Agent (A2A) compliant agent registry system.

## Features

- **Agent Management**: View, filter, edit, and delete agents
- **Modern UI**: Built with Tailwind CSS for a clean, responsive design
- **Real-time Data**: Live agent status with heartbeat functionality
- **Search & Filter**: Find agents by name, owner, skill, and capabilities
- **Agent Invocation**: Get invoke URLs for registered agents
- **TypeScript**: Full type safety with auto-generated types from OpenAPI spec

## Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the backend** (if not already running):
   ```bash
   cd ../backend/app
   uvicorn src.main:app --reload
   ```

3. **Start the frontend**:
   ```bash
   npm start
   ```

4. **Open your browser** to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
src/
├── components/          # React components
│   ├── Layout.tsx      # Main layout wrapper
│   ├── AgentCard.tsx   # Individual agent display
│   └── AgentFilters.tsx # Filter controls
├── services/           # API layer
│   └── api.ts         # Backend API client
├── types/             # TypeScript definitions
│   └── agent.ts       # Agent-related types
└── App.tsx           # Main application component
```

## Configuration

The frontend connects to the backend API at `http://localhost:8000` by default. You can change this by:

1. Setting the `REACT_APP_API_URL` environment variable
2. Editing the `.env` file in the project root

## API Integration

The frontend integrates with all backend endpoints:

- `GET /agents` - List and filter agents
- `GET /agents/{id}` - Get specific agent details  
- `POST /agents/register` - Register new agents
- `PUT /agents/{id}` - Update agent information
- `DELETE /agents/{id}` - Remove agents
- `POST /agents/{id}/heartbeat` - Update agent heartbeat
- `GET /agents/{id}/invoke_url` - Get agent invocation details
- `GET /health` - Backend health check

## Technologies Used

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **date-fns** - Date formatting utilities

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run test suite
- `npm run eject` - Eject from Create React App

## Agent2Agent Protocol

This frontend is designed to work with A2A-compliant agents. The UI displays:

- Agent capabilities (streaming, notifications, etc.)
- Skills and their descriptions
- Protocol version compatibility
- Security requirements
- Provider information

For more information about the A2A protocol, see the backend documentation.

