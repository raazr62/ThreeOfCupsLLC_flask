# Three of Cups, LLC

A friendship matchmaking platform where meaningful connections are formed through intentional pairings by a community weaver and therapist—not an algorithm.

🌐 **Live Website:** https://threeofcupsllc.com

---

## About the Project

Three of Cups, LLC was created to address one of today's biggest social challenges: loneliness.

While technology has made it easier than ever to connect online, genuine and lasting friendships have become increasingly difficult to build. Three of Cups offers a more intentional approach by matching individuals through human insight rather than automated algorithms.

Instead of relying solely on data, every friendship match is thoughtfully curated by a community weaver and therapist who considers emotional compatibility, shared values, life circumstances, interests, and personal intentions.

The goal is simple:

> **Help people move from surface-level interactions to meaningful, long-lasting friendships.**

---

## Mission

Our mission is to build authentic communities by creating intentional friendships through human-centered matchmaking.

We believe that genuine connection isn't a luxury—it's a fundamental human need.

---

## Features

- Human-curated friendship matching
- Therapist-guided compatibility approach
- User registration and authentication
- Friendship application process
- Personalized user profiles
- Secure account management
- Contact and inquiry forms
- Responsive design for desktop and mobile
- Admin dashboard for managing users and matchmaking
- Email notifications
- Secure backend architecture

---

## Tech Stack

### Backend

- Flask
- Python
- SQLAlchemy
- Flask-Login
- Flask-WTF
- Jinja2

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap

### Database

- SQLite (Development)
- PostgreSQL / MySQL (Production, if applicable)

### Deployment

- Gunicorn
- Nginx
- Linux Server

---

## Project Structure

```text
project/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   ├── forms/
│   ├── utils/
│   └── __init__.py
│
├── migrations/
├── config.py
├── requirements.txt
├── run.py
└── README.md
```

---

## Installation

### Clone the repository

```bash
git clone https://github.com/yourusername/threeofcups.git
cd threeofcups
```

### Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file and configure the required variables.

Example:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
```

### Run the application

```bash
flask run
```

or

```bash
python run.py
```

The application will be available at:

```
http://127.0.0.1:5000
```

---

## Screenshots

You can add screenshots here.

```
screenshots/
├── home.png
├── profile.png
├── dashboard.png
```

---

## Why Three of Cups?

Unlike traditional social networking or friendship apps that depend on algorithms, Three of Cups focuses on intentional human connection.

Every match is thoughtfully created by a community weaver and therapist who understands that lasting friendships require:

- Shared values
- Emotional compatibility
- Similar life stages
- Mutual intentions
- Authentic connection

This human-first approach creates stronger and more meaningful relationships.

---

## Future Improvements

- Advanced user dashboard
- Video introductions
- Event management
- Community groups
- Messaging system
- Match history
- Notification center
- AI-assisted administrative tools
- Improved analytics

---

## Contributing

Contributions, suggestions, and improvements are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push the branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---

## License

This project is proprietary software developed for **Three of Cups, LLC**.

Unauthorized copying, modification, distribution, or commercial use without permission is prohibited.

---

## Contact

**Three of Cups, LLC**

🌐 Website: https://threeofcupsllc.com

---

*"Meaningful friendships begin with intentional connection."*