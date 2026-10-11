import json
from datetime import datetime, timedelta
from database import get_connection

def get_cheat_status(user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cheat_settings WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    settings = cursor.fetchone()

    cursor.execute("SELECT * FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    profile = cursor.fetchone()

    # Checar refeições livres registradas na semana corrente (Segunda a Domingo)
    today = datetime.now()
    start_of_week = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    end_of_week = (today + timedelta(days=6 - today.weekday())).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM cheat_logs
        WHERE user_id = ? AND date >= ? AND date <= ?
        ORDER BY date DESC
    """, (user_id, start_of_week, end_of_week))
    week_logs = [dict(r) for r in cursor.fetchall()]

    for log in week_logs:
        if isinstance(log.get("damage_control"), str):
            try:
                log["damage_control"] = json.loads(log["damage_control"])
            except Exception:
                log["damage_control"] = {}

    daily_saving = settings["daily_bank_kcal"] if settings else 200.0
    meals_allowed = settings["meals_per_week"] if settings else 1
    cheat_active = bool(settings["cheat_mode_active"]) if settings else False
    active_date = settings["active_date"] if settings else ""

    # Se a data ativa for diferente de hoje, desativa automaticamente
    today_str = today.strftime("%Y-%m-%d")
    if cheat_active and active_date and active_date != today_str:
        cursor.execute("UPDATE cheat_settings SET cheat_mode_active = 0, active_date = ''")
        conn.commit()
        cheat_active = False

    target_cal = profile["target_calories"] if profile else 2000.0
    # Cálculo do banco: 5 dias de economia geram o saldo extra da refeição livre
    saved_week_kcal = daily_saving * 5
    cheat_day_budget = target_cal + saved_week_kcal

    conn.close()

    return {
        "cheat_mode_active": cheat_active,
        "active_date": active_date,
        "meals_allowed_per_week": meals_allowed,
        "meals_used_this_week": len(week_logs),
        "meals_remaining": max(0, meals_allowed - len(week_logs)),
        "daily_bank_saving_kcal": daily_saving,
        "adjusted_daily_target_kcal": max(1200.0, target_cal - daily_saving),
        "normal_daily_target_kcal": target_cal,
        "banked_calories_pool": saved_week_kcal,
        "cheat_day_calorie_allowance": cheat_day_budget,
        "week_start": start_of_week,
        "week_end": end_of_week,
        "recent_logs": week_logs,
        "damage_control_checklist": [
            {"id": "water", "title": "Hidratação Reforçada (+1000ml)", "desc": "Beba 1L extra de água para reduzir a retenção de sódio e ajudar na digestão.", "completed": False},
            {"id": "protein", "title": "Bater Meta de Proteína Primeiro", "desc": "Consuma suas proteínas magras antes da refeição livre para garantir saciedade.", "completed": False},
            {"id": "workout", "title": "Treino do Dia Cumprido", "desc": "Treinar pernas ou costas antes do dia do lixo direciona nutrientes para o músculo.", "completed": False},
            {"id": "mindful", "title": "Alimentação Consciente (Sem Celular)", "desc": "Aproveite a textura e o sabor da refeição devagar. Pare quando estiver saciado.", "completed": False},
            {"id": "zero_drink", "title": "Bebidas Sem Açúcar", "desc": "Não gaste calorias com refrigerante normal ou sucos concentrados; prefira água ou refri zero.", "completed": False}
        ]
    }

def toggle_cheat_mode(active: bool, user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d") if active else ""

    cursor.execute("""
        UPDATE cheat_settings
        SET cheat_mode_active = ?, active_date = ?
        WHERE user_id = ?
    """, (1 if active else 0, today_str, user_id))
    conn.commit()
    conn.close()

    return {"success": True, "cheat_mode_active": active, "date": today_str}

def update_cheat_settings(meals_per_week: int, daily_bank_kcal: float, user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cheat_settings
        SET meals_per_week = ?, daily_bank_kcal = ?
        WHERE user_id = ?
    """, (meals_per_week, daily_bank_kcal, user_id))
    conn.commit()
    conn.close()

    return {"success": True, "meals_per_week": meals_per_week, "daily_bank_kcal": daily_bank_kcal}

def log_cheat_meal(date: str, title: str, restaurant_name: str, estimated_calories: float, damage_control: dict, notes: str, user_id: int = 1):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO cheat_logs (user_id, date, title, restaurant_name, estimated_calories, damage_control, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        date or datetime.now().strftime("%Y-%m-%d"),
        title,
        restaurant_name,
        estimated_calories,
        json.dumps(damage_control or {}, ensure_ascii=False),
        notes
    ))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {"success": True, "id": log_id, "message": "Refeição livre registrada com sucesso!"}
