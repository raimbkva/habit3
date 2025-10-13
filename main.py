from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
from datetime import date

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ===== Временное хранение данных =====
USERS_FILE = "data/users.json"
HABITS_FILE = "data/habits.json"

# Функции для работы с JSON
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ===== Главная =====
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ===== Регистрация =====
@app.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register")
def register(request: Request, email: str = Form(...), password: str = Form(...)):
    users = load_json(USERS_FILE)
    if email in users:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email уже зарегистрирован"})
    users[email] = {"password": password}
    save_json(USERS_FILE, users)
    return RedirectResponse("/login", status_code=302)

# ===== Вход =====
@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users = load_json(USERS_FILE)
    if email in users and users[email]["password"] == password:
        response = RedirectResponse("/habits", status_code=302)
        response.set_cookie(key="user_email", value=email)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "Неверный email или пароль"})

# ===== Привычки =====
@app.get("/habits")
def habits_page(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse("/login")
    habits = load_json(HABITS_FILE)
    user_habits = habits.get(user_email, [])
    return templates.TemplateResponse("habits.html", {"request": request, "habits": user_habits})

@app.post("/add_habit")
def add_habit(request: Request, title: str = Form(...), description: str = Form(...)):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse("/login")
    habits = load_json(HABITS_FILE)
    if user_email not in habits:
        habits[user_email] = []
    habits[user_email].append({
        "title": title,
        "description": description,
        "start_date": str(date.today()),
        "streak": 0
    })
    save_json(HABITS_FILE, habits)
    return RedirectResponse("/habits", status_code=302)

# ===== Статистика =====
@app.get("/stats")
def stats_page(request: Request):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse("/login")
    habits = load_json(HABITS_FILE).get(user_email, [])
    total = len(habits)
    completed = sum(h.get("streak", 0) > 0 for h in habits)
    percent = int((completed / total) * 100) if total > 0 else 0
    return templates.TemplateResponse("stats.html", {"request": request, "habits": habits, "percent": percent})
