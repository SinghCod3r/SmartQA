# Smart QA Test Case Generator

A production-grade SaaS application that generates industry-standard test cases from software requirements using AI (Claude Sonnet).

## Features

- 🤖 **AI-Powered Generation** - Leverage Claude Sonnet to generate comprehensive test cases
- 📄 **Multi-Format Upload** - Support for PDF, DOCX, and TXT file uploads
- 📊 **Export Options** - Download test cases as Excel (.xlsx) or CSV
- 🎯 **Multi-Platform Support** - Generate tests for Web, Mobile, API, and Desktop apps
- 🔒 **Secure** - Password hashing with bcrypt, session token authentication
- 📜 **History Tracking** - Access all previously generated test cases

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Backend**: Python Flask
- **Database**: SQLite (MVP), structured for PostgreSQL migration
- **AI Engine**: Anthropic Claude API

## Project Structure

```
QA_test_Case_writeup/
├── backend/
│   ├── app.py                  # Main Flask application
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite database setup
│   │   └── user.py             # User model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py             # Login/Signup endpoints
│   │   ├── generate.py         # Test case generation
│   │   └── export.py           # Download/History endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # Claude Sonnet integration
│   │   └── file_parser.py      # PDF/DOCX/TXT extraction
│   └── utils/
│       ├── __init__.py
│       └── helpers.py          # Utility functions
├── frontend/
│   ├── index.html              # Landing page
│   ├── login.html              # Login page
│   ├── signup.html             # Signup page
│   ├── dashboard.html          # Main dashboard
│   └── static/
│       ├── css/
│       │   └── styles.css      # Main stylesheet
│       └── js/
│           ├── api.js          # API client
│           ├── auth.js         # Authentication logic
│           └── dashboard.js    # Dashboard functionality
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser

### 1. Clone/Setup the Project

```bash
cd e:\QA_test_Case_writeup
```

### 2. Set Up Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend` folder:

```env
# Required for AI-powered generation
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Change for production
SECRET_KEY=your_secret_key_here
FLASK_DEBUG=True
```

> **Note**: Without an ANTHROPIC_API_KEY, the application will generate mock test cases for demonstration purposes.

### 4. Run the Backend Server

```bash
# From the backend directory
python app.py
```

The API will be available at `http://localhost:5000`

### 5. Serve the Frontend

Option A - Using Python's built-in server:
```bash
# Open a new terminal, navigate to frontend
cd frontend
python -m http.server 8080
```

Option B - Simply open the HTML files directly in your browser:
```
Open: e:\QA_test_Case_writeup\frontend\index.html
```

### 6. Access the Application

- Landing Page: `http://localhost:8080/index.html`
- Login: `http://localhost:8080/login.html`
- Signup: `http://localhost:8080/signup.html`
- Dashboard: `http://localhost:8080/dashboard.html`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signup` | Create new user account |
| POST | `/api/login` | Authenticate user |
| POST | `/api/logout` | Invalidate session |
| GET | `/api/me` | Get current user info |

### Test Case Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate test cases from requirements |
| GET | `/api/generate/<id>` | Get specific generated file |

### Export & History

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/download/excel/<id>` | Download as Excel file |
| GET | `/api/download/csv/<id>` | Download as CSV file |
| GET | `/api/history` | Get user's generation history |
| DELETE | `/api/history/<id>` | Delete history item |

## Usage Guide

1. **Sign Up**: Create an account with your name, email, and password
2. **Log In**: Access your dashboard
3. **Enter Requirements**: Either:
   - Paste requirements text directly
   - Upload a PDF, DOCX, or TXT file
4. **Select Project Type**: Choose Web, Mobile, API, or Desktop
5. **Generate**: Click "Generate Test Cases" to create AI-powered test cases
6. **Export**: Download results as Excel or CSV
7. **History**: Access previous generations from the history section

## Test Cases Generated Include

- Test ID
- Module
- Test Scenario
- Preconditions
- Steps
- Test Data
- Expected Result
- Actual Result (blank for manual entry)
- Status (Pass/Fail/Pending)
- Priority (High/Medium/Low)
- Severity (Critical/Major/Minor/Trivial)
- Edge Cases

## Security Features

- **Password Hashing**: Bcrypt with salt
- **Session Tokens**: Secure random tokens with expiration
- **Input Validation**: Server-side validation for all inputs
- **CORS**: Configured for frontend origin
- **Error Handling**: Graceful error handling without exposing internals

## Future Enhancements

- [ ] PostgreSQL migration for production
- [ ] OAuth integration (Google, GitHub)
- [ ] Team collaboration features
- [ ] Test case templates
- [ ] Integration with test management tools (Jira, TestRail)
- [ ] Bulk file upload support

## Troubleshooting

### CORS Errors
Ensure both frontend and backend are running, and the frontend is served from `http://localhost:8080`.

### Database Errors
Delete `backend/database.db` and restart the server to recreate the database.

### API Key Not Working
Verify your Anthropic API key is correctly set in the `.env` file and the file is in the `backend` directory.

## License

MIT License - Feel free to use and modify for your needs.
