import hashlib
import secrets
import sqlite3
from typing import Optional
from database import get_connection

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed, salt

def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    hashed, _ = hash_password(password, salt)
    return hashed == stored_hash

def register_user(name: str, email: str, password: str, profile_data: Optional[dict] = None):
    email = email.strip().lower()
    name = name.strip()
    
    if not name or not email or not password:
        return {"success": False, "message": "Preencha todos os campos obrigatórios."}
    
    if len(password) < 4:
        return {"success": False, "message": "A senha deve ter no mínimo 4 caracteres."}
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "Este e-mail já está cadastrado. Faça login."}
        
    pwd_hash, salt = hash_password(password)
    
    cursor.execute("""
        INSERT INTO users (name, email, password_hash, salt)
        VALUES (?, ?, ?, ?)
    """, (name, email, pwd_hash, salt))
    user_id = cursor.lastrowid

    p = profile_data or {}
    gender = p.get('gender', 'M')
    age = p.get('age', 28)
    weight = float(p.get('weight', 75.0))
    height = float(p.get('height', 175.0))
    activity_level = p.get('activity_level', 'moderado')
    goal = p.get('goal', 'emagrecer')
    target_cal = float(p.get('target_calories', 1900))
    target_p = float(p.get('target_protein', 150))
    target_c = float(p.get('target_carbs', 180))
    target_f = float(p.get('target_fat', 55))
    target_w = float(p.get('target_water', 2600))
    
    # Criar perfil personalizado para este usuário
    cursor.execute("""
        INSERT INTO user_profile (user_id, name, gender, age, weight, height, activity_level, goal, target_calories, target_protein, target_carbs, target_fat, target_water)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, gender, age, weight, height, activity_level, goal, target_cal, target_p, target_c, target_f, target_w))
    
    # Criar configurações padrão do dia do lixo
    cursor.execute("""
        INSERT INTO cheat_settings (user_id, meals_per_week, daily_bank_kcal, cheat_mode_active, active_date)
        VALUES (?, 1, 200.0, 0, '')
    """, (user_id,))

    # Iniciar streak do usuário com 1 dia e 2 proteções
    cursor.execute("""
        INSERT OR IGNORE INTO user_streaks (user_id, current_streak, longest_streak, last_active_date, freezes_remaining)
        VALUES (?, 1, 1, date('now'), 2)
    """, (user_id,))

    # Pontos de boas-vindas
    cursor.execute("""
        INSERT INTO user_points (user_id, date, action_type, points, description)
        VALUES (?, date('now'), 'account_created', 50, '🎉 Bem-vindo ao VivaLeve!')
    """, (user_id,))
    
    conn.commit()
    conn.close()
    
    # Gerar token simples de sessão
    token = f"{user_id}_{secrets.token_hex(16)}"
    
    return {
        "success": True,
        "message": "Conta criada com sucesso!",
        "token": token,
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }

def login_user(email: str, password: str):
    email = email.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return {"success": False, "message": "E-mail ou senha incorretos."}
        
    user_dict = dict(user)
    if not verify_password(password, user_dict["password_hash"], user_dict["salt"]):
        conn.close()
        return {"success": False, "message": "E-mail ou senha incorretos."}
        
    conn.close()
    
    token = f"{user_dict['id']}_{secrets.token_hex(16)}"
    
    return {
        "success": True,
        "message": "Login realizado com sucesso!",
        "token": token,
        "user": {
            "id": user_dict["id"],
            "name": user_dict["name"],
            "email": user_dict["email"]
        }
    }

def reset_password(email: str, new_password: str):
    email = email.strip().lower()
    if not email or not new_password:
        return {"success": False, "message": "Preencha o e-mail e a nova senha."}
    if len(new_password) < 4:
        return {"success": False, "message": "A nova senha deve ter no mínimo 4 caracteres."}
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return {"success": False, "message": "Nenhuma conta cadastrada com este e-mail."}
        
    user_dict = dict(user)
    pwd_hash, salt = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, user_dict["id"]))
    conn.commit()
    conn.close()
    
    token = f"{user_dict['id']}_{secrets.token_hex(16)}"
    return {
        "success": True,
        "message": "Senha redefinida com sucesso!",
        "token": token,
        "user": {
            "id": user_dict["id"],
            "name": user_dict["name"],
            "email": user_dict["email"]
        }
    }

