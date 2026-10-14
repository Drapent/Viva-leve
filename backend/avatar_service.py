"""
VivaLeve - Serviço de Avatar Evolutivo 3D com Foto, Panca/Músculos Dinâmicos e Loja Fit
Transforma o cumprimento da dieta e dos treinos em uma jornada de RPG gamificada.

O avatar é um modelo 3D paramétrico: a leitura da balança define o volume do
corpo (gordura x músculo) e a análise da foto pela IA define o rosto.
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_connection
import body_metrics_service as body_metrics

AVATAR_SHOP_ITEMS = [
    # Roupas (Outfits)
    {"id": "regata_basica", "name": "Regata Básica Branca", "category": "outfit", "price": 0, "icon": "🎽", "desc": "Roupa inicial padrão de treino."},
    {"id": "regata_growth", "name": "Regata Cavada Growth Black", "category": "outfit", "price": 120, "icon": "⬛", "desc": "Destaca ombros largos e peitoral trincado."},
    {"id": "dry_fit_neon", "name": "Camiseta Dry-Fit Neon Pro", "category": "outfit", "price": 180, "icon": "🎽", "desc": "Tecnologia antitranspirante com brilho esportivo."},
    {"id": "moletom_oversized", "name": "Moletom Oversized Monstro", "category": "outfit", "price": 250, "icon": "🧥", "desc": "Estilo old school dos bodybuilders."},
    {"id": "top_fitness_pink", "name": "Top & Legging Power Pink", "category": "outfit", "price": 150, "icon": "👚", "desc": "Conjunto anatômico de alta compressão."},
    
    # Acessórios
    {"id": "shaker", "name": "Coqueteleira de Whey 700ml", "category": "accessory", "price": 0, "icon": "🥤", "desc": "Acessório indispensável pós-treino."},
    {"id": "luvas_treino", "name": "Luvas de Musculação em Couro", "category": "accessory", "price": 100, "icon": "🧤", "desc": "Mais pegada e proteção para puxadas e supinos."},
    {"id": "galao_agua_2l", "name": "Galão Monster 2.2 Litros", "category": "accessory", "price": 140, "icon": "🚰", "desc": "Garante hidratação nível atleta de ponta."},
    {"id": "cinto_lombar", "name": "Cinto de Força de Agachamento", "category": "accessory", "price": 200, "icon": "🥋", "desc": "Para quem pega cargas pesadas no agachamento e terra."},
    {"id": "tenis_dourado", "name": "Tênis Olímpico Dourado Fit", "category": "accessory", "price": 300, "icon": "👟", "desc": "Estabilidade e estilo máximo nos pés."},

    # Auras Especiais de Nível
    {"id": "nenhuma", "name": "Sem Aura", "category": "aura", "price": 0, "icon": "⚪", "desc": "Modo natural."},
    {"id": "aura_fogo", "name": "Aura de Fogo Queima-Calorias", "category": "aura", "price": 250, "icon": "🔥", "desc": "Efeito flamejante ativo ao redor do avatar."},
    {"id": "aura_raio", "name": "Aura Elétrica Super Saiyajin", "category": "aura", "price": 400, "icon": "⚡", "desc": "Raios pulsantes de pura energia e foco."},
    {"id": "aura_dourada", "name": "Aura Lendária Shape dos Deuses", "category": "aura", "price": 600, "icon": "✨", "desc": "Resplendor divino dos campeões consistentes."}
]

def get_or_create_avatar(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_avatar WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        # Estado corporal inicial vem do perfil + objetivo (ou da balança, se já houver leitura)
        model = body_metrics.build_body_model(user_id)
        cursor.execute("""
            INSERT INTO user_avatar (user_id, photo_url, body_fat_visual, muscle_mass_visual, level, xp, coins, equipped_outfit, equipped_accessory, equipped_aura, unlocked_items_json)
            VALUES (?, '', ?, ?, 1, 0, 150, 'regata_basica', 'shaker', 'nenhuma', '["regata_basica", "shaker", "nenhuma"]')
        """, (user_id, int(round(model["body_fat"])), int(round(model["muscle_pct"]))))
        conn.commit()
        cursor.execute("SELECT * FROM user_avatar WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    avatar_data = dict(row)
    try:
        avatar_data["unlocked_items"] = json.loads(avatar_data["unlocked_items_json"])
    except Exception:
        avatar_data["unlocked_items"] = ["regata_basica", "shaker", "nenhuma"]

    # Calcular nível com base no XP (a cada 200 XP = 1 nível)
    level = 1 + (avatar_data["xp"] // 200)
    avatar_data["level"] = level
    avatar_data["next_level_xp"] = level * 200
    avatar_data["xp_progress"] = avatar_data["xp"] % 200

    # Análise de evolução recente no diário e treinos
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) as c FROM diary_entries WHERE user_id = ? AND date = ?", (user_id, today))
    diary_count = cursor.fetchone()["c"]
    cursor.execute("SELECT COUNT(*) as c FROM workout_logs WHERE user_id = ? AND date = ?", (user_id, today))
    workout_count = cursor.fetchone()["c"]

    avatar_data["active_today"] = (diary_count > 0 or workout_count > 0)
    avatar_data["shop_catalog"] = AVATAR_SHOP_ITEMS

    conn.close()

    # Acopla o corpo (balança) e o rosto (IA) ao payload do avatar
    avatar_data["body"] = body_metrics.build_body_model(user_id)
    avatar_data["appearance"] = get_appearance(user_id)

    return avatar_data

def update_avatar_photo(user_id: int, photo_data_url: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_avatar
        SET photo_url = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (photo_data_url, user_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Foto do avatar atualizada com sucesso!"}


# ----------------- APARÊNCIA DO ROSTO (extraída da foto pela IA) -----------------
APPEARANCE_DEFAULTS = {
    "skin_tone": "#dfae86",
    "hair_color": "#2b1d16",
    "eye_color": "#3b2412",
    "face_shape": "quadrado",
    "hair_style": "curto",
    "facial_hair": "nenhum",
    "shoulder_width": "medio",
    "frame": "medio",
    "brow_thickness": 1.0,
    "face_roundness": 1.0,
    "jaw_width": 1.0,
    "ai_confidence": 0.0,
    "ai_engine": "",
}


def get_appearance(user_id: int) -> Dict[str, Any]:
    """Lê (ou cria) a aparência do avatar e devolve sempre todos os campos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM avatar_appearance WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("""
            INSERT INTO avatar_appearance (user_id, skin_tone, hair_color, eye_color, face_shape,
                                           hair_style, facial_hair, shoulder_width, frame)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, APPEARANCE_DEFAULTS["skin_tone"], APPEARANCE_DEFAULTS["hair_color"],
            APPEARANCE_DEFAULTS["eye_color"], APPEARANCE_DEFAULTS["face_shape"],
            APPEARANCE_DEFAULTS["hair_style"], APPEARANCE_DEFAULTS["facial_hair"],
            APPEARANCE_DEFAULTS["shoulder_width"], APPEARANCE_DEFAULTS["frame"],
        ))
        conn.commit()
        row = cursor.execute("SELECT * FROM avatar_appearance WHERE user_id = ?", (user_id,)).fetchone()

    conn.close()
    data = dict(row)
    for key, default in APPEARANCE_DEFAULTS.items():
        if data.get(key) is None:
            data[key] = default
    return data


def save_appearance(user_id: int, traits: Dict[str, Any], engine: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    get_appearance(user_id)  # garante que a linha exista
    cursor.execute("""
        UPDATE avatar_appearance SET
            skin_tone = ?, hair_color = ?, eye_color = ?, face_shape = ?,
            hair_style = ?, facial_hair = ?, shoulder_width = ?, frame = ?,
            brow_thickness = ?, face_roundness = ?, jaw_width = ?,
            ai_confidence = ?, ai_engine = ?, analyzed_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (
        traits.get("skin_tone"), traits.get("hair_color"), traits.get("eye_color"),
        traits.get("face_shape"), traits.get("hair_style"), traits.get("facial_hair"),
        traits.get("shoulder_width"), traits.get("frame"),
        traits.get("brow_thickness"), traits.get("face_roundness"), traits.get("jaw_width"),
        traits.get("confidence", 0.0), engine, user_id,
    ))
    conn.commit()
    conn.close()
    return get_appearance(user_id)


def get_appearance_json(user_id: int) -> str:
    """Serializa a aparência para ser embutida no payload do avatar."""
    return json.dumps(get_appearance(user_id))


def build_avatar_model(user_id: int) -> Dict[str, Any]:
    """
    Pacote completo que o renderizador 3D consome: corpo (balança) + rosto (IA) + equipamento.
    É a fonte única de verdade visual do avatar.
    """
    body = body_metrics.build_body_model(user_id)
    appearance = get_appearance(user_id)

    avatar = get_or_create_avatar(user_id)

    return {
        "user_id": user_id,
        "level": avatar.get("level", 1),
        "xp": avatar.get("xp", 0),
        "coins": avatar.get("coins", 0),
        "photo_url": avatar.get("photo_url", ""),
        "equipped": {
            "outfit": avatar.get("equipped_outfit", "regata_basica"),
            "accessory": avatar.get("equipped_accessory", "shaker"),
            "aura": avatar.get("equipped_aura", "nenhuma"),
        },
        "appearance": appearance,
        "body": body,
        "outfit_catalog": OUTFIT_STYLE_BY_ITEM,
    }


# Mapa item -> estilo de roupa que o 3D sabe renderizar.
# Sem entrada no mapa => o avatar veste a regata basica (malha).
OUTFIT_STYLE_BY_ITEM = {
    "regata_basica": {"kind": "tank", "color": "#f8fafc", "accent": "#e2e8f0"},
    "regata_growth": {"kind": "tank", "color": "#0b0b0f", "accent": "#f59e0b"},
    "dry_fit_neon": {"kind": "tee", "color": "#0f172a", "accent": "#22d3ee"},
    "moletom_oversized": {"kind": "hoodie", "color": "#312e81", "accent": "#a5b4fc"},
    "top_fitness_pink": {"kind": "sportsbra", "color": "#ec4899", "accent": "#fbcfe8"},
    # nomes antigos mantidos para nao quebrar avatares ja equipados
    "top_power_pink": {"kind": "sportsbra", "color": "#ec4899", "accent": "#fbcfe8"},
}

def buy_shop_item(user_id: int, item_id: str) -> Dict[str, Any]:
    item = next((i for i in AVATAR_SHOP_ITEMS if i["id"] == item_id), None)
    if not item:
        return {"success": False, "message": "Item não encontrado no catálogo."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT coins, unlocked_items_json FROM user_avatar WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": "Avatar não encontrado."}

    coins = row["coins"]
    try:
        unlocked = json.loads(row["unlocked_items_json"])
    except Exception:
        unlocked = ["regata_basica", "shaker", "nenhuma"]

    if item_id in unlocked:
        conn.close()
        return {"success": False, "message": "Você já possui este item desbloqueado!"}

    if coins < item["price"]:
        conn.close()
        return {"success": False, "message": f"Moedas insuficientes! Você tem {coins} e o item custa {item['price']} Moedas Fit."}

    new_coins = coins - item["price"]
    unlocked.append(item_id)

    cursor.execute("""
        UPDATE user_avatar
        SET coins = ?, unlocked_items_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (new_coins, json.dumps(unlocked), user_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"🎉 {item['name']} adquirido com sucesso!",
        "new_coins": new_coins,
        "item": item
    }

def _normalize_category(category: str) -> str:
    """O front usa PT-BR ('roupa'), a base usa EN ('outfit'). Aceita os dois."""
    c = (category or "").strip().lower()
    if c in ("roupa", "outfit"):
        return "outfit"
    if c in ("acessorio", "accessory"):
        return "accessory"
    if c == "aura":
        return "aura"
    return ""


def equip_item(user_id: int, item_id: str, category: str) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT unlocked_items_json FROM user_avatar WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": "Avatar não encontrado."}

    try:
        unlocked = json.loads(row["unlocked_items_json"])
    except Exception:
        unlocked = ["regata_basica", "shaker", "nenhuma"]

    if item_id not in unlocked:
        conn.close()
        return {"success": False, "message": "Você precisa desbloquear este item antes de equipar."}

    category = _normalize_category(category)
    if category == "outfit":
        cursor.execute("UPDATE user_avatar SET equipped_outfit = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (item_id, user_id))
    elif category == "accessory":
        cursor.execute("UPDATE user_avatar SET equipped_accessory = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (item_id, user_id))
    elif category == "aura":
        cursor.execute("UPDATE user_avatar SET equipped_aura = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (item_id, user_id))
    else:
        conn.close()
        return {"success": False, "message": "Categoria inválida."}

    conn.commit()
    conn.close()
    return {"success": True, "message": "Item equipado no avatar!"}
