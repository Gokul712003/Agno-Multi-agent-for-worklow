# Multi Agent Workflow Manager

Agno-powered workflow automation system that integrates multiple digital workplace tools and services through specialized agents.

## Project Overview

This project implements a hierarchical multi-agent system designed to automate and streamline various workplace tasks across different platforms. It uses the Agno framework to create specialized agents that can interact with Google Workspace, communication tools, and more.

## Architecture

The system is structured with a master agent that orchestrates specialized agents for different services:

### Communication Agents
- **Slack Agent**: Manages Slack messaging and channel operations
- **Gmail Agent**: Handles email reading, writing, and sending
- **Zoom Agent**: Schedules and manages online meetings

### Google Workspace Agents
- **Google Docs Agent**: Creates and edits Google Documents
- **Google Sheets Agent**: Manages spreadsheets and data operations
- **Google Calendar Agent**: Handles calendar events and scheduling

### Support Agents
- **Email Writer**: Composes professional emails with appropriate structure and content
- **Writer Agent**: Generates creative content for documents
- **Data Entry Agent**: Specializes in spreadsheet data operations

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Gokul712003/workflow-agent.git
cd workflow-agent
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables by creating a `.env` file:
```
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
SLACK_TOKEN=your_slack_token
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
COMPOSIO_API_KEY=your_composio_api_key
```

4. Prepare service credentials:
   - Place Google API credentials in `credentials.json`
   - Set up Zoom API credentials
   - Configure Slack API access

## Usage

Run the application:

```bash
python final_prototype.py
```

This will start the Agno playground web interface where you can interact with the master agent. Example commands:

- "Schedule a team meeting for tomorrow at 3pm"
- "Send an email to john@example.com about the project update"
- "Create a document summarizing our quarterly results"
- "Make a spreadsheet to track project expenses"
- "Post a message in the #project Slack channel"

## Key Features

- **Integrated Workspace**: Single interface to control multiple workplace tools
- **Specialized Agents**: Purpose-built agents with domain-specific expertise
- **Tool Integration**: Seamless connection to Google Workspace, Slack, Zoom, and more
- **Natural Language Interface**: Control complex operations through simple text commands
- **Persistent Memory**: Agents remember context and previous interactions

## Dependencies

- Agno Framework
- Google API Python Client
- Slack SDK
- Zoom API Client
- Pydantic
- SQLite (for persistent storage)
- Composio Tools
