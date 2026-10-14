"""
VivaLeve - Servico de Wearables (Relogio Digital / Smartwatch / Faixa de FC)

Recebe os dados vindos do relogio via Web Bluetooth (BLE) e os converte em
numeros que a dieta entende:
  - gasto calorico diario -> realimenta o TDEE e o saldo de calorias
  - passos, distancia, minutos ativos -> validam as metas e dao XP/coins
  - FC de repouso, media, maxima e SpO2 -> saude cardiovascular
  - horas de sono -> recuperacao e disciplina
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import get_connection

# Metas de referencia (valores OMS / ACSM). A UI pode sobrescrever por usuario.
DEFAULT_STEPS_GOAL = 10_000
DEFAULT_ACTIVE_MIN_GOAL = 30
DEFAULT_SLEEP_GOAL = 8.0


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _clamp(v: Optional[float], low: float, high: float, fallback: float = 0.0) -> float:
    if v is None:
        return fallback
    try:
        f = float(v)
    except (TypeError, ValueError):
        return fallback
    if f != f:
        return fallback
    return max(low, min(high, f))


# ---------------------------------------------------------------------------
# DISPOSITIVOS
# ---------------------------------------------------------------------------
def register_device(user_id: int, name: str, kind: str = "watch",
                    manufacturer: str = "", device_id: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO wearable_devices (user_id, name, kind, manufacturer, device_id, last_connected_at, last_sync_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (user_id, name, kind, manufacturer, device_id))
    conn.commit()
    device_pk = cursor.lastrowid
    conn.close()
    return {"success": True, "device_id": device_pk, "message": f"{name} pareado com sucesso!"}


def touch_device(user_id: int, device_id: Optional[int], name: str = "") -> None:
    conn = get_connection()
    cursor = conn.cursor()
    if device_id:
        cursor.execute(
            "UPDATE wearable_devices SET last_sync_at = CURRENT_TIMESTAMP, last_connected_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (device_id, user_id),
        )
    conn.commit()
    conn.close()


def list_devices(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wearable_devices WHERE user_id = ? ORDER BY last_sync_at DESC, id DESC",
        (user_id,),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def remove_device(user_id: int, device_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wearable_devices WHERE id = ? AND user_id = ?", (device_id, user_id))
    removed = cursor.rowcount
    conn.commit()
    conn.close()
    return {"success": removed > 0, "message": "Dispositivo removido." if removed else "Dispositivo nao encontrado."}


# ---------------------------------------------------------------------------
# SESSAO DIARIA
# ---------------------------------------------------------------------------
def log_session(user_id: int, data: Dict[str, Any], source: str = "manual",
                device_id: Optional[int] = None, device_name: str = "") -> Dict[str, Any]:
    """Grava (ou soma) os dados do relogio de um dia."""
    date = data.get("date") or today_str()

    calories = _clamp(data.get("calories_burned"), 0.0, 15_000.0, 0.0)
    active_cal = _clamp(data.get("active_calories"), 0.0, 10_000.0, max(0.0, calories * 0.7))
    steps = int(_clamp(data.get("steps"), 0, 200_000, 0))
    distance = _clamp(data.get("distance_km"), 0.0, 500.0, 0.0)
    resting_hr = data.get("resting_hr")
    avg_hr = data.get("avg_hr")
    max_hr = data.get("max_hr")
    active_minutes = int(_clamp(data.get("active_minutes"), 0, 1_440, 0))
    sleep_hours = _clamp(data.get("sleep_hours"), 0.0, 24.0, 0.0)
    spo2 = data.get("spo2")

    # Espera ativa do relogio: se veio FC media mas sem minutos ativos, infere
    if active_minutes == 0 and (avg_hr or calories):
        active_minutes = int(max(0, min(240, calories / 4.0)))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wearable_sessions WHERE user_id = ? AND date = ?", (user_id, date))
    old = cursor.fetchone()

    if old:
        # Soma com o que ja existia (varios envios do mesmo relogio no mesmo dia)
        merged = {
            "calories_burned": float(old["calories_burned"] or 0) + calories,
            "active_calories": float(old["active_calories"] or 0) + active_cal,
            "steps": int(old["steps"] or 0) + steps,
            "distance_km": float(old["distance_km"] or 0) + distance,
            "active_minutes": int(old["active_minutes"] or 0) + active_minutes,
            "sleep_hours": max(float(old["sleep_hours"] or 0), sleep_hours),
            "resting_hr": min([x for x in [old["resting_hr"], resting_hr] if x] or [None]) if (old["resting_hr"] and resting_hr) else (resting_hr or old["resting_hr"]),
            "avg_hr": max([x for x in [old["avg_hr"], avg_hr] if x] or [None]) if (old["avg_hr"] and avg_hr) else (avg_hr or old["avg_hr"]),
            "max_hr": max([x for x in [old["max_hr"], max_hr] if x] or [None]) if (old["max_hr"] and max_hr) else (max_hr or old["max_hr"]),
            "spo2": spo2 or old["spo2"],
        }
        cursor.execute("""
            UPDATE wearable_sessions SET
                calories_burned = ?, active_calories = ?, steps = ?, distance_km = ?,
                resting_hr = ?, avg_hr = ?, max_hr = ?, active_minutes = ?,
                sleep_hours = ?, spo2 = ?, source = ?, device_name = ?, device_id = ?
            WHERE id = ?
        """, (
            merged["calories_burned"], merged["active_calories"], merged["steps"], merged["distance_km"],
            merged["resting_hr"], merged["avg_hr"], merged["max_hr"], merged["active_minutes"],
            merged["sleep_hours"], merged["spo2"], source, device_name or old["device_name"], device_id or old["device_id"],
            old["id"],
        ))
    else:
        cursor.execute("""
            INSERT INTO wearable_sessions
                (user_id, date, device_id, device_name, calories_burned, active_calories, steps,
                 distance_km, resting_hr, avg_hr, max_hr, active_minutes, sleep_hours, spo2, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, date, device_id, device_name, calories, active_cal, steps, distance,
            resting_hr, avg_hr, max_hr, active_minutes, sleep_hours, spo2, source,
        ))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Dados do relogio sincronizados!",
        "summary": get_day_summary(user_id, date),
    }


def get_session(user_id: int, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wearable_sessions WHERE user_id = ? AND date = ?",
        (user_id, date or today_str()),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_history(user_id: int, days: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM wearable_sessions WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, days),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


def get_day_summary(user_id: int, date: Optional[str] = None) -> Dict[str, Any]:
    """Leitura de hoje + saldo calórico real versus a meta da dieta."""
    date = date or today_str()
    session = get_session(user_id, date)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT target_calories, activity_level FROM user_profile WHERE user_id = ?", (user_id,)
    )
    prof = cursor.fetchone()
    conn.close()

    target = float((prof["target_calories"] if prof else 1900) or 1900)

    consumed = 0.0
    try:
        conn2 = get_connection()
        cur2 = conn2.cursor()
        cur2.execute(
            "SELECT SUM(calories) as total FROM diary_entries WHERE user_id = ? AND date = ?",
            (user_id, date),
        )
        row2 = cur2.fetchone()
        consumed = float((row2["total"] if row2 else 0) or 0)
        conn2.close()
    except Exception:
        consumed = 0.0

    burned = float(session["calories_burned"]) if session else 0.0
    # O alvo de perda de peso ja embutido no calculo da dieta cobre o gasto basal.
    # O relogio entra como "adicional" apenas pelo excedente de atividade.
    bonus = max(0.0, burned - 250.0) * 0.5

    return {
        "date": date,
        "connected": bool(session),
        "device_name": session["device_name"] if session else "",
        "source": session["source"] if session else "",
        "calories_burned": round(burned),
        "active_calories": round(float(session["active_calories"])) if session else 0,
        "steps": int(session["steps"]) if session else 0,
        "distance_km": round(float(session["distance_km"]), 2) if session else 0.0,
        "resting_hr": session["resting_hr"] if session else None,
        "avg_hr": session["avg_hr"] if session else None,
        "max_hr": session["max_hr"] if session else None,
        "active_minutes": int(session["active_minutes"]) if session else 0,
        "sleep_hours": round(float(session["sleep_hours"]), 1) if session else 0.0,
        "spo2": session["spo2"] if session else None,
        "calories_consumed": round(consumed),
        "target_calories": round(target),
        "net_balance": round(consumed - burned),
        "diet_balance": round(consumed - (target + bonus)),
        "workout_bonus_calories": round(bonus),
        "goals": {
            "steps": DEFAULT_STEPS_GOAL,
            "active_minutes": DEFAULT_ACTIVE_MIN_GOAL,
            "sleep_hours": DEFAULT_SLEEP_GOAL,
        },
        "progress": {
            "steps": min(100, round(((session["steps"] if session else 0) / DEFAULT_STEPS_GOAL) * 100)),
            "active_minutes": min(100, round(((session["active_minutes"] if session else 0) / DEFAULT_ACTIVE_MIN_GOAL) * 100)),
            "sleep_hours": min(100, round(((float(session["sleep_hours"]) if session else 0) / DEFAULT_SLEEP_GOAL) * 100)),
            "calories_burned": min(100, round((burned / 2_500.0) * 100)),
        },
    }


def health_score(user_id: int) -> Dict[str, Any]:
    """Leitura simples de saude cardiovascular a partir do relogio."""
    session = get_session(user_id)
    if not session:
        return {"score": None, "message": "Conecte um relogio para medir sua saude cardiovascular."}

    score = 100
    notes = []

    resting = session["resting_hr"]
    if resting:
        if resting <= 60:
            score += 0
        elif resting <= 70:
            score -= 8
            notes.append("FC de repouso levemente alta (acima de 60 ideal).")
        else:
            score -= 20
            notes.append("FC de repouso acima de 70 bpm. improving com cardio e boa para voce.")

    active = session["active_minutes"] or 0
    if active < 15:
        score -= 20
        notes.append("Menos de 15 min de atividade hoje. Mire em 30 min.")
    elif active < 30:
        score -= 8
        notes.append("Atividade parcial. Faltam minutos para a meta diaria.")

    steps = session["steps"] or 0
    if steps < 4_000:
        score -= 15
        notes.append("Passos baixos hoje. Uma caminhada de 20 min ja resolve.")
    elif steps >= 10_000:
        notes.append("Meta de 10.000 passos batida. Excelente!")

    sleep = float(session["sleep_hours"] or 0)
    if sleep and sleep < 6:
        score -= 12
        notes.append("Sono abaixo de 6h compromete a recuperacao e o emagrecimento.")
    elif sleep >= 7.5:
        notes.append("Sono de qualidade. Hormona do crescimento working a seu favor.")

    spo2 = session["spo2"]
    if spo2 and spo2 < 95:
        score -= 15
        notes.append("SpO2 abaixo de 95%. Vale consultar um medico.")

    score = max(0, min(100, score))
    return {
        "score": score,
        "label": "Excelente" if score >= 85 else ("Bom" if score >= 70 else ("Regular" if score >= 50 else "Atencao")),
        "notes": notes,
    }