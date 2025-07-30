# FocusBot - Discord Focus Session Manager

## Overview

FocusBot is a Discord bot designed to manage collaborative focus sessions with timed intervals and member tracking. The application allows Discord users to create, join, and manage focus sessions across multiple servers with real-time status updates and automatic cleanup of expired sessions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Discord.py (Python-based Discord bot framework)
- **Language**: Python 3.8+
- **Architecture Pattern**: Event-driven bot architecture with slash commands
- **Session Management**: In-memory session storage with automatic cleanup mechanisms

### Bot Structure
- Single-file bot implementation (`main.py`)
- Slash command-based interaction system
- Event-driven message handling for Discord API
- Real-time session state management

## Key Components

### Command System
- **Slash Commands**: Modern Discord interaction system using application commands
- **Permission Controls**: Role-based access control for session management
- **Input Validation**: Duration limits (1-480 minutes) and user state validation

### Session Management
- **Focus Sessions**: Time-bound collaborative sessions with participant tracking
- **Multi-Server Support**: Isolated session management per Discord server
- **Automatic Cleanup**: Background processes to handle expired sessions
- **State Persistence**: In-memory storage for active sessions

### Core Commands
1. `/startfocus` - Creates new focus sessions with custom duration
2. `/joinfocus` - Allows users to join active sessions
3. `/leavefocus` - Enables users to leave sessions
4. `/status` - Provides real-time session information
5. `/endfocus` - Terminates sessions (creator/moderator only)

## Data Flow

### Session Lifecycle
1. **Creation**: User initiates session with `/startfocus <minutes>`
2. **Participation**: Users join/leave using dedicated commands
3. **Monitoring**: Real-time status updates via `/status`
4. **Termination**: Automatic expiry or manual termination via `/endfocus`

### State Management
- Session data stored in memory during bot runtime
- Participant lists maintained per session
- Timer mechanisms for automatic session expiration
- Server-specific session isolation

## External Dependencies

### Discord Integration
- **Discord.py Library**: Primary framework for Discord API interaction
- **Discord Developer Portal**: Bot token and application configuration
- **Discord Permissions**: Bot requires appropriate server permissions for slash commands

### Runtime Requirements
- **Python 3.8+**: Minimum runtime environment
- **Discord Bot Token**: Authentication for Discord API access

## Deployment Strategy

### Environment Setup
- Python virtual environment recommended
- Environment variables for bot token configuration
- Discord bot permissions: Send messages, use slash commands

### Hosting Considerations
- Continuous uptime required for session management
- Memory-based storage means sessions reset on bot restart
- Scalable for multiple Discord servers simultaneously

### Security Measures
- Token-based authentication with Discord API
- Permission-based command restrictions
- Input validation for all user commands

## Recent Changes (July 30, 2025)

### Latest Updates
- ✓ Implemented complete FocusBot based on user template
- ✓ Added enhanced features: automatic session cleanup, permission controls
- ✓ Added input validation (1-480 minutes limit)
- ✓ Added comprehensive status command with embeds
- ✓ Added leave focus functionality
- ✓ Bot successfully connected to Discord as "FocusBOT#7824"
- ✓ Added PostgreSQL database integration for persistent statistics
- ✓ Added personal statistics tracking (`/mystats` command)
- ✓ Added server leaderboard functionality (`/leaderboard` command)
- ✓ Added motivational messages based on focus time achievements
- ✓ Added weekly statistics tracking for users
- ✓ Ready for testing with all enhanced statistical features

## Development Notes

### Current Implementation
- Single-file architecture for simplicity (`main.py`)
- In-memory session storage (non-persistent)
- French language interface
- Enhanced error handling and user feedback
- Background task for automatic session cleanup
- Permission-based controls for ending sessions
- Rich embed status display

### Potential Enhancements
- Database integration for session persistence
- Advanced statistics and analytics
- Customizable session types and features
- Web dashboard for session management
