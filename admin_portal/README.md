# Admin Portal

This is the admin portal for the Sessions management system, built with React, TypeScript, and Vite.

## Features

- **Session Management**: Create, edit, and manage sessions with flexible scheduling
- **Signups & Waitlist**: Manage student signups and promote from waitlist to confirmed slots
- **Attendance**: Mark attendance for session occurrences with present/absent/excused status
- **Locations**: Manage session venues with contact information
- **School Terms**: Create and manage academic terms
- **Exports**: Export signups and attendance data as CSV files
- **Authentication**: Google OAuth integration for admin access

## Getting Started

```bash
# Install dependencies
pnpm install

# Start development server (runs on port 3001)
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

## Environment

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3001
- All admin endpoints require authentication via Google OAuth

## Architecture

- **Pages**: Main route components for different sections
- **Components**: Reusable UI components (Sidebar, Layout, ProtectedRoute)
- **Services**: API client and authentication service
- **Context**: React context for authentication state management
- **Types**: TypeScript interfaces for backend data models

## Key Pages

- `/login` - Google OAuth login
- `/dashboard` - Overview and stats
- `/sessions` - Session listing and management
- `/sessions/new` - Create new session
- `/sessions/:id` - View session details, signups, and occurrences
- `/sessions/:id/edit` - Edit session
- `/attendance/:occurrenceId` - Mark attendance
- `/locations` - Manage session locations
- `/terms` - Manage school terms
