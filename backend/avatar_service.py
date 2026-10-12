"""
VivaLeve - Serviço de Avatar Evolutivo com Foto, Panca/Músculos Dinâmicos e Loja Fit
Transforma o cumprimento da dieta e dos treinos em uma jornada de RPG gamificada.
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from database import get_connection

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

    # Puxar dados de perfil para calcular estado corporal realista
    cursor.execute("SELECT weight, height, goal FROM user_profile WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()
    weight = prof["weight"] if prof and prof["weight"] else 75.0
    height = prof["height"] if prof and prof["height"] else 175.0
    goal = prof["goal"] if prof and prof["goal"] else "emagrecer"

    h_m = height / 100.0 if height > 3 else height
    bmi = weight / (h_m ** 2) if h_m > 0 else 23.0

    # Estimativa inicial visual de panca e músculo
    init_fat = min(50, max(12, int((bmi - 18) * 3.5)))
    init_muscle = 45 if goal != "hipertrofia" else 55

    if not row:
        cursor.execute("""
            INSERT INTO user_avatar (user_id, photo_url, body_fat_visual, muscle_mass_visual, level, xp, coins, equipped_outfit, equipped_accessory, equipped_aura, unlocked_items_json)
            VALUES (?, '', ?, ?, 1, 0, 150, 'regata_basica', 'shaker', 'nenhuma', '["regata_basica", "shaker", "nenhuma"]')
        """, (user_id, init_fat, init_muscle))
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
