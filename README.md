# Sessions Management System

A comprehensive session management platform for organizing and managing youth programs, classes, and activities. The system provides both public-facing session discovery and caregiver signup capabilities, along with powerful administrative tools for staff.

## 🌟 Features

### Public Features

- **Session Discovery**: Browse available sessions by region with search and filtering
- **Detailed Information**: View session schedules, locations, age requirements, and capacity
- **Calendar Export**: Download session calendars in .ics format for personal calendars

### Caregiver Portal

- **Magic Link Authentication**: Secure, passwordless login via email
- **Child Management**: Register and manage multiple children
- **Session Signups**: Enroll children in sessions with automatic age eligibility checking
- **Waitlist Management**: Automatic waitlist placement when sessions are full or age-ineligible
- **Session History**: Track enrollments and attendance

### Admin Portal

- **Google OAuth Authentication**: Secure staff login with Google accounts
- **Session Management**: Create and manage term-based and special sessions
- **Block/Term Configuration**: Set up school terms and special event blocks
- **Location Management**: Configure venues with maps and details
- **Attendance Tracking**: Take attendance with detailed roll calls
- **Student Management**: View student profiles, medical info, and signup history
- **Exclusion Dates**: Manage school holidays and closure dates
- **Calendar Overview**: Visual calendar of all session occurrences
- **Bulk Communications**: Send emails to session participants

## 🏗️ Architecture

The system consists of three main components:

- **Backend API** (Python/Litestar) - RESTful API with PostgreSQL database
- **Admin Portal** (React/TypeScript) - Staff administration interface  
- **Frontend** (Astro) - Public-facing session discovery and caregiver portal

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 22+ and pnpm (for local development)
- Python 3.13+ (for local backend development)
- PostgreSQL 16+ (for local development)

### Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/Tuhura-Tech/sessions.git
   cd sessions
   ```

2. **Backend Setup**

   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your configuration
   uv sync
   uv run alembic upgrade head
   uv run python main.py
   ```

3. **Admin Portal Setup**

   ```bash
   cd admin_portal
   cp .env.example .env
   pnpm install
   pnpm run dev
   ```

4. **Frontend Setup**

   ```bash
   cd frontend
   pnpm install
   pnpm run dev
   ```

### Docker Deployment

```bash
docker compose up -d
```

See `docker-compose.yml` for configuration details.

## 📦 Docker Images

Pre-built Docker images are available on GitHub Container Registry:

- `ghcr.io/yourusername/sessions-backend:latest`
- `ghcr.io/yourusername/sessions-admin:latest`
- `ghcr.io/yourusername/sessions-frontend:latest`

## 🔧 Configuration

### Backend Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/sessions
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/admin-auth/callback
```

See `backend/.env.example` for all available options.

### Frontend Configuration

Configure API endpoints in `admin_portal/.env` and `frontend/.env`.

## 🧪 Testing

### Backend Tests

```bash
cd backend
uv run pytest
```

### Frontend Tests (Playwright)

```bash
cd admin_portal
pnpm run test

cd frontend
pnpm run test:e2e
```

## 📚 API Documentation

The API is self-documenting with OpenAPI/Swagger:

- Development: <http://localhost:8000/docs>

## 🏛️ Database Schema

The system uses PostgreSQL with the following main entities:

- **Sessions** - Class/program definitions
- **SessionBlocks** - Time periods (terms, special events)
- **SessionOccurrences** - Individual class meetings
- **Signups** - Student enrollments
- **Children** - Student profiles
- **Caregivers** - Parent/guardian accounts
- **Staff** - Admin users
- **Locations** - Venue information
- **ExclusionDates** - Holidays/closures

Database migrations are managed with Alembic.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

This project is licensed under the AGPLv3 License - see the [LICENSE](LICENSE) file for details.

## 🔒 Security

For security concerns, please email <security@example.com> instead of using the issue tracker.

See [SECURITY.md](SECURITY.md) for our security policy.

## 🙏 Acknowledgments

Built with:

- [Litestar](https://litestar.dev/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [Astro](https://astro.build/) - Web framework
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Tailwind CSS](https://tailwindcss.com/) - Styling

## 📧 Support

For questions and support, please open an issue on GitHub.
