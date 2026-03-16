**Live Demo:** https://inventory-management-production-607b.up.railway.app/login

# Inventory Manager

A multi-user inventory management web app where users can track personal inventory, share it with others, and manage stock levels in real time.

---

## Tech Stack

- **Backend:** Python, Flask, Flask-Login, Flask-Migrate, Flask-Limiter
- **Database:** PostgreSQL, SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript
- **Auth:** JWT session-based auth with bcrypt password hashing

---

## Features

- User registration and login with secure password hashing
- Personal inventory management — add, edit, and delete items
- Restock minimum threshold — items flagged as low stock when quantity drops below minimum
- Share inventory with other users by username
- Shared users can view and edit items in shared inventories
- Owners can revoke access at any time
- Rate limiting on auth routes to prevent brute force attacks
- Database migrations managed with Flask-Migrate

---

## Project Structure

```
├── app/
│   ├── __init__.py        # App factory, extension initialization
│   ├── models.py          # Database models
│   ├── routes.py          # All API and page routes
│   └── validators.py      # Input validation
├── migrations/            # Database migration history
├── static/
│   ├── css/               # Stylesheets
│   └── js/                # Frontend JavaScript
├── templates/             # Jinja2 HTML templates
├── .env.example           # Environment variable reference
├── requirements.txt       # Python dependencies
└── run.py                 # App entry point
```

---

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/register` | Create a new account | No |
| POST | `/login` | Log in | No |
| GET | `/logout` | Log out | Yes |
| GET | `/getUserInventory` | Get current user's inventory | Yes |
| POST | `/add_row` | Add an inventory item | Yes |
| PUT | `/edit_row` | Edit an inventory item | Yes |
| DELETE | `/delete_row/<item_id>` | Delete an inventory item | Yes |
| POST | `/share_inv` | Share inventory with a user | Yes |
| DELETE | `/unshare_inv/<shared_id>` | Revoke a user's access | Yes |
| GET | `/sharedinv` | View shared inventories | Yes |
| PUT | `/edit_shared_row` | Edit item in shared inventory | Yes |
| GET | `/api/me` | Get current user info | Yes |

---

## Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/lugonzalez126/inventory-management.git
cd inventory-management
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
cp .env.example .env
```
Open `.env` and fill in your values.

**5. Create the database**
```bash
createdb inventory_db
flask db upgrade
```

**6. Run the app**
```bash
python run.py
```

The app will be running at `https://inventory-management-production-607b.up.railway.app/login`

---

## Environment Variables

See `.env.example` for required variables:

```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://localhost/inventory_db
```

Generate a secure secret key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
