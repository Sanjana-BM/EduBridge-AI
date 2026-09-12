# 🎓 EduBridge AI

**EduBridge AI** is a web-based educational application developed using **Python and Django**. The project aims to provide an interactive platform for students by combining web technologies with AI-based educational capabilities.

## 🚀 Technologies Used

* **Python**
* **Django 5.2.7**
* **HTML5**
* **CSS3**
* **JavaScript**
* **SQLite**
* **ASGI**

## ✨ Features

* User-friendly educational web interface
* Django-based backend
* Database integration
* AI-based educational functionality
* Responsive web application
* Easy-to-use navigation

## 📂 Project Structure

```text
EduBridge-AI/
│
├── edubridge/
│   ├── manage.py
│   ├── edubridge/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   └── ...
│
├── requirements.txt
├── .gitignore
└── README.md
```

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
```

### 2. Navigate to the Project

```bash
cd edubridge
```

### 3. Create a Virtual Environment

```bash
python -m venv env
```

### 4. Activate the Virtual Environment

**Windows:**

```bash
env\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Apply Database Migrations

```bash
python manage.py migrate
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and visit:

```text
http://127.0.0.1:8000/
```

## 📦 Requirements

The project uses the following dependencies:

```text
asgiref==3.10.0
Django==5.2.7
sqlparse==0.5.3
tzdata==2025.2
```

## 🔒 GitHub Security

Do not upload sensitive information such as:

* API keys
* Passwords
* Django secret keys
* `.env` files
* Virtual environment files

Add the following to `.gitignore`:

```text
env/
__pycache__/
*.pyc
db.sqlite3
.env
```

## 🔮 Future Enhancements

* Personalized AI-based learning
* Student progress tracking
* Intelligent recommendations
* Enhanced educational resources
* User authentication and profiles
* Deployment to a cloud platform

## 👨‍💻 Author

**Sanjana BM**

## 📄 License

This project is developed for educational and learning purposes.
