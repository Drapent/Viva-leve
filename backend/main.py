import os
import sys
import json
import math
import socket
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

# Garantir que o diretório backend esteja no sys.path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from database import get_connection, init_db
from seed_foods import seed_foods
from seed_restaurants import seed_restaurants
import cheat_day
import gemini_service
import auth
import gamification
import meal_planner

# Inicializar banco e sementes se necessário
init_db()
seed_foods()
seed_restaurants()

APP_VERSION = "2.1.0"
APP_TIMESTAMP = str(int(datetime.now().timestamp()))

app = FastAPI(
    title="VivaLeve API",
    description="Backend para aplicativo de nutrição, diário de macros, sistema de dia do lixo, restaurantes e auth",
    version=APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ----------------- MODELOS PYDANTIC -----------------

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    gender: Optional[str] = "M"
    age: Optional[int] = 28
    weight: Optional[float] = 75.0
    height: Optional[float] = 175.0
    activity_level: Optional[str] = "moderado"
    goal: Optional[str] = "emagrecer"
    pace: Optional[str] = "moderado"
    target_calories: Optional[float] = None
    target_protein: Optional[float] = None
    target_carbs: Optional[float] = None
    target_fat: Optional[float] = None
    target_water: Optional[float] = None

class CalculationPreviewRequest(BaseModel):
    weight: float
    height: float
    age: int
    gender: str = "M"
    activity_level: str = "moderado"
    goal: str = "emagrecer"
    pace: Optional[str] = "moderado"

class UserLogin(BaseModel):
    email: str
    password: str

class PasswordReset(BaseModel):
    email: str
    new_password: str

class QuickLoginRequest(BaseModel):
    user_id: int

class ProfileUpdate(BaseModel):
    user_id: Optional[int] = 1
    name: Optional[str] = None
    gender: Optional[str] = "M"
    age: Optional[int] = 28
    weight: Optional[float] = 75.0
    height: Optional[float] = 175.0
    activity_level: Optional[str] = "moderado"
    goal: Optional[str] = "emagrecer"
    target_calories: Optional[float] = None
    target_protein: Optional[float] = None
    target_carbs: Optional[float] = None
    target_fat: Optional[float] = None
    target_water: Optional[float] = None
    recalculate: Optional[bool] = False

class ApiKeyUpdate(BaseModel):
    user_id: Optional[int] = 1
    gemini_api_key: str

class FoodCreate(BaseModel):
    user_id: Optional[int] = 1
    name: str
    category: Optional[str] = "Personalizado"
    portion_name: Optional[str] = "100g"
    portion_grams: Optional[float] = 100.0
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = 0.0

class DiaryEntryCreate(BaseModel):
    user_id: Optional[int] = 1
    date: str
    meal_type: str # breakfast, lunch, snack, dinner, extra
    food_name: str
    amount_grams: float
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: Optional[float] = 0.0
    notes: Optional[str] = ""

class WaterLog(BaseModel):
    user_id: Optional[int] = 1
    date: str
    amount_ml: int

class WeightLog(BaseModel):
    user_id: Optional[int] = 1
    date: str
    weight: float
    notes: Optional[str] = ""

class CheatToggle(BaseModel):
    user_id: Optional[int] = 1
    active: bool

class CheatSettingsUpdate(BaseModel):
    user_id: Optional[int] = 1
    meals_per_week: int
    daily_bank_kcal: float

class CheatMealLog(BaseModel):
    user_id: Optional[int] = 1
    date: Optional[str] = None
    title: str
    restaurant_name: Optional[str] = ""
    estimated_calories: float
    damage_control: Optional[dict] = None
    notes: Optional[str] = ""

class MenuAnalysisRequest(BaseModel):
    restaurant_name: str
    menu_text: str

class ChatRequest(BaseModel):
    user_id: Optional[int] = 1
    message: str

class CheatChoiceRequest(BaseModel):
    user_id: Optional[int] = 1
    chosen_dish: str
    restaurant_name: Optional[str] = ""
    message: Optional[str] = ""

class MissionCompleteRequest(BaseModel):
    user_id: Optional[int] = 1

class FamilyCreate(BaseModel):
    user_id: Optional[int] = 1
    family_name: str

class FamilyJoin(BaseModel):
    user_id: Optional[int] = 1
    invite_code: str

class FamilyAddMember(BaseModel):
    admin_user_id: Optional[int] = 1
    member_name: str
    member_email: str
    password: Optional[str] = "123456"

class FamilyLeave(BaseModel):
    user_id: Optional[int] = 1

class MenuSwapDish(BaseModel):
    user_id: Optional[int] = 1
    mode: Optional[str] = "individual"
    day_key: str
    meal_type: str

class MenuLogDish(BaseModel):
    user_id: Optional[int] = 1
    date: str
    meal_type: str
    dish_name: str

# ----------------- FUNÇÕES AUXILIARES -----------------

def calculate_nutritional_targets(weight, height, age, gender, activity_level, goal, pace="moderado"):
    if not gender or str(gender).upper() == "F":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5

    multipliers = {
        "sedentario": 1.2,
        "leve": 1.375,
        "moderado": 1.55,
        "intenso": 1.725,
        "muito_intenso": 1.9
    }
    multiplier = multipliers.get(str(activity_level).lower(), 1.55)
    tdee = bmr * multiplier

    # Ritmo de déficit ou superávit
    deficit_map = {
        "suave": 300,
        "moderado": 500,
        "acelerado": 750
    }
    surplus_map = {
        "suave": 250,
        "moderado": 400,
        "acelerado": 600
    }
    
    pace_clean = str(pace or "moderado").lower()
    
    if goal == "emagrecer":
        cal_diff = -deficit_map.get(pace_clean, 500)
        target_calories = round(tdee + cal_diff)
    elif goal == "hipertrofia":
        cal_diff = surplus_map.get(pace_clean, 400)
        target_calories = round(tdee + cal_diff)
    else: # manter
        cal_diff = 0
        target_calories = round(tdee)

    # Limite mínimo seguro de calorias
    min_calories = 1200 if str(gender).upper() == "F" else 1400
    target_calories = max(min_calories, target_calories)

    # IMC e Classificação
    height_m = height / 100.0 if height > 3 else height
    bmi = round(weight / (height_m ** 2), 1) if height_m > 0 else 22.0
    if bmi < 18.5:
        bmi_status = "Abaixo do peso"
        bmi_color = "amber"
    elif bmi < 25.0:
        bmi_status = "Peso saudável"
        bmi_color = "emerald"
    elif bmi < 30.0:
        bmi_status = "Sobrepeso leve"
        bmi_color = "amber"
    elif bmi < 35.0:
        bmi_status = "Obesidade Grau I"
        bmi_color = "rose"
    else:
        bmi_status = "Obesidade Grau II/III"
        bmi_color = "rose"

    # Macronutrientes
    protein_mult = 2.0 if goal == "emagrecer" else (2.2 if goal == "hipertrofia" else 1.8)
    protein_g = round(weight * protein_mult)
    fat_g = round(weight * 0.85)
    cal_from_pf = (protein_g * 4) + (fat_g * 9)
    rem_cal = max(200, target_calories - cal_from_pf)
    carbs_g = round(rem_cal / 4)
    water_ml = round(weight * 38)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "cal_diff": cal_diff,
        "bmi": bmi,
        "bmi_status": bmi_status,
        "bmi_color": bmi_color,
        "target_calories": target_calories,
        "target_protein": protein_g,
        "target_carbs": carbs_g,
        "target_fat": fat_g,
        "target_water": water_ml
    }

def calculate_distance(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return None
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(r * c, 1)

# ----------------- ROTAS DO SISTEMA & APK & LIVE UPDATE -----------------

def get_public_url():
    if os.environ.get("VIVALEVE_PUBLIC_URL"):
        return os.environ.get("VIVALEVE_PUBLIC_URL").strip()
    
    pub_txt = Path(__file__).parent.parent / "public_url.txt"
    if pub_txt.exists():
        try:
            url = pub_txt.read_text(encoding="utf-8").strip()
            if url.startswith("https://"):
                return url
        except Exception:
            pass

    log_file = Path(__file__).parent.parent / "cloudflared.log"
    if log_file.exists():
        try:
            content = log_file.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", content)
            if match:
                return match.group(0)
        except Exception:
            pass

    return None

@app.get("/api/server-info")
def get_server_info():
    local_ip = get_local_ip()
    port = int(os.environ.get("VIVALEVE_PORT", os.environ.get("PORT", 8088)))
    pub_url = get_public_url()
    return {
        "version": APP_VERSION,
        "timestamp": APP_TIMESTAMP,
        "local_ip": local_ip,
        "port": port,
        "public_url": pub_url,
        "mobile_url": pub_url or f"http://{local_ip}:{port}",
        "name": "VivaLeve"
    }

@app.get("/api/version")
def get_app_version():
    return {
        "version": APP_VERSION,
        "timestamp": APP_TIMESTAMP
    }

# ----------------- ROTAS DE AUTENTICAÇÃO -----------------

@app.post("/api/auth/register")
def register(data: UserRegister):
    profile_data = {
        "gender": data.gender,
        "age": data.age,
        "weight": data.weight,
        "height": data.height,
        "activity_level": data.activity_level,
        "goal": data.goal,
        "pace": data.pace,
        "target_calories": data.target_calories,
        "target_protein": data.target_protein,
        "target_carbs": data.target_carbs,
        "target_fat": data.target_fat,
        "target_water": data.target_water
    }
    profile_data = {k: v for k, v in profile_data.items() if v is not None}
    
    # Se calorias ou macros não foram informados explicitamente mas os dados biométricos foram, calcula
    if "target_calories" not in profile_data and data.weight and data.height and data.age:
        calc = calculate_nutritional_targets(
            data.weight, data.height, data.age,
            data.gender or "M", data.activity_level or "moderado",
            data.goal or "emagrecer", data.pace or "moderado"
        )
        profile_data["target_calories"] = calc["target_calories"]
        profile_data["target_protein"] = calc["target_protein"]
        profile_data["target_carbs"] = calc["target_carbs"]
        profile_data["target_fat"] = calc["target_fat"]
        profile_data["target_water"] = calc["target_water"]

    res = auth.register_user(data.name, data.email, data.password, profile_data=profile_data)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.post("/api/profile/calculate-preview")
def preview_calculation(data: CalculationPreviewRequest):
    return calculate_nutritional_targets(
        data.weight, data.height, data.age,
        data.gender, data.activity_level, data.goal, data.pace
    )

@app.post("/api/auth/login")
def login(data: UserLogin):
    res = auth.login_user(data.email, data.password)
    if not res["success"]:
        raise HTTPException(status_code=401, detail=res["message"])
    return res

@app.post("/api/auth/reset-password")
def reset_password(data: PasswordReset):
    res = auth.reset_password(data.email, data.new_password)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@app.get("/api/auth/recent-account")
def get_recent_account():
    # Proteção de privacidade: contas nunca são transmitidas publicamente para outros aparelhos
    return {"success": False, "user": None}

@app.post("/api/auth/quick-login")
def quick_login(data: QuickLoginRequest):
    # Proteção de segurança: logins exigem validação de credenciais
    return {"success": False, "message": "Autenticação requer e-mail e senha."}

@app.get("/api/auth/me")
def get_current_user(user_id: int = Query(1)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return dict(row)

# ----------------- ROTAS DE PERFIL & METAS -----------------

@app.get("/api/profile")
def get_profile(user_id: int = Query(1)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cursor.fetchone()
    
    if not row:
        # Criar se não existir
        cursor.execute("""
            INSERT INTO user_profile (user_id, name, gender, age, weight, height, activity_level, goal, target_calories, target_protein, target_carbs, target_fat, target_water)
            VALUES (?, 'Usuário', 'M', 28, 75.0, 175.0, 'moderado', 'emagrecer', 1900, 150, 180, 55, 2600)
        """, (user_id,))
        conn.commit()
        cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()

    profile = dict(row)
    conn.close()

    ai_info = gemini_service.get_ai_info(user_id)
    profile["ia_info"] = ai_info
    profile["ia_integrada_ativa"] = ai_info["ia_integrada_ativa"]
    profile["ia_provedor"] = ai_info["ia_provedor"]
    profile["link_groq"] = ai_info["link_groq"]
    profile["link_gemini"] = ai_info["link_gemini"]
    profile["has_gemini_key"] = ai_info["tem_chave_personalizada"]
    profile["gemini_api_key_masked"] = ai_info["chave_mascarada"]

    calc = calculate_nutritional_targets(
        profile["weight"], profile["height"], profile["age"],
        profile["gender"], profile["activity_level"], profile["goal"]
    )
    profile["calculated"] = calc

    return profile

@app.post("/api/profile")
def update_profile(data: ProfileUpdate):
    user_id = data.user_id or 1
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    current = cursor.fetchone()
    if not current:
        conn.close()
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    current = dict(current)

    target_cal = data.target_calories
    target_p = data.target_protein
    target_c = data.target_carbs
    target_f = data.target_fat
    target_w = data.target_water

    if data.recalculate:
        calc = calculate_nutritional_targets(
            data.weight or current["weight"],
            data.height or current["height"],
            data.age or current["age"],
            data.gender or current["gender"],
            data.activity_level or current["activity_level"],
            data.goal or current["goal"]
        )
        target_cal = calc["target_calories"]
        target_p = calc["target_protein"]
        target_c = calc["target_carbs"]
        target_f = calc["target_fat"]
        target_w = calc["target_water"]

    cursor.execute("""
        UPDATE user_profile SET
            name = COALESCE(?, name),
            gender = COALESCE(?, gender),
            age = COALESCE(?, age),
            weight = COALESCE(?, weight),
            height = COALESCE(?, height),
            activity_level = COALESCE(?, activity_level),
            goal = COALESCE(?, goal),
            target_calories = COALESCE(?, target_calories),
            target_protein = COALESCE(?, target_protein),
            target_carbs = COALESCE(?, target_carbs),
            target_fat = COALESCE(?, target_fat),
            target_water = COALESCE(?, target_water),
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        data.name, data.gender, data.age, data.weight, data.height,
        data.activity_level, data.goal, target_cal, target_p, target_c,
        target_f, target_w, user_id
    ))

    today_str = datetime.now().strftime("%Y-%m-%d")
    if data.weight:
        cursor.execute("""
            INSERT INTO weight_entries (user_id, date, weight, notes)
            VALUES (?, ?, ?, 'Atualização de perfil')
        """, (user_id, today_str, data.weight))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Perfil atualizado com sucesso!"}

@app.post("/api/settings/api-key")
def update_api_key(data: ApiKeyUpdate):
    user_id = data.user_id or 1
    conn = get_connection()
    cursor = conn.cursor()
    key_val = data.gemini_api_key.strip() if data.gemini_api_key else ""
    cursor.execute("UPDATE user_profile SET gemini_api_key = ? WHERE user_id = ?", (key_val, user_id))
    conn.commit()
    conn.close()
    msg = "Chave de IA personalizada atualizada com sucesso!" if key_val else "IA Integrada padrão de fábrica reativada com sucesso!"
    return {"success": True, "message": msg, "has_custom_key": bool(key_val)}

# ----------------- ROTAS DE ALIMENTOS -----------------

@app.get("/api/foods")
def search_foods(q: Optional[str] = Query(None)):
    conn = get_connection()
    cursor = conn.cursor()
    if q and q.strip():
        term = f"%{q.strip()}%"
        cursor.execute("""
            SELECT * FROM foods
            WHERE name LIKE ? OR category LIKE ?
            ORDER BY is_custom DESC, name ASC
            LIMIT 40
        """, (term, term))
    else:
        cursor.execute("SELECT * FROM foods ORDER BY id ASC LIMIT 50")

    foods = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return foods

@app.post("/api/foods")
def create_custom_food(food: FoodCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO foods (user_id, name, category, portion_name, portion_grams, calories, protein, carbs, fat, fiber, is_custom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        food.user_id or 1, food.name, food.category, food.portion_name, food.portion_grams,
        food.calories, food.protein, food.carbs, food.fat, food.fiber
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"success": True, "id": new_id, "message": "Alimento cadastrado com sucesso!"}

# ----------------- ROTAS DE DIÁRIO -----------------

@app.get("/api/diary")
def get_diary(date: Optional[str] = None, user_id: int = Query(1)):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    profile_row = cursor.fetchone()
    if not profile_row:
        cursor.execute("SELECT * FROM user_profile ORDER BY id ASC LIMIT 1")
        profile_row = cursor.fetchone()
    profile = dict(profile_row)

    cursor.execute("""
        SELECT * FROM diary_entries
        WHERE user_id = ? AND date = ?
        ORDER BY id ASC
    """, (user_id, date))
    entries = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT SUM(amount_ml) as total_water FROM water_entries WHERE user_id = ? AND date = ?", (user_id, date))
    water_row = cursor.fetchone()
    total_water = water_row["total_water"] or 0

    cursor.execute("SELECT * FROM cheat_settings WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    cheat_st = cursor.fetchone()
    cheat_active = bool(cheat_st["cheat_mode_active"]) if cheat_st else False

    conn.close()

    meals = {
        "breakfast": {"title": "Café da Manhã", "icon": "☕", "items": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
        "lunch": {"title": "Almoço", "icon": "🥗", "items": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
        "snack": {"title": "Lanche da Tarde", "icon": "🍎", "items": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
        "dinner": {"title": "Jantar", "icon": "🍲", "items": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0},
        "extra": {"title": "Ceia / Snacks", "icon": "🌙", "items": [], "calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    }

    tot_cal, tot_p, tot_c, tot_f, tot_fib = 0.0, 0.0, 0.0, 0.0, 0.0

    for item in entries:
        m_type = item["meal_type"]
        if m_type in meals:
            meals[m_type]["items"].append(item)
            meals[m_type]["calories"] += item["calories"]
            meals[m_type]["protein"] += item["protein"]
            meals[m_type]["carbs"] += item["carbs"]
            meals[m_type]["fat"] += item["fat"]

        tot_cal += item["calories"]
        tot_p += item["protein"]
        tot_c += item["carbs"]
        tot_f += item["fat"]
        tot_fib += item["fiber"]

    daily_saving = cheat_st["daily_bank_kcal"] if cheat_st else 200.0
    effective_target_cal = (profile["target_calories"] + (daily_saving * 5)) if cheat_active else profile["target_calories"]
    remaining_cal = effective_target_cal - tot_cal

    return {
        "date": date,
        "cheat_mode_active": cheat_active,
        "summary": {
            "consumed_calories": round(tot_cal),
            "target_calories": round(effective_target_cal),
            "remaining_calories": round(remaining_cal),
            "percentage": min(150, round((tot_cal / effective_target_cal) * 100)) if effective_target_cal > 0 else 0,
            "protein": {"consumed": round(tot_p, 1), "target": profile["target_protein"]},
            "carbs": {"consumed": round(tot_c, 1), "target": profile["target_carbs"]},
            "fat": {"consumed": round(tot_f, 1), "target": profile["target_fat"]},
            "fiber": {"consumed": round(tot_fib, 1), "target": 25.0},
            "water": {"consumed": total_water, "target": profile["target_water"]}
        },
        "meals": meals
    }

@app.post("/api/diary")
def add_diary_entry(entry: DiaryEntryCreate):
    uid = entry.user_id or 1
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO diary_entries (user_id, date, meal_type, food_name, amount_grams, calories, protein, carbs, fat, fiber, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        uid, entry.date, entry.meal_type, entry.food_name, entry.amount_grams,
        entry.calories, entry.protein, entry.carbs, entry.fat, entry.fiber, entry.notes
    ))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Pontos de gamificação e atualização da sequência/foguinho
    try:
        gamification.award_points(uid, "meal_logged", 10, f"Refeição registrada: {entry.food_name}", entry.date)
        if entry.notes and "IA" in entry.notes:
            gamification.award_points(uid, "scanner_used", 15, "Foto analisada com IA", entry.date)
        gamification.get_or_create_streak(uid, entry.date)
    except Exception:
        pass

    return {"success": True, "id": new_id, "message": "Item adicionado ao diário com sucesso!"}

@app.delete("/api/diary/{entry_id}")
def delete_diary_entry(entry_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Item removido do diário."}

# ----------------- ROTAS DE ÁGUA -----------------

@app.post("/api/water")
def log_water(data: WaterLog):
    user_id = data.user_id or 1
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO water_entries (user_id, date, amount_ml)
        VALUES (?, ?, ?)
    """, (user_id, data.date, data.amount_ml))
    conn.commit()

    cursor.execute("SELECT SUM(amount_ml) as total FROM water_entries WHERE user_id = ? AND date = ?", (user_id, data.date))
    total = cursor.fetchone()["total"] or 0
    conn.close()

    # Pontos de gamificação e atualização de streak
    try:
        if total >= 2000:
            gamification.award_points(user_id, "water_goal_met", 20, "Meta diária de 2L de água batida!", data.date)
        gamification.get_or_create_streak(user_id, data.date)
    except Exception:
        pass

    return {"success": True, "total_water": total}

@app.delete("/api/water/reset")
def reset_water(date: str, user_id: int = Query(1)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM water_entries WHERE user_id = ? AND date = ?", (user_id, date))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Registro de água zerado para hoje."}

# ----------------- ROTAS DO DIA DO LIXO -----------------

@app.get("/api/cheat-day")
def get_cheat_day_info(user_id: int = Query(1)):
    return cheat_day.get_cheat_status(user_id=user_id)

@app.post("/api/cheat-day/toggle")
def toggle_cheat(data: CheatToggle):
    return cheat_day.toggle_cheat_mode(data.active, user_id=data.user_id or 1)

@app.post("/api/cheat-day/settings")
def update_cheat_settings(data: CheatSettingsUpdate):
    return cheat_day.update_cheat_settings(data.meals_per_week, data.daily_bank_kcal, user_id=data.user_id or 1)

@app.post("/api/cheat-day/log")
def log_cheat(data: CheatMealLog):
    return cheat_day.log_cheat_meal(
        data.date, data.title, data.restaurant_name,
        data.estimated_calories, data.damage_control, data.notes,
        user_id=data.user_id or 1
    )

# ----------------- ROTAS DE RESTAURANTES -----------------

@app.get("/api/restaurants")
def get_restaurants(
    q: Optional[str] = None,
    cuisine: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None
):
    conn = get_connection()
    cursor = conn.cursor()

    query_parts = []
    params = []

    if q and q.strip():
        query_parts.append("(name LIKE ? OR cuisine LIKE ? OR address LIKE ?)")
        term = f"%{q.strip()}%"
        params.extend([term, term, term])

    if cuisine and cuisine != "Todos":
        query_parts.append("category = ?")
        params.append(cuisine)

    where_clause = " WHERE " + " AND ".join(query_parts) if query_parts else ""
    cursor.execute(f"SELECT * FROM restaurants {where_clause} ORDER BY rating DESC", params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    result = []
    for r in rows:
        try:
            r["diet_dishes"] = json.loads(r["diet_dishes"])
        except Exception:
            r["diet_dishes"] = []
        try:
            r["cheat_dishes"] = json.loads(r["cheat_dishes"])
        except Exception:
            r["cheat_dishes"] = []

        if lat is not None and lng is not None and r["latitude"] and r["longitude"]:
            r["distance_km"] = calculate_distance(lat, lng, r["latitude"], r["longitude"])
        else:
            r["distance_km"] = None

        result.append(r)

    if lat is not None and lng is not None:
        result.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 9999)

    return result

@app.get("/api/restaurants/{rest_id}")
def get_restaurant_detail(rest_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants WHERE id = ?", (rest_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Restaurante não encontrado")

    data = dict(row)
    data["diet_dishes"] = json.loads(data["diet_dishes"])
    data["cheat_dishes"] = json.loads(data["cheat_dishes"])
    return data

@app.post("/api/restaurants/ai-analyze")
def ai_analyze_restaurant_menu(data: MenuAnalysisRequest):
    return gemini_service.analyze_restaurant_menu(data.restaurant_name, data.menu_text)

# ----------------- ROTAS DE IA & FOTO SCANNER -----------------

@app.get("/api/ai/info")
def get_ai_info_status(user_id: int = Query(1)):
    return gemini_service.get_ai_info(user_id)

@app.post("/api/ai/scan-food")
async def scan_food(file: UploadFile = File(...), user_id: int = Form(1)):
    contents = await file.read()
    mime_type = file.content_type or "image/jpeg"
    result = gemini_service.analyze_food_photo(contents, mime_type, user_id=user_id)
    return result

@app.post("/api/ai/chat")
def chat_with_nutri(data: ChatRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, goal, target_calories FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (data.user_id or 1,))
    row = cursor.fetchone()
    user_context = dict(row) if row else {}
    conn.close()

    return gemini_service.chat_nutrition(data.message, user_context, user_id=data.user_id or 1)

# ----------------- ROTAS DE PROGRESSO & PESO -----------------

@app.get("/api/stats/progress")
def get_progress_stats(user_id: int = Query(1)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM weight_entries WHERE user_id = ? ORDER BY date ASC, id ASC LIMIT 30", (user_id,))
    weights = [dict(r) for r in cursor.fetchall()]

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT date, SUM(calories) as total_calories
        FROM diary_entries
        WHERE user_id = ? AND date >= ?
        GROUP BY date
        ORDER BY date ASC
    """, (user_id, seven_days_ago))
    cal_history = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "weight_history": weights,
        "caloric_history": cal_history
    }

@app.post("/api/stats/weight")
def log_weight(data: WeightLog):
    user_id = data.user_id or 1
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO weight_entries (user_id, date, weight, notes)
        VALUES (?, ?, ?, ?)
    """, (user_id, data.date, data.weight, data.notes))

    cursor.execute("UPDATE user_profile SET weight = ? WHERE user_id = ?", (data.weight, user_id))

    conn.commit()
    conn.close()

    return {"success": True, "message": "Peso registrado com sucesso!"}

# ----------------- ROTAS DE GAMIFICAÇÃO & BATALHA FAMILIAR -----------------

@app.get("/api/gamification/streak")
def get_user_streak(user_id: int = Query(1), date: Optional[str] = None):
    return gamification.get_or_create_streak(user_id=user_id, today_str=date)

@app.get("/api/gamification/missions")
def get_user_missions(user_id: int = Query(1), date: Optional[str] = None):
    return gamification.get_or_generate_missions(user_id=user_id, date_str=date)

@app.post("/api/gamification/missions/{mission_id}/complete")
def complete_user_mission(mission_id: int, data: MissionCompleteRequest):
    return gamification.complete_mission_manually(user_id=data.user_id or 1, mission_id=mission_id)

@app.get("/api/gamification/family-battle")
def get_family_battle_status(user_id: int = Query(1), date: Optional[str] = None):
    return gamification.get_family_battle(current_user_id=user_id, date_str=date)

@app.post("/api/gamification/family-battle/cheat-choice")
def set_family_cheat_choice(data: CheatChoiceRequest):
    return gamification.save_family_cheat_choice(
        user_id=data.user_id or 1,
        chosen_dish=data.chosen_dish,
        restaurant_name=data.restaurant_name or "",
        message=data.message or ""
    )

# ----------------- ROTAS DE GESTÃO DA FAMÍLIA REAL -----------------

@app.get("/api/family")
def get_user_family_route(user_id: int = Query(1)):
    return gamification.get_user_family(user_id=user_id)

@app.post("/api/family/create")
def create_family_route(data: FamilyCreate):
    return gamification.create_family(user_id=data.user_id or 1, family_name=data.family_name)

@app.post("/api/family/join")
def join_family_route(data: FamilyJoin):
    return gamification.join_family(user_id=data.user_id or 1, invite_code=data.invite_code)

@app.post("/api/family/add-member")
def add_family_member_route(data: FamilyAddMember):
    return gamification.add_family_member_direct(
        admin_user_id=data.admin_user_id or 1,
        member_name=data.member_name,
        member_email=data.member_email,
        password=data.password or "123456"
    )

@app.post("/api/family/leave")
def leave_family_route(data: FamilyLeave):
    return gamification.leave_family(user_id=data.user_id or 1)

# ----------------- ROTAS DO ASSISTENTE DE CARDÁPIO SEMANAL -----------------

@app.get("/api/menu/weekly")
def get_weekly_menu(
    user_id: int = Query(1),
    mode: str = Query("individual"),
    force_regenerate: bool = Query(False)
):
    return meal_planner.get_or_create_weekly_menu(
        user_id=user_id,
        mode=mode,
        force_regenerate=force_regenerate
    )

@app.post("/api/menu/weekly/regenerate")
def regenerate_weekly_menu(
    user_id: int = Query(1),
    mode: str = Query("individual")
):
    return meal_planner.get_or_create_weekly_menu(
        user_id=user_id,
        mode=mode,
        force_regenerate=True
    )

@app.post("/api/menu/weekly/swap-dish")
def swap_weekly_menu_dish(data: MenuSwapDish):
    return meal_planner.swap_dish(
        user_id=data.user_id or 1,
        mode=data.mode or "individual",
        day_key=data.day_key,
        meal_type=data.meal_type
    )

@app.post("/api/menu/weekly/log-to-diary")
def log_dish_to_diary(data: MenuLogDish):
    return meal_planner.log_menu_dish_to_diary(
        user_id=data.user_id or 1,
        date_str=data.date,
        meal_type=data.meal_type,
        dish_name=data.dish_name
    )

# ----------------- ROTAS DE DOWNLOAD DO APK -----------------

@app.get("/download/apk")
def download_apk_file():
    apk_path = FRONTEND_DIR / "downloads" / "VivaLeve.apk"
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo APK não encontrado.")
    return FileResponse(
        path=str(apk_path),
        filename="VivaLeve.apk",
        media_type="application/vnd.android.package-archive"
    )

@app.get("/api/download/apk-info")
def get_apk_info():
    apk_path = FRONTEND_DIR / "downloads" / "VivaLeve.apk"
    exists = apk_path.exists()
    size_mb = round(apk_path.stat().st_size / (1024 * 1024), 1) if exists else 0
    return {
        "exists": exists,
        "filename": "VivaLeve.apk",
        "size_mb": size_mb,
        "download_url": "/download/apk",
        "version": APP_VERSION,
        "features": [
            "Instalação direta no celular Android",
            "Atualização automática via Wi-Fi",
            "Scanner de foto por IA ultra-rápido",
            "Ofensiva e Foguinho estilo Duolingo/TikTok",
            "Batalha Familiar do Dia do Lixo"
        ]
    }

# ----------------- ARQUIVOS ESTÁTICOS & FRONTEND -----------------

@app.get("/sw.js")
@app.get("/service-worker.js")
def serve_sw():
    sw_file = FRONTEND_DIR / "sw.js"
    if sw_file.exists():
        return FileResponse(
            sw_file, 
            media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"}
        )
    raise HTTPException(status_code=404, detail="Service worker não encontrado")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "VivaLeve API online. Frontend não encontrado em /frontend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
