import sqlite3
import hashlib
import json
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "vivaleve.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela de Usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Perfil do Usuário
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        name TEXT DEFAULT 'Usuário',
        gender TEXT DEFAULT 'M',
        age INTEGER DEFAULT 28,
        weight REAL DEFAULT 75.0,
        height REAL DEFAULT 175.0,
        activity_level TEXT DEFAULT 'moderado',
        goal TEXT DEFAULT 'emagrecer',
        target_calories REAL DEFAULT 2000,
        target_protein REAL DEFAULT 150,
        target_carbs REAL DEFAULT 200,
        target_fat REAL DEFAULT 65,
        target_water REAL DEFAULT 2500,
        gemini_api_key TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Alimentos (Tabela TACO / Customizados)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'Geral',
        portion_name TEXT DEFAULT '100g',
        portion_grams REAL DEFAULT 100.0,
        calories REAL NOT NULL,
        protein REAL NOT NULL,
        carbs REAL NOT NULL,
        fat REAL NOT NULL,
        fiber REAL DEFAULT 0.0,
        is_custom INTEGER DEFAULT 0
    );
    """)

    # Diário de Refeições
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS diary_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        date TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        food_name TEXT NOT NULL,
        amount_grams REAL NOT NULL,
        calories REAL NOT NULL,
        protein REAL NOT NULL,
        carbs REAL NOT NULL,
        fat REAL NOT NULL,
        fiber REAL DEFAULT 0.0,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Consumo de Água
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS water_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        date TEXT NOT NULL,
        amount_ml INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Histórico de Peso
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weight_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        date TEXT NOT NULL,
        weight REAL NOT NULL,
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Configurações do Dia do Lixo
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cheat_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        meals_per_week INTEGER DEFAULT 1,
        daily_bank_kcal REAL DEFAULT 200.0,
        cheat_mode_active INTEGER DEFAULT 0,
        active_date TEXT DEFAULT ''
    );
    """)

    # Registro de Refeições Livres (Dia do Lixo)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cheat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        restaurant_name TEXT DEFAULT '',
        estimated_calories REAL DEFAULT 1200,
        damage_control TEXT DEFAULT '{}',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Restaurantes & Recomendações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        cuisine TEXT NOT NULL,
        address TEXT NOT NULL,
        latitude REAL DEFAULT 0.0,
        longitude REAL DEFAULT 0.0,
        price TEXT DEFAULT '$$',
        rating REAL DEFAULT 4.5,
        diet_dishes TEXT DEFAULT '[]',
        cheat_dishes TEXT DEFAULT '[]',
        tips TEXT DEFAULT ''
    );
    """)

    # Tabela de Sequência / Foguinho (Streaks estilo Duolingo / TikTok)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_streaks (
        user_id INTEGER PRIMARY KEY,
        current_streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0,
        last_active_date TEXT DEFAULT '',
        freezes_remaining INTEGER DEFAULT 2,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Missões Diárias Lúdicas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        mission_key TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        points INTEGER DEFAULT 20,
        completed INTEGER DEFAULT 0,
        completed_at TIMESTAMP
    );
    """)

    # Tabela de Pontos e Atividades da Gamificação
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        action_type TEXT NOT NULL,
        points INTEGER NOT NULL,
        description TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Escolha do Dia do Lixo da Família (Prêmio do Campeão da Semana)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS family_cheat_choice (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_key TEXT NOT NULL,
        family_id INTEGER DEFAULT 1,
        winner_user_id INTEGER NOT NULL,
        winner_name TEXT NOT NULL,
        chosen_dish TEXT NOT NULL,
        restaurant_name TEXT DEFAULT '',
        message TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Grupos Familiares
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS families (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        invite_code TEXT UNIQUE NOT NULL,
        created_by_user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Membros da Família
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        family_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL UNIQUE,
        role TEXT DEFAULT 'member',
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (family_id) REFERENCES families(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Tabela de Cardápios Semanais Inteligentes (Individual ou Família)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weekly_menus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        family_id INTEGER DEFAULT NULL,
        week_key TEXT NOT NULL,
        mode TEXT NOT NULL DEFAULT 'individual',
        menu_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Limpeza de usuários fictícios antigos das sementes de teste
    cursor.execute("DELETE FROM users WHERE email LIKE '%@familia.com'")
    cursor.execute("DELETE FROM user_points WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM user_streaks WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM user_profile WHERE user_id NOT IN (SELECT id FROM users)")


    # Migrações seguras: garantir que a coluna user_id exista em todas as tabelas
    tables_to_check = ['user_profile', 'foods', 'diary_entries', 'water_entries', 'weight_entries', 'cheat_settings', 'cheat_logs']
    for table in tables_to_check:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'user_id' not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT 1")

    # Migração segura para family_cheat_choice
    cursor.execute("PRAGMA table_info(family_cheat_choice)")
    choice_cols = [row['name'] for row in cursor.fetchall()]
    if 'family_id' not in choice_cols:
        cursor.execute("ALTER TABLE family_cheat_choice ADD COLUMN family_id INTEGER DEFAULT NULL")

    # Criar usuário padrão se a tabela users estiver vazia
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        salt = "a1b2c3d4e5f67890"
        pwd_hash = hashlib.sha256(("123456" + salt).encode('utf-8')).hexdigest()
        cursor.execute("""
            INSERT INTO users (id, name, email, password_hash, salt)
            VALUES (1, 'Usuário VivaLeve', 'usuario@vivaleve.com', ?, ?)
        """, (pwd_hash, salt))

    # Garantir que o perfil padrão para user_id = 1 existe
    cursor.execute("SELECT COUNT(*) as count FROM user_profile WHERE user_id = 1")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO user_profile (user_id, name, gender, age, weight, height, activity_level, goal, target_calories, target_protein, target_carbs, target_fat, target_water)
            VALUES (1, 'Usuário VivaLeve', 'M', 28, 75.0, 175.0, 'moderado', 'emagrecer', 1900, 150, 180, 55, 2600)
        """)

    # Garantir cheat_settings para user_id = 1
    cursor.execute("SELECT COUNT(*) as count FROM cheat_settings WHERE user_id = 1")
    if cursor.fetchone()["count"] == 0:
        cursor.execute("""
            INSERT INTO cheat_settings (user_id, meals_per_week, daily_bank_kcal, cheat_mode_active, active_date)
            VALUES (1, 1, 200.0, 0, '')
        """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados SQLite atualizado com suporte a multiusuário com sucesso!")
