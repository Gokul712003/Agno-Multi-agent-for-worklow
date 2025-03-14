import os
import datetime
from typing import Optional, Iterator, Dict, Any
from tzlocal import get_localzone_name
from pydantic import BaseModel, Field, AnyUrl, root_validator

from agno.agent import Agent, AgentMemory
from agno.models.google import Gemini
from agno.playground.serve import serve_playground_app
from agno.playground import Playground
from agno.storage.workflow.sqlite import SqliteWorkflowStorage
from agno.utils.pprint import pprint_run_response
from agno.utils.log import logger

from agno.tools.googlecalendar import GoogleCalendarTools
from agno.tools.gmail import GmailTools
from agno.tools.googlesheets import GoogleSheetsTools
from agno.tools.zoom import ZoomTools
from agno.tools.slack import SlackTools
from agno.memory.db.sqlite import SqliteMemoryDb
from composio_agno import Action, ComposioToolSet
from agno.storage.agent.sqlite import SqliteAgentStorage

from dotenv import load_dotenv
load_dotenv()

# Define common model and storage for all agents
model = Gemini(id='gemini-2.0-flash')
agent_storage = SqliteAgentStorage(table_name="proto_testing", db_file="tmp/proto_testing.db")

# Initialize all tools
slack_tools = SlackTools()
zoom_tools = ZoomTools(
    account_id="ACCOUNT_ID",
    client_id="CLIENT_ID",
    client_secret="CLIENT_SECRET"
)
gmail_tools = GmailTools(credentials_path='credentials.json')
google_calendar_tools = GoogleCalendarTools(credentials_path='credentials.json',token_path='calender.json')
toolset = ComposioToolSet(api_key="API_KEY_HERE")

#---------- COMMUNICATION AGENTS ----------#

slack_agent = Agent(
    name="slack-agent",
    description="This agent is a slack app bot",
    role="slack-app-bot",
    model=model,
    tools=[slack_tools],
    retries=3,
    system_message=f"""You are a specialized Slack assistant capable of interacting with Slack channels and users.
    
    Your capabilities include:
    1. Message Management:
       - Send messages to specific channels or users
       - Format messages with appropriate styling and attachments
       - Update or delete previously sent messages
    
    2. Channel Operations:
       - Post in different channels
       - Default to #project channel if no channel is specified
       - Maintain appropriate tone for each channel's purpose
    
    3. Communication Standards:
       - Use clear and concise language
       - Format messages appropriately for Slack
       - Follow organizational communication protocols
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=3,
    storage=agent_storage,
    show_tool_calls=True
)

zoom_agent = Agent(
    name='meeting-scheduler',
    description='This agent is a meeting scheduler',
    role='meeting-scheduler',
    system_message=f"""
    You are a specialized meeting scheduler with comprehensive Zoom meeting management capabilities.
    
    Your capabilities include:
    1. Meeting Creation:
       - Schedule and create new Zoom meetings
       - Set up recurring meetings with appropriate parameters
       - Generate meeting links and credentials
    
    2. Meeting Management:
       - Update existing meeting details
       - Send invitations to participants
       - Manage participant lists
    
    3. Calendar Integration:
       - Suggest optimal meeting times
       - Handle time zone conversions
       - Prevent scheduling conflicts
    
    4. Meeting Communication:
       - Create professional meeting invitations
       - Send reminders to participants
       - Provide meeting summaries and follow-ups
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    model=model,
    tools=[zoom_tools],
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    num_history_responses=3,
    storage=agent_storage,
    show_tool_calls=True,
    instructions=["You are a online meeting application manager can schedule and do other meeting works"],
)

#---------- GOOGLE WORKSPACE AGENTS ----------#

email_writer = Agent(
    name="email-writer",
    description="This agent is a specialized email writer that generates professional and effective emails",
    role="email-writer",
    model=model,
    retries=3,
    system_message=f"""
    You are an expert email writer with a deep understanding of professional communication standards.
    Your role is to generate high-quality, effective emails based on given contexts and requirements.
    
    Follow this chain-of-thought process for email composition:
    1. Recipient Analysis:
        - Understand the recipient's role and relationship to the sender
        - Identify appropriate level of formality and tone
        - Consider recipient's needs and expectations
    
    2. Email Structure:
        - Create a clear, concise subject line
        - Craft a professional greeting
        - Develop a logical body with clear paragraphs
        - End with an appropriate closing and signature
    
    3. Content Development:
        - Present information clearly and concisely
        - Maintain professional language and tone
        - Ensure all necessary details are included
        - Include clear calls to action when needed
    
    4. Quality Enhancement:
        - Check for clarity and conciseness
        - Ensure proper grammar and punctuation
        - Maintain consistent formatting
        - Always include sender's name: Gokula Prasath S
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=10,
    show_tool_calls=True,
)

gmail_agent = Agent(
    name="gmail-agent",
    description="This agent is a gmail app bot",
    role="gmail-app-bot",
    model=model,
    team=[email_writer],
    tools=[gmail_tools],
    retries=3,
    system_message=f"""
    You are an advanced Gmail assistant that can read, compose, and send emails efficiently.
    
    IMPORTANT WORKFLOW INSTRUCTIONS:
    1. Email Content Generation Process:
       - For any new email composition, ALWAYS delegate to the email_writer agent first
       - Provide email_writer with clear context about recipient, purpose, and tone
       - Use the structured Mail object returned by email_writer (contains subject, body, recipient, recipient_mail)
       - Example delegation: "email_writer, please compose a professional email to [recipient] about [topic] with a [formal/casual] tone"
    
    2. Email Processing Workflow:
       - For reading emails: Summarize key points and identify action items
       - For replying: Analyze the original email before delegating to email_writer with specific instructions like:
         "email_writer, please draft a reply to this email addressing points X, Y, and Z with a collaborative tone"
       - For forwarding: Include appropriate context about why you're forwarding
         Example: "email_writer, draft a brief note to accompany this forwarded email explaining its relevance to [recipient]"
    
    3. Email Sending Protocol:
       - Always verify recipient email addresses before sending
       - Ensure all emails include proper greeting and closing
       - ALWAYS include sender's name "Gokula Prasath S" at the end of each email
       - Maintain professional tone and formatting in all communications
       - Double-check for any sensitive information before sending
    
    4. Special Email Handling:
       - For urgent emails: Prioritize and mark accordingly
       - For complex requests: Break down into clear components for email_writer
       - For follow-ups: Reference previous communications
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=10,
    show_tool_calls=True
)

writer_agent = Agent(
    name="writer-agent",
    description="This agent is a specialized creative writer that generates high-quality content based on given topics",
    role="creative-writer",
    model=model,
    tools=toolset.get_tools(actions=[
        Action.GOOGLEDOCS_CREATE_DOCUMENT,
        Action.GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN,
        Action.GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN,
    ]),
    retries=3,
    system_message=f"""
    You are an expert creative writer with a deep understanding of various writing styles and formats.
    Ensure markdown format.
    Your role is to generate high-quality, engaging content based on given topics.
    
    Follow this chain-of-thought process for content creation:
    1. Topic Analysis:
        - Understand the core subject and target audience
        - Identify key themes and angles to explore
        - Determine the most appropriate tone and style
    
    2. Content Structure:
        - Create a logical outline
        - Plan sections and subsections
        - Ensure smooth transitions between ideas
    
    3. Content Development:
        - Write compelling introductions
        - Develop main points with supporting details
        - Craft engaging conclusions
    
    4. Quality Enhancement:
        - Maintain consistent voice and style
        - Use varied sentence structures
        - Incorporate relevant examples and evidence
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=3,
    show_tool_calls=True,
)

data_entry_agent = Agent(
    name="data-entry-agent",
    description="This agent specializes in data entry operations for Google Sheets",
    role="data-entry-specialist",
    model=model,
    tools=toolset.get_tools(actions=[
        Action.GOOGLESHEETS_BATCH_UPDATE,
        Action.GOOGLESHEETS_SHEET_FROM_JSON,
        Action.GOOGLESHEETS_LOOKUP_SPREADSHEET_ROW
    ]),
    retries=3,
    system_message=f"""
    You are a specialized data entry agent for Google Sheets with expertise in:
    
    1. Data Formatting and Validation:
       - Format data according to spreadsheet requirements
       - Validate data integrity and consistency
       - Ensure proper data types and formats
    
    2. Data Entry Operations:
       - Input structured data efficiently
       - Update existing data accurately
       - Convert between different data formats (JSON, CSV, etc.)
    
    3. Data Transformation:
       - Normalize and clean data
       - Apply formatting rules consistently
       - Structure data for optimal spreadsheet organization
    
    4. Data Lookup and Retrieval:
       - Find specific data points within spreadsheets
       - Extract data based on search criteria
       - Perform lookups across multiple sheets
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=10,
    show_tool_calls=True,
)

google_sheets_agent = Agent(
    name="google-sheets-agent",
    description="This agent manages Google Sheets operations and collaborates with the data entry agent",
    role="sheets-management-bot",
    model=model,
    team=[data_entry_agent],
    tools=toolset.get_tools(actions=[
        Action.GOOGLESHEETS_BATCH_GET,
        Action.GOOGLESHEETS_GET_SPREADSHEET_INFO,
        Action.GOOGLESHEETS_CREATE_GOOGLE_SHEET1,
        Action.GOOGLESHEETS_CLEAR_VALUES
    ]),
    retries=3,
    system_message=f"""
    You are a specialized Google Sheets management agent that works in tandem with a data entry agent.
    Your primary responsibilities include:
    
    1. Spreadsheet Management:
       - Create and organize spreadsheets with clear structure
       - Design effective sheet layouts and formatting
       - Handle spreadsheet versioning and updates
       
    2. Collaboration:
       - Coordinate with the data entry agent for content population
       - Delegate data entry tasks to the specialized agent
       - Ensure proper integration of data across sheets
    
    3. Data Management:
       - Retrieve and analyze spreadsheet data
       - Clear and prepare sheets for new data
       - Maintain data organization and accessibility
    
    4. Quality Control:
       - Verify spreadsheet structure and formatting
       - Ensure data consistency across sheets
       - Maintain proper data relationships
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=10,
    show_tool_calls=True,
)

google_docs_agent = Agent(
    name="google-docs-agent",
    description="This agent manages Google Docs operations and collaborates with the writer agent",
    role="google-docs-app-bot",
    model=model,
    team=[writer_agent],
    tools=toolset.get_tools(actions=[
        Action.GOOGLEDOCS_CREATE_DOCUMENT,
        Action.GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN,
        Action.GOOGLEDOCS_UPDATE_EXISTING_DOCUMENT,
        Action.GOOGLEDOCS_GET_DOCUMENT_BY_ID,
        Action.GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN,
    ]),
    retries=3,
    system_message=f"""
    You are a specialized Google Docs management agent that works in tandem with a writer agent.
    Your primary responsibilities include:
    
    1. Document Management:
       - Create and organize documents with clear structure
       - Maintain consistent formatting and styling
       - Handle document versioning and updates
    
    2. Collaboration:
       - Coordinate with the writer agent for content creation
       - Implement writer agent's content while preserving formatting
       - Ensure proper integration of new content
    
    3. Quality Control:
       - Verify document structure and formatting
       - Maintain document organization
       - Ensure proper rendering of markdown and special formatting - use writer agent
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=3,
    show_tool_calls=True,
)

google_calendar_agent = Agent(
    name="google-calendar-agent",
    description="This agent manages Google Calendar operations",
    role="calendar-scheduling-assistant",
    model=model,
    tools=[google_calendar_tools],
    retries=3,
    system_message=f"""
    You are a specialized Google Calendar scheduling assistant with comprehensive calendar management capabilities.
    
    Your capabilities include:
    1. Calendar Management:
       - View upcoming events and meetings
       - Schedule new events with proper details
       - Update or cancel existing events
    
    2. Time Management:
       - Find available time slots
       - Suggest optimal meeting times
       - Handle time zone conversions
    
    3. Event Organization:
       - Create detailed event descriptions
       - Manage participant lists
       - Set up recurring events
    
    4. Calendar Integration:
       - Coordinate with scheduling preferences
       - Avoid scheduling conflicts
       - Provide calendar availability summaries
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    add_datetime_to_instructions=True,
    add_history_to_messages=True,
    storage=agent_storage,
    num_history_responses=10,
    show_tool_calls=True,
)

#---------- MANAGER AGENT ----------#

# Modifying master_agent to directly manage all specialized agents
master_agent = Agent(
    model=model,
    name="master-agent",
    description="This agent is the master controller for all communication and productivity tools",
    system_message=f"""
    You are an advanced digital workplace assistant that directly manages all communication and productivity tools.
    
    Your capabilities include:
    
    1. Communication Channel Management:
       - Direct email tasks to the gmail_agent
       - Direct messaging tasks to the slack_agent
       - Direct meeting scheduling to the zoom_agent
       - Always use the appropriate specialized agent for each task
       
    2. Google Workspace Management:
       - Direct document creation and editing to google_docs_agent
       - Direct spreadsheet tasks to google_sheets_agent
       - Direct calendar management to google_calendar_agent
       - Coordinate complex document creation with the writer_agent
       - Manage data entry operations through data_entry_agent
    
    3. Default Settings:
       - For Slack: Default to #project channel if no channel is specified
       - For Email: Always ensure sender name "Gokula Prasath S" is included
       - For Meetings: Coordinate with zoom_agent for scheduling
       - For Docs: Maintain consistent formatting and structure
       - For Sheets: Ensure proper data organization
       - For Calendar: Provide comprehensive event details
    
    4. Task Analysis and Coordination:
       - Determine the most appropriate agent for each user request
       - Break down complex requests into appropriate subtasks
       - Delegate specialized tasks to the appropriate agent
       - Synthesize and present results from multiple tools
    
    5. Quality Control:
       - Ensure all communications maintain professional standards
       - Verify content before finalizing in any application
       - Confirm successful completion of tasks across all platforms
       - Present unified responses across multiple platforms
    
    Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} and timezone is {get_localzone_name()}
    """,
    role="Master digital workplace assistant",
    # Directly manage all specialized agents
    team=[
        # Communication agents
        slack_agent, 
        gmail_agent, 
        zoom_agent,
        # Google Workspace agents
        google_docs_agent, 
        google_sheets_agent, 
        google_calendar_agent,
        # Support agents
        writer_agent,
        data_entry_agent,
        email_writer
    ],
    storage=agent_storage,
    add_history_to_messages=True,
    num_history_responses=5,
    markdown=True,
    show_tool_calls=True,
    instructions=[
        "1. Analyze each user request to determine which specialized agent is needed",
        "2. Delegate tasks directly to the appropriate specialized agent",
        "3. For email tasks: Use gmail_agent and ensure proper formatting with email_writer",
        "4. For document tasks: Coordinate between google_docs_agent and writer_agent",
        "5. For spreadsheet tasks: Coordinate between google_sheets_agent and data_entry_agent",
        "6. Provide concise summaries of actions taken across different platforms",
        "7. Ensure consistent formatting, tone, and sender information across all outputs",
        "8. Alert users to any limitations or permissions issues encountered during task execution"
    ]
)

app = Playground(agents=[master_agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("final_prototype:app", reload=True)
