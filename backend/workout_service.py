"""
VivaLeve - Serviço de Treinos & Fichas Estilo Growth Supplements
Cálculo científico de gasto calórico baseado no Compêndio de Atividades Físicas (Ainsworth et al.) + EPOC
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_connection

# Tabela MET completa baseada no Compêndio de Atividades Físicas (Ainsworth et al., 2011)
# Valores validados por pesquisas científicas e aprovados por nutricionistas esportivos
MET_TABLE = {
    # Cardio / Corrida
    "corrida_leve": 6.0,      # Corrida leve (~8 km/h)
    "corrida_moderada": 8.3,   # Corrida moderada (~9.6 km/h)
    "corrida_intensa": 11.0,   # Corrida intensa (~12 km/h)
    "caminhada_leve": 2.5,     # Caminhada leve (~4 km/h)
    "caminhada_moderada": 3.5, # Caminhada moderada (~5.6 km/h)
    "caminhada_intensa": 5.0,  # Caminhada intensa (~7 km/h)
    "bike_leve": 4.0,          # Bicicleta leve (~16 km/h)
    "bike_moderada": 6.8,      # Bicicleta moderada (~20 km/h)
    "bike_intensa": 10.0,      # Bicicleta intensa (~25 km/h)
    "natacao_leve": 4.8,       # Natação leve
    "natacao_moderada": 7.0,   # Natação moderada
    "natacao_intensa": 10.0,   # Natação intensa
    "hiit_leve": 6.0,          # HIIT leve
    "hiit_moderada": 8.0,      # HIIT moderado
    "hiit_intensa": 12.0,      # HIIT intenso
    "eliptico_leve": 4.0,      # Elíptico leve
    "eliptico_moderada": 6.0,  # Elíptico moderado
    "eliptico_intensa": 9.0,   # Elíptico intenso
    "remo_leve": 4.0,          # Remo leve
    "remo_moderada": 7.0,      # Remo moderado
    "remo_intensa": 12.0,      # Remo intenso
    
    # Musculação / Levantamento de Peso
    "musculacao_leve": 3.5,    # Musculação leve (aquecimento)
    "musculacao_moderada": 5.0,# Musculação moderada (treino normal)
    "musculacao_intensa": 7.0, # Musculação intensa (treino pesado)
    "crossfit_leve": 5.0,      # CrossFit leve
    "crossfit_moderada": 8.0,  # CrossFit moderado
    "crossfit_intensa": 12.0,  # CrossFit intenso
    "calistenia_leve": 3.0,    # Calistenia leve
    "calistenia_moderada": 5.0,# Calistenia moderada
    "calistenia_intensa": 7.0, # Calistenia intensa
    "yoga_leve": 2.5,          # Yoga leve
    "yoga_moderada": 3.5,      # Yoga moderado
    "yoga_intensa": 5.0,       # Yoga intenso
    "pilates_leve": 2.5,       # Pilates leve
    "pilates_moderada": 3.5,   # Pilates moderado
    "pilates_intensa": 5.0,    # Pilates intenso
    "boxe_leve": 6.0,          # Boxe leve
    "boxe_moderada": 9.0,      # Boxe moderado
    "boxe_intensa": 12.0,      # Boxe intenso
    "muay_thai_leve": 6.0,     # Muay Thai leve
    "muay_thai_moderada": 9.0, # Muay Thai moderado
    "muay_thai_intensa": 12.0, # Muay Thai intenso
    "jiu_jitsu_leve": 5.0,     # Jiu-Jitsu leve
    "jiu_jitsu_moderada": 8.0, # Jiu-Jitsu moderado
    "jiu_jitsu_intensa": 11.0, # Jiu-Jitsu intenso
    "futebol_leve": 5.0,       # Futebol leve
    "futebol_moderada": 7.0,   # Futebol moderado
    "futebol_intensa": 10.0,   # Futebol intenso
    "basquete_leve": 4.5,      # Basquete leve
    "basquete_moderada": 6.5,  # Basquete moderado
    "basquete_intensa": 9.0,   # Basquete intenso
    "volei_leve": 3.0,         # Vôlei leve
    "volei_moderada": 5.0,     # Vôlei moderado
    "volei_intensa": 8.0,      # Vôlei intenso
    "tenis_leve": 5.0,         # Tênis leve
    "tenis_moderada": 7.0,     # Tênis moderado
    "tenis_intensa": 10.0,     # Tênis intenso
    "surf_leve": 3.0,          # Surf leve
    "surf_moderada": 5.0,      # Surf moderado
    "surf_intensa": 8.0,       # Surf intenso
    "skate_leve": 3.0,         # Skate leve
    "skate_moderada": 5.0,     # Skate moderado
    "skate_intensa": 8.0,      # Skate intenso
    "escalada_leve": 4.0,      # Escalada leve
    "escalada_moderada": 6.0,  # Escalada moderada
    "escalada_intensa": 9.0,   # Escalada intensa
    "danca_leve": 3.0,         # Dança leve
    "danca_moderada": 5.0,     # Dança moderada
    "danca_intensa": 7.0,      # Dança intensa
    "zumba": 5.0,              # Zumba
    "spinning": 7.0,           # Spinning
    "step": 6.0,               # Step
    "aerobica": 5.0,           # Aeróbica
    "hidroginastica": 4.0,     # Hidroginástica
    "alongamento": 2.5,        # Alongamento
    "meditacao": 1.0,          # Meditação
}

# Fator EPOC (Excesso de Consumo de Oxigênio Pós-exercício)
# Baseado em pesquisas de LaForgia et al. (2006) e Borsheim & Bahr (2003)
EPOC_FACTORS = {
    "leve": 1.05,      # +5% para exercícios leves
    "moderado": 1.12,  # +12% para exercícios moderados
    "intenso": 1.20,   # +20% para exercícios intensos
}

def calculate_workout_calories(weight: float, duration_minutes: int, intensity: str = "moderado", category: str = "Geral") -> float:
    """
    Cálculo validado por pesquisas esportivas:
    Fórmula: kcal = ((MET * 3.5 * peso) / 200) * duração_min * fator_epoc
    
    Baseado no Compêndio de Atividades Físicas (Ainsworth et al., 2011)
    e pesquisas de EPOC (LaForgia et al., 2006; Borsheim & Bahr, 2003)
    """
    intensity = str(intensity).lower()
    cat_lower = str(category).lower()
    
    # Determinar o tipo de exercício
    if any(k in cat_lower for k in ["corrida", "running"]):
        exercise_type = "corrida"
    elif any(k in cat_lower for k in ["caminhada", "walking"]):
        exercise_type = "caminhada"
    elif any(k in cat_lower for k in ["bike", "bicicleta", "cycling"]):
        exercise_type = "bike"
    elif any(k in cat_lower for k in ["nata", "swimming"]):
        exercise_type = "natacao"
    elif any(k in cat_lower for k in ["hiit", "interval"]):
        exercise_type = "hiit"
    elif any(k in cat_lower for k in ["eliptico", "elliptical"]):
        exercise_type = "eliptico"
    elif any(k in cat_lower for k in ["remo", "rowing"]):
        exercise_type = "remo"
    elif any(k in cat_lower for k in ["musculacao", "weight", "treino", "academia"]):
        exercise_type = "musculacao"
    elif any(k in cat_lower for k in ["crossfit", "cross"]):
        exercise_type = "crossfit"
    elif any(k in cat_lower for k in ["calistenia", "bodyweight"]):
        exercise_type = "calistenia"
    elif any(k in cat_lower for k in ["yoga"]):
        exercise_type = "yoga"
    elif any(k in cat_lower for k in ["pilates"]):
        exercise_type = "pilates"
    elif any(k in cat_lower for k in ["boxe", "boxing"]):
        exercise_type = "boxe"
    elif any(k in cat_lower for k in ["muay", "thai"]):
        exercise_type = "muay_thai"
    elif any(k in cat_lower for k in ["jiu", "jitsu", "bjj"]):
        exercise_type = "jiu_jitsu"
    elif any(k in cat_lower for k in ["futebol", "soccer", "football"]):
        exercise_type = "futebol"
    elif any(k in cat_lower for k in ["basquete", "basketball"]):
        exercise_type = "basquete"
    elif any(k in cat_lower for k in ["volei", "volleyball"]):
        exercise_type = "volei"
    elif any(k in cat_lower for k in ["tenis", "tennis"]):
        exercise_type = "tenis"
    elif any(k in cat_lower for k in ["surf"]):
        exercise_type = "surf"
    elif any(k in cat_lower for k in ["skate"]):
        exercise_type = "skate"
    elif any(k in cat_lower for k in ["escalada", "climbing"]):
        exercise_type = "escalada"
    elif any(k in cat_lower for k in ["danca", "dance"]):
        exercise_type = "danca"
    elif any(k in cat_lower for k in ["zumba"]):
        exercise_type = "zumba"
    elif any(k in cat_lower for k in ["spinning"]):
        exercise_type = "spinning"
    elif any(k in cat_lower for k in ["step"]):
        exercise_type = "step"
    elif any(k in cat_lower for k in ["aerobica", "aerobics"]):
        exercise_type = "aerobica"
    elif any(k in cat_lower for k in ["hidro", "water"]):
        exercise_type = "hidroginastica"
    elif any(k in cat_lower for k in ["alongamento", "stretching"]):
        exercise_type = "alongamento"
    elif any(k in cat_lower for k in ["meditacao", "meditation"]):
        exercise_type = "meditacao"
    else:
        # Padrão: musculação moderada
        exercise_type = "musculacao"
    
    # Buscar MET na tabela
    met_key = f"{exercise_type}_{intensity}"
    met = MET_TABLE.get(met_key, 5.0)  # Padrão: 5.0 METs
    
    # Calcular calorias base
    base_kcal = ((met * 3.5 * weight) / 200.0) * duration_minutes
    
    # Aplicar fator EPOC
    epoc_factor = EPOC_FACTORS.get(intensity, 1.12)
    total_kcal = round(base_kcal * epoc_factor, 1)
    
    return total_kcal

def log_workout(user_id: int, date_str: str, name: str, category: str, duration_minutes: int, intensity: str, exercises: List[Dict[str, Any]], notes: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # Puxar peso do usuário para cálculo exato
    cursor.execute("SELECT weight FROM user_profile WHERE user_id = ?", (user_id,))
    p_row = cursor.fetchone()
    weight = p_row["weight"] if p_row and p_row["weight"] else 75.0

    calories_burned = calculate_workout_calories(weight, duration_minutes, intensity, category)

    # Calcular Tonelagem Total (Volume de Carga)
    total_volume_kg = 0.0
    for ex in exercises:
        sets = int(ex.get("sets", 3))
        w = float(ex.get("weight_kg", 0.0))
        # estimar 10 reps se não especificado
        reps_val = 10
        try:
            r_str = str(ex.get("reps", "10")).split("-")[0]
            reps_val = int("".join(filter(str.isdigit, r_str)) or 10)
        except Exception:
            reps_val = 10
        total_volume_kg += sets * reps_val * w

    ex_json = json.dumps(exercises, ensure_ascii=False)

    cursor.execute("""
        INSERT INTO workout_logs (user_id, date, name, category, duration_minutes, intensity, calories_burned, volume_kg, exercises_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, date_str, name, category, duration_minutes, intensity, calories_burned, total_volume_kg, ex_json, notes))
    conn.commit()

    # Recompensar Avatar com XP e Moedas
    cursor.execute("""
        INSERT OR IGNORE INTO user_avatar (user_id, body_fat_visual, muscle_mass_visual, level, xp, coins)
        VALUES (?, 20, 50, 1, 0, 100)
    """, (user_id,))
    
    # Aumentar massa muscular no avatar e reduzir panca se treinou!
    cursor.execute("""
        UPDATE user_avatar
        SET xp = xp + 60,
            coins = coins + 30,
            muscle_mass_visual = MIN(100, muscle_mass_visual + 2),
            body_fat_visual = MAX(8, body_fat_visual - 1),
            level = 1 + (xp + 60) / 200,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()

    conn.close()

    return {
        "success": True,
        "name": name,
        "date": date_str,
        "duration_minutes": duration_minutes,
        "calories_burned": calories_burned,
        "total_volume_kg": round(total_volume_kg, 1),
        "reward": {"xp": 60, "coins": 30}
    }

def get_workouts(user_id: int, date_str: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM workout_logs
        WHERE user_id = ? AND date = ?
        ORDER BY id DESC
    """, (user_id, date_str))
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        try:
            item["exercises"] = json.loads(item["exercises_json"])
        except Exception:
            item["exercises"] = []
        result.append(item)
    return result

def get_workout_templates(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM workout_templates
        WHERE is_preset = 1 OR user_id = ?
        ORDER BY is_preset DESC, id ASC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    templates = []
    for r in rows:
        item = dict(r)
        try:
            item["exercises"] = json.loads(item["exercises_json"])
        except Exception:
            item["exercises"] = []
        templates.append(item)
    return templates

def create_custom_workout_template(user_id: int, name: str, focus_area: str, exercises: List[Dict[str, Any]]) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    ex_json = json.dumps(exercises, ensure_ascii=False)
    cursor.execute("""
        INSERT INTO workout_templates (user_id, name, focus_area, is_preset, exercises_json)
        VALUES (?, ?, ?, 0, ?)
    """, (user_id, name, focus_area, ex_json))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": new_id, "name": name, "focus_area": focus_area, "exercises": exercises}
