"""
VivaLeve - Servico de Composicao Corporal (Balanca Digital / Bioimpedancia)

Concentra toda a matematica que converte a leitura de uma balanca digital
(peso, gordura, massa muscular, agua, osseo, gordura visceral, BMR) no
"modelo corporal 3D" que o Avatar3D desenha na tela.

Regras de negocio:
- A leitura mais recente da balanca e a fonte da verdade do avatar.
- Sem balanca, o modelo e derivado do peso do perfil + objetivo da dieta.
- Perder gordura e ganhar musculo mudam o avatar em direcoes opostas, de forma
  proporcional e estavel (nunca "pula" de um dia para o outro).
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from database import get_connection

# Limites fisiologicos usados para clampar leituras invalidas de hardware
BF_MIN, BF_MAX = 3.0, 65.0
MM_MIN, MM_MAX = 15.0, 75.0
WATER_MIN, WATER_MAX = 30.0, 75.0
BONE_MIN, BONE_MAX = 0.5, 6.0
VF_MIN, VF_MAX = 1.0, 40.0


def _clamp(value: Optional[float], low: float, high: float, fallback: float = 0.0) -> float:
    if value is None:
        return fallback
    try:
        v = float(value)
    except (TypeError, ValueError):
        return fallback
    if v != v:  # NaN
        return fallback
    return max(low, min(high, v))


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _round(value: float, digits: int = 1) -> float:
    return round(float(value), digits)


# ---------------------------------------------------------------------------
# LEITURA DA BALANCA
# ---------------------------------------------------------------------------
def save_scale_reading(
    user_id: int,
    date: str,
    data: Dict[str, Any],
    source: str = "manual",
    device_name: str = "",
) -> Dict[str, Any]:
    """Grava (ou sobrescreve) a leitura da balanca de um dia e deriva o avatar."""
    conn = get_connection()
    cursor = conn.cursor()

    # Peso só é válido se positivo: clamp com 0 zerado faria uma leitura "vazia"
    # virar 20 kg (o mínimo) e gerar um boneco irreal.
    raw_weight = data.get("weight")
    try:
        weight = float(raw_weight) if raw_weight is not None else 0.0
    except (TypeError, ValueError):
        weight = 0.0
    if weight <= 0:
        weight = 0.0
    elif weight < 20.0 or weight > 400.0:
        # Fora da faixaadulta plausível: ignora o peso, mas mantém o resto da leitura
        weight = 0.0

    body_fat = _clamp(data.get("body_fat"), BF_MIN, BF_MAX, None) if data.get("body_fat") is not None else None
    muscle_mass = _clamp(data.get("muscle_mass"), MM_MIN, MM_MAX, None) if data.get("muscle_mass") is not None else None
    water_pct = _clamp(data.get("water_pct"), WATER_MIN, WATER_MAX, None) if data.get("water_pct") is not None else None
    bone_mass = _clamp(data.get("bone_mass"), BONE_MIN, BONE_MAX, None) if data.get("bone_mass") is not None else None
    visceral_fat = _clamp(data.get("visceral_fat"), VF_MIN, VF_MAX, None) if data.get("visceral_fat") is not None else None
    basal = data.get("basal_metabolism")
    metabolic_age = data.get("metabolic_age")

    if weight <= 0 and body_fat is None and muscle_mass is None:
        conn.close()
        return {"success": False, "message": "Leitura invalida: informe ao menos o peso ou o percentual de gordura."}

    # Deriva campos ausentes a partir dos presentes
    if body_fat is None and muscle_mass is not None:
        body_fat = _round(_derive_body_fat_from_muscle(muscle_mass), 1)
    if muscle_mass is None and body_fat is not None:
        muscle_mass = _round(_derive_muscle_from_fat(body_fat), 1)
    if body_fat is None and weight > 0:
        bmi = _estimate_bmi(user_id, weight)
        body_fat = _round(_clamp(
            _estimate_body_fat_from_bmi(bmi, *_age_and_sex(user_id)), BF_MIN, BF_MAX, 25.0), 1)
        muscle_mass = _round(_derive_muscle_from_fat(body_fat), 1)
    if water_pct is None and body_fat is not None:
        water_pct = _round(max(WATER_MIN, 65.5 - (body_fat * 0.55)), 1)
    if bone_mass is None and weight > 0:
        bone_mass = _round(max(BONE_MIN, weight * 0.0125), 2)
    if basal is None and weight > 0 and muscle_mass is not None:
        basal = _round(_estimate_bmr_from_muscle(weight, muscle_mass, user_id), 0)

    bmi = _estimate_bmi(user_id, weight) if weight > 0 else None

    cursor.execute("""
        INSERT INTO body_composition
            (user_id, date, weight, body_fat, muscle_mass, water_pct, bone_mass,
             visceral_fat, basal_metabolism, metabolic_age, bmi, source, device_name, raw_payload)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            weight = excluded.weight,
            body_fat = excluded.body_fat,
            muscle_mass = excluded.muscle_mass,
            water_pct = excluded.water_pct,
            bone_mass = excluded.bone_mass,
            visceral_fat = excluded.visceral_fat,
            basal_metabolism = excluded.basal_metabolism,
            metabolic_age = excluded.metabolic_age,
            bmi = excluded.bmi,
            source = excluded.source,
            device_name = excluded.device_name,
            raw_payload = excluded.raw_payload
    """, (
        user_id, date, weight, body_fat, muscle_mass, water_pct, bone_mass,
        visceral_fat, basal, metabolic_age, bmi, source, device_name,
        json.dumps(data.get("raw", {}) or {}),
    ))

    # Mantem o peso do perfil e o grafico de peso em dia
    if weight > 0:
        cursor.execute("UPDATE user_profile SET weight = ? WHERE user_id = ?", (weight, user_id))
        cursor.execute(
            "INSERT INTO weight_entries (user_id, date, weight, notes) VALUES (?, ?, ?, ?)",
            (user_id, date, weight, "Leitura automatica da balanca"),
        )

    conn.commit()
    conn.close()

    model = build_body_model(user_id)
    return {
        "success": True,
        "message": "Leitura da balanca registrada! O avatar foi remodelado.",
        "body_model": model,
    }


def get_latest_reading(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM body_composition WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    try:
        data["raw"] = json.loads(data.pop("raw_payload", "{}") or "{}")
    except Exception:
        data["raw"] = {}
    return data


def get_history(user_id: int, limit: int = 90) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM body_composition WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit),
    )
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return list(reversed(rows))


# ---------------------------------------------------------------------------
# ESTIMATIVAS SEM BALANCA
# ---------------------------------------------------------------------------
def _get_profile(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}


def _estimate_bmi(user_id: int, weight: float) -> float:
    prof = _get_profile(user_id)
    height = float(prof.get("height") or 175.0)
    h_m = height / 100.0 if height > 3 else height
    if h_m <= 0:
        return 22.0
    return weight / (h_m ** 2)


def _derive_muscle_from_fat(body_fat: float) -> float:
    """
    Bióimpedância devolve *massa muscular esquelética* (% do peso corporal), que
    não é o mesmo que "tudo que não é gordura". A massa magra tem ~50% de músculo
    esquelético em adultos, então derivamos por esse fator.
    Ex.: 18% de gordura -> 41% de músculo (realista), e não 78%.
    """
    return _clamp((100.0 - body_fat) * 0.50, MM_MIN, MM_MAX, 40.0)


def _derive_body_fat_from_muscle(muscle_pct: float) -> float:
    """Operação inversa: quando a balança só devolve músculo."""
    return _clamp(100.0 - (muscle_pct / 0.50), BF_MIN, BF_MAX, 24.0)


def _age_and_sex(user_id: int) -> tuple:
    prof = _get_profile(user_id)
    return float(prof.get("age") or 28.0), (prof.get("gender") or "M") == "F"


def _estimate_body_fat_from_bmi(bmi: float, age: float = 28.0, is_female: bool = False) -> float:
    """
    Deurenberg, Seidell & van der Wouden (1991), Br J Nutr 65:105-114.

        GC% = 1,20*IMC + 0,23*idade - 10,8*sexo - 5,4

    sexo = 1 para homens e 0 para mulheres (homens tem ~10,8 pontos percentuais
    a menos de gordura no mesmo IMC). R2 = 0,79; erro padrao ~4,1 pontos.
    """
    sex = 0.0 if is_female else 1.0
    bf = (1.20 * bmi) + (0.23 * age) - (10.8 * sex) - 5.4
    return bf


def _estimate_bmr_from_muscle(weight: float, muscle_pct: float, user_id: int) -> float:
    """Katch-McArdle: BMR calculado a partir da massa magra (dado da balanca)."""
    prof = _get_profile(user_id)
    lean = weight * (muscle_pct / 100.0)
    bmr = 370.0 + (21.6 * lean)
    if (prof.get("gender") or "M") == "F":
        bmr *= 0.95
    return bmr


# ---------------------------------------------------------------------------
# MODELO CORPORAL 3D  (o coracao do avatar)
# ---------------------------------------------------------------------------
def build_body_model(user_id: int) -> Dict[str, Any]:
    """
    Traduz os dados corporais em parametros geometricos prontos para o Three.js.

    `bulk` e o indice que realmente move o boneco:
      -1.0 = Definitions/ extremely lean   (sem gordura, zero panca)
       0.0 = referencia (beleza media)
      +1.0 = obesity/ muito gordo (barriga, pescoco, coxas)
    A massa muscular e um multiplicador separado, que engrossa ombros, braco,
    peito e coxa SEM aumentar a barriga.
    """
    prof = _get_profile(user_id)
    reading = get_latest_reading(user_id)

    height_cm = float(prof.get("height") or 175.0)
    if height_cm > 3:
        pass
    else:
        height_cm = height_cm * 100.0

    goal = (prof.get("goal") or "emagrecer").lower()
    profile_weight = float(prof.get("weight") or 75.0)

    if reading and (reading.get("body_fat") or reading.get("weight")):
        weight = float(reading.get("weight") or profile_weight)
        body_fat = float(reading.get("body_fat") or 24.0)
        muscle_pct = float(reading.get("muscle_mass") or _derive_muscle_from_fat(body_fat))
        source = reading.get("source") or "balanca"
        measured = True
    else:
        age, is_female = _age_and_sex(user_id)
        bmi = _estimate_bmi(user_id, profile_weight)
        body_fat = _clamp(_estimate_body_fat_from_bmi(bmi, age, is_female), BF_MIN, BF_MAX, 25.0)
        muscle_pct = _derive_muscle_from_fat(body_fat)
        if goal == "hipertrofia":
            muscle_pct = _clamp(muscle_pct + 6.0, MM_MIN, MM_MAX)
        weight = profile_weight
        source = "estimativa"
        measured = False

    # Escala 1..4: quanto mais gordo, mais o corpo "cresce" (espessura, nao altura)
    bulk = _clamp((body_fat - 18.0) / 20.0, -1.0, 1.6)

    # Definiacao muscular: acima de ~34% ja e consideravelmente definido
    definition = _clamp((muscle_pct - 24.0) / 26.0, 0.0, 1.6)

    lean_mass = weight * (1.0 - body_fat / 100.0)
    fat_mass = weight - lean_mass

    # Altura proporcional do boneco: pessoas mais baixas ficam com o boneco menor
    height_scale = _clamp(height_cm / 175.0, 0.86, 1.14)

    # Biquinis: coxa e panturrilha grossam menos que a barriga (gordura subcutanea)
    thigh_extra = 0.25 + bulk * 0.55
    arm_extra = 0.35 + bulk * 0.65
    waist_extra = 0.2 + bulk * 1.15
    chest_extra = 0.3 + bulk * 0.6
    neck_extra = 0.15 + bulk * 0.85
    shoulder_extra = 0.1 + bulk * 0.3
    hip_extra = 0.2 + bulk * 0.7
    face_fullness = _clamp(0.2 + bulk * 0.55, -0.5, 1.4)

    ffmi = (lean_mass / (height_m(height_cm) ** 2)) if height_cm > 0 else 0.0

    return {
        "measured": measured,
        "source": source,
        "goal": goal,
        "weight": _round(weight),
        "height_cm": _round(height_cm),
        "body_fat": _round(body_fat),
        "muscle_pct": _round(muscle_pct),
        "lean_mass": _round(lean_mass),
        "fat_mass": _round(fat_mass),
        "water_pct": _round(reading.get("water_pct")) if reading and reading.get("water_pct") else None,
        "bone_mass": _round(reading.get("bone_mass"), 2) if reading and reading.get("bone_mass") else None,
        "visceral_fat": _round(reading.get("visceral_fat")) if reading and reading.get("visceral_fat") else None,
        "metabolic_age": reading.get("metabolic_age") if reading else None,
        "bmr": reading.get("basal_metabolism") if reading and reading.get("basal_metabolism") else None,
        "bmi": _round(_estimate_bmi(user_id, weight)),
        "ffmi": _round(ffmi, 2),
        "body_fat_class": body_fat_class(body_fat),
        "model": {
            "height_scale": _round(height_scale, 3),
            "bulk": _round(bulk, 3),
            "definition": _round(definition, 3),
            "muscle_scale": _round(0.55 + definition * 0.6, 3),
            "shoulder_extra": _round(shoulder_extra, 3),
            "chest_extra": _round(chest_extra, 3),
            "waist_extra": _round(waist_extra, 3),
            "hip_extra": _round(hip_extra, 3),
            "arm_extra": _round(arm_extra, 3),
            "thigh_extra": _round(thigh_extra, 3),
            "neck_extra": _round(neck_extra, 3),
            "face_fullness": _round(face_fullness, 3),
            "belly": _round(max(0.0, bulk), 3),
        },
    }


def height_m(height_cm: float) -> float:
    h = height_cm / 100.0 if height_cm > 3 else height_cm
    return max(0.5, h)


def body_fat_class(body_fat: float) -> str:
    if body_fat < 6:
        return " Gordura essencial"
    if body_fat < 14:
        return "Atleta"
    if body_fat < 18:
        return "Fitness"
    if body_fat < 25:
        return "Media"
    if body_fat < 32:
        return "Acima do peso"
    return "Obesidade"


# ---------------------------------------------------------------------------
# EVOLUCAO (o "boneco" mudando ao longo das semanas)
# ---------------------------------------------------------------------------
def record_snapshot(user_id: int, note: str = "") -> Dict[str, Any]:
    """Congela o estado corporal de hoje para alimentar a linha do tempo."""
    model = build_body_model(user_id)
    date = today_str()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT level FROM user_avatar WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    level = row["level"] if row else 1

    cursor.execute("""
        INSERT INTO avatar_snapshots (user_id, date, weight, body_fat, muscle_mass, lean_mass, avatar_bulk, level, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            weight = excluded.weight,
            body_fat = excluded.body_fat,
            muscle_mass = excluded.muscle_mass,
            lean_mass = excluded.lean_mass,
            avatar_bulk = excluded.avatar_bulk,
            level = excluded.level,
            note = excluded.note
    """, (
        user_id, date, model["weight"], model["body_fat"], model["muscle_pct"],
        model["lean_mass"], model["model"]["bulk"], level, note,
    ))
    conn.commit()
    conn.close()
    return model


def get_evolution(user_id: int, limit: int = 60) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM avatar_snapshots WHERE user_id = ? ORDER BY date ASC LIMIT ?",
        (user_id, limit),
    )
    rows = [dict(r) for r in cursor.fetchall()]

    # Garante pelo menos o estado atual na linha do tempo
    current = build_body_model(user_id)
    if not rows:
        rows = [{
            "date": today_str(), "weight": current["weight"], "body_fat": current["body_fat"],
            "muscle_mass": current["muscle_pct"], "lean_mass": current["lean_mass"],
            "avatar_bulk": current["model"]["bulk"], "level": 1, "note": "Estado atual",
        }]
    conn.close()

    first, last = rows[0], rows[-1]
    return {
        "timeline": rows,
        "current": current,
        "delta": {
            "weight": _round(last["weight"] - first["weight"]),
            "body_fat": _round(last["body_fat"] - first["body_fat"]),
            "muscle": _round(last["muscle_mass"] - first["muscle_mass"]),
            "lean_mass": _round(last["lean_mass"] - first["lean_mass"]),
        },
    }