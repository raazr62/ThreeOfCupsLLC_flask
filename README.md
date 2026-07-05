# Three of Cups, LLC

A full-stack Flask application that helps adults build meaningful, lasting friendships through intentional human matchmaking—not algorithms.

## 🌟 About the Project

Three of Cups, LLC is a friendship matchmaking platform where meaningful connections are formed through intentional pairings by a community weaver and therapist rather than automated algorithms.

In an age where digital connectivity has increased but genuine human connection has declined, Three of Cups exists to help people create authentic friendships based on compatibility, shared values, and life circumstances.

Unlike traditional social networking or dating platforms, every friendship match is thoughtfully curated by a human expert who understands relationship dynamics and community building.

---

## 🎯 Mission

Our mission is to combat loneliness by creating intentional, meaningful friendships through personalized human matchmaking.

We believe that genuine connection is a fundamental human need, and building lasting friendships requires empathy, understanding, and thoughtful curation—not machine learning algorithms.

---

## ✨ Features

- User Registration & Authentication
- User Profile Management
- Friendship Matchmaking
- Human-Curated Pairing Process
- Community Member Management
- Secure Authentication
- Responsive User Interface
- Admin Dashboard
- Email Notifications
- Contact & Support System

---

## 🛠 Tech Stack

### Backend

- Flask
- Flask SQLAlchemy
- Flask Migrate
- Flask Login / JWT Authentication
- WTForms (if applicable)
- RESTful APIs

### Frontend

- HTML5
- CSS3
- Bootstrap
- JavaScript

### Database

- PostgreSQL / MySQL / SQLite

### Other Tools

- Jinja2 Templates
- Gunicorn (Production)
- Nginx
- Docker (Optional)

---

## 📁 Project Structure

```text
three-of-cups/
│
├── app/
│   ├── auth/
│   ├── users/
│   ├── matchmaking/
│   ├── admin/
│   ├── templates/
│   ├── static/
│   ├── models/
│   ├── services/
│   ├── routes/
│   └── utils/
│
├── migrations/
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/three-of-cups.git

cd three-of-cups
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
FLASK_APP=run.py
FLASK_ENV=development

SECRET_KEY=your_secret_key

DATABASE_URL=your_database_url
```

### 5. Run Database Migrations

```bash
flask db upgrade
```

### 6. Run the Application

```bash
flask run
```

The application will be available at:

```
http://127.0.0.1:5000
```

---

## 🔒 Authentication

The application includes secure authentication features such as:

- User Registration
- Login
- Logout
- Password Security
- Session Management
- Protected Routes

---

## ❤️ How Matchmaking Works

Unlike platforms powered by recommendation algorithms, Three of Cups takes a human-first approach.

Each friendship match is thoughtfully curated by a community weaver and therapist who considers:

- Shared values
- Personal interests
- Communication styles
- Emotional compatibility
- Life stage
- Individual intentions
- Community goals

This intentional process creates opportunities for deeper, more authentic friendships.

---

## 📌 Future Enhancements

- Messaging System
- Event Management
- Group Communities
- Video Introductions
- Calendar Integration
- Notifications
- Mobile Application
- AI-assisted Admin Tools (without replacing human matchmaking)

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to your branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 💙 Philosophy

> Meaningful friendships aren't created by algorithms—they're cultivated through empathy, intention, and genuine human understanding.

Three of Cups exists to help people move beyond surface-level interactions and build authentic relationships that enrich their lives, one intentional pairing at a time.