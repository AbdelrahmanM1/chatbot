# ChatBot with Flask and Google Search API

A modern chatbot application built with Flask that integrates Google Custom Search API for intelligent responses. Features user authentication, markdown support, and a beautiful UI.

## Features

- User authentication (login/register)
- Google Custom Search API integration
- Markdown support in chat messages
- Modern and responsive UI
- Real-time chat interface
- Secure user sessions
- SQLite database for user management

## Prerequisites

- Python 3.7 or higher
- Google Custom Search API credentials
- pip (Python package manager)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following variables:
```
SECRET_KEY=your-secret-key
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
```

## Getting Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Custom Search API
4. Create credentials (API key)
5. Create a Custom Search Engine and get the Search Engine ID (CSE ID)

## Running the Application

1. Make sure your virtual environment is activated
2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── templates/         # HTML templates
│   ├── base.html     # Base template
│   ├── index.html    # Landing page
│   ├── login.html    # Login page
│   ├── register.html # Registration page
│   └── chat.html     # Chat interface
└── chatbot.db        # SQLite database (created automatically)
```

## Security Notes

- Never commit your `.env` file or expose your API keys
- The application uses Flask-Login for secure session management
- Passwords are stored in the database (in a production environment, use proper password hashing)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 