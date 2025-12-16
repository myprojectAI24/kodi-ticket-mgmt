# Flask Ticket Management System for Kodi

A Flask-based web application with MVC architecture for managing Kodi user profiles and time-limited access tickets.

## Features

- **Admin Authentication**: Secure login system for admin users
- **Profile Management**: Create profiles (groups) for different users
- **Ticket System**: Auto-generated 4-digit PINs with time limits
- **Status Tracking**: Visual indication of active (green) vs used (red) tickets
- **Kodi Integration**: API endpoints for Kodi to register logins
- **Script Execution**: Automatic SSH script execution on ticket creation
- **Bootstrap UI**: Modern, responsive interface
- **SQLite Database**: Lightweight database storage

## Concepts

- **Profile**: A user group (e.g., "Kids", "Guest") that can have multiple tickets
- **Ticket**: A time-limited access code with:
  - Auto-generated unique 4-digit PIN
  - Length in minutes
  - Active status (green = unused, red = used)
  - Used timestamp when activated

## Project Structure (MVC)

```
project/
│
├── app.py                 # Main application file
├── models.py              # Models (Database layer)
├── controllers.py         # Controllers (Business logic)
├── templates/             # Views (Presentation layer)
│   ├── base.html
│   ├── login.html
│   ├── profiles.html
│   ├── profile_form.html
│   ├── profile_detail.html
│   └── ticket_form.html
├── log/                   # Execution logs
│   └── exec.log
├── requirements.txt       # Python dependencies
└── accounts.db           # SQLite database (auto-created)
```

## Installation

1. **Clone or create the project directory**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   Open your browser and go to `http://localhost:5000`

## Default Credentials

- **Username**: `admin`
- **Password**: `admin123`

## Usage

1. **Login**: Use the default admin credentials to log in
2. **Create Profile**: Create a profile for a user group (e.g., "Kids")
3. **Create Ticket**: 
   - Click on a profile to view details
   - Click "Create New Ticket"
   - Enter the length in minutes
   - System auto-generates a unique 4-digit PIN
   - Script `execute-on-kodi_set-passwd-per-profile.sh profile:PIN` is executed
   - Ticket appears GREEN (active) in the list
4. **Kodi Login**: User enters the PIN on Kodi to log in
5. **Register Login**: Kodi calls API endpoint to mark ticket as used
6. **Ticket Status**: Ticket turns RED after being used

## API Endpoints

### Register Login (Mark ticket as used)
```bash
POST /api/login
Content-Type: application/json

{
  "lock_code": "1234"
}
```

### Get Ticket Info
```bash
GET /api/ticket/<lock_code>
```

See `API_DOCUMENTATION.md` for complete API details and integration examples.

## Security Notes

- Change the `SECRET_KEY` in `app.py` for production
- Change the default admin password after first login
- Use environment variables for sensitive configuration
- Enable HTTPS in production

## Database Schema

### Admin Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Hashed password
- `created_at`: Timestamp

### Profile Table
- `id`: Primary key
- `name`: Unique profile name
- `created_at`: Timestamp
- `updated_at`: Timestamp

### Ticket Table
- `id`: Primary key
- `profile_id`: Foreign key to Profile
- `lock_code`: 4-digit PIN (unique, auto-generated)
- `length`: Duration in minutes
- `is_active`: Boolean (true=green/unused, false=red/used)
- `used_at`: Timestamp when ticket was used
- `created_at`: Timestamp

## Technologies Used

- **Flask**: Web framework
- **SQLAlchemy**: ORM for database operations
- **Bootstrap 5**: Frontend styling
- **SQLite**: Database
- **Werkzeug**: Password hashing