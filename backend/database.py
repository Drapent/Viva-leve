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

    # Tabela de Treinos e Exercícios (Estilo Growth Supplements)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 45,
        intensity TEXT DEFAULT 'moderado',
        calories_burned REAL DEFAULT 300.0,
        volume_kg REAL DEFAULT 0.0,
        exercises_json TEXT NOT NULL DEFAULT '[]',
        notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Fichas e Treinos Personalizados
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workout_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        name TEXT NOT NULL,
        focus_area TEXT NOT NULL,
        is_preset INTEGER DEFAULT 0,
        exercises_json TEXT NOT NULL DEFAULT '[]',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabela de Avatar Evolutivo com Foto & Gamificação
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_avatar (
        user_id INTEGER PRIMARY KEY,
        photo_url TEXT DEFAULT '',
        body_fat_visual INTEGER DEFAULT 20,
        muscle_mass_visual INTEGER DEFAULT 50,
        level INTEGER DEFAULT 1,
        xp INTEGER DEFAULT 0,
        coins INTEGER DEFAULT 100,
        equipped_outfit TEXT DEFAULT 'regata_basica',
        equipped_accessory TEXT DEFAULT 'shaker',
        equipped_aura TEXT DEFAULT 'nenhuma',
        unlocked_items_json TEXT DEFAULT '["regata_basica", "shaker"]',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # ----------------- AVATAR 3D: analise facial por IA -----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS avatar_appearance (
        user_id INTEGER PRIMARY KEY,
        skin_tone TEXT DEFAULT '#e0ac69',
        hair_color TEXT DEFAULT '#2b1d16',
        hair_style TEXT DEFAULT 'curto',
        facial_hair TEXT DEFAULT 'nenhum',
        eye_color TEXT DEFAULT '#3b2412',
        face_shape TEXT DEFAULT 'quadrado',
        shoulder_width TEXT DEFAULT 'medio',
        frame TEXT DEFAULT 'medio',
        brow_thickness REAL DEFAULT 1.0,
        face_roundness REAL DEFAULT 1.0,
        jaw_width REAL DEFAULT 1.0,
        ai_confidence REAL DEFAULT 0.0,
        ai_engine TEXT DEFAULT '',
        analyzed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS avatar_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weight REAL DEFAULT 0.0,
        body_fat REAL DEFAULT 0.0,
        muscle_mass REAL DEFAULT 0.0,
        lean_mass REAL DEFAULT 0.0,
        avatar_bulk REAL DEFAULT 0.0,
        level INTEGER DEFAULT 1,
        note TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_avatar_snapshots_day
        ON avatar_snapshots(user_id, date);
    """)

    # ----------------- BALANCA DIGITAL (BIOIMPEDANCIA BLE) -----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS body_composition (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        weight REAL DEFAULT 0.0,
        body_fat REAL,
        muscle_mass REAL,
        water_pct REAL,
        bone_mass REAL,
        visceral_fat REAL,
        basal_metabolism REAL,
        metabolic_age REAL,
        bmi REAL,
        source TEXT DEFAULT 'manual',
        device_name TEXT DEFAULT '',
        raw_payload TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_body_composition_day
        ON body_composition(user_id, date);
    """)

    # ----------------- RELOGIO / SMARTWATCH (BLE HRM-GPS) -----------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wearable_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        kind TEXT DEFAULT 'watch',
        manufacturer TEXT DEFAULT '',
        device_id TEXT DEFAULT '',
        last_connected_at TIMESTAMP,
        last_sync_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wearable_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        device_id INTEGER,
        device_name TEXT DEFAULT '',
        calories_burned REAL DEFAULT 0.0,
        active_calories REAL DEFAULT 0.0,
        steps INTEGER DEFAULT 0,
        distance_km REAL DEFAULT 0.0,
        resting_hr INTEGER,
        avg_hr INTEGER,
        max_hr INTEGER,
        active_minutes INTEGER DEFAULT 0,
        sleep_hours REAL DEFAULT 0.0,
        spo2 INTEGER,
        source TEXT DEFAULT 'manual',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_wearable_sessions_day
        ON wearable_sessions(user_id, date);
    """)

    # Limpeza de usuários fictícios antigos das sementes de teste
    cursor.execute("DELETE FROM users WHERE email LIKE '%@familia.com'")
    cursor.execute("DELETE FROM user_points WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM user_streaks WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM user_profile WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM avatar_snapshots WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM body_composition WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM wearable_sessions WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM wearable_devices WHERE user_id NOT IN (SELECT id FROM users)")
    cursor.execute("DELETE FROM avatar_appearance WHERE user_id NOT IN (SELECT id FROM users)")


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

    # Migrações para campos adicionais do perfil (estilo de vida e personalização de dieta)
    cursor.execute("PRAGMA table_info(user_profile)")
    profile_cols = [row['name'] for row in cursor.fetchall()]
    if 'meals_per_day' not in profile_cols:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN meals_per_day INTEGER DEFAULT 4")
    if 'diet_style' not in profile_cols:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN diet_style TEXT DEFAULT 'padrao'")
    if 'target_weight' not in profile_cols:
        cursor.execute("ALTER TABLE user_profile ADD COLUMN target_weight REAL DEFAULT 70.0")

    # Inserir Fichas de Treino Pré-definidas Estilo Growth se tabela estiver vazia
    cursor.execute("SELECT COUNT(*) as count FROM workout_templates WHERE is_preset = 1")
    if cursor.fetchone()["count"] == 0:
        presets = [
            ("Treino A - Peito, Tríceps & Ombros", "Peito e Tríceps", json.dumps([
                {"name": "Supino Reto com Barra", "sets": 4, "reps": "8-12", "weight_kg": 40.0, "rest_sec": 90},
                {"name": "Supino Inclinado com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 18.0, "rest_sec": 75},
                {"name": "Crossover / Peck Deck", "sets": 3, "reps": "12-15", "weight_kg": 25.0, "rest_sec": 60},
                {"name": "Desenvolvimento com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 14.0, "rest_sec": 75},
                {"name": "Elevação Lateral", "sets": 4, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Tríceps Corda no Cross", "sets": 4, "reps": "10-12", "weight_kg": 20.0, "rest_sec": 60},
                {"name": "Tríceps Testa", "sets": 3, "reps": "10-12", "weight_kg": 15.0, "rest_sec": 60}
            ])),
            ("Treino B - Costas, Bíceps & Abdômen", "Costas e Bíceps", json.dumps([
                {"name": "Puxada Frontal Alta", "sets": 4, "reps": "8-12", "weight_kg": 45.0, "rest_sec": 90},
                {"name": "Remada Baixa no Triângulo", "sets": 4, "reps": "10-12", "weight_kg": 40.0, "rest_sec": 75},
                {"name": "Remada Curvada com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 16.0, "rest_sec": 75},
                {"name": "Crucifixo Invertido", "sets": 3, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Rosca Direta com Barra W", "sets": 4, "reps": "10-12", "weight_kg": 20.0, "rest_sec": 60},
                {"name": "Rosca Martelo com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 12.0, "rest_sec": 60},
                {"name": "Abdominal Infra na Paralela", "sets": 3, "reps": "15-20", "weight_kg": 0.0, "rest_sec": 45}
            ])),
            ("Treino C - Pernas Completo (Quadríceps & Glúteos)", "Pernas", json.dumps([
                {"name": "Agachamento Livre com Barra", "sets": 4, "reps": "8-10", "weight_kg": 50.0, "rest_sec": 120},
                {"name": "Leg Press 45º", "sets": 4, "reps": "10-12", "weight_kg": 120.0, "rest_sec": 90},
                {"name": "Cadeira Extensora", "sets": 3, "reps": "12-15", "weight_kg": 40.0, "rest_sec": 60},
                {"name": "Mesa Flexora", "sets": 4, "reps": "10-12", "weight_kg": 35.0, "rest_sec": 60},
                {"name": "Stiff com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 18.0, "rest_sec": 75},
                {"name": "Panturrilha em Pé", "sets": 4, "reps": "15-20", "weight_kg": 45.0, "rest_sec": 45}
            ])),
            ("Treino D - Cardio & Core (Queima Calórica)", "Cardio e Abdômen", json.dumps([
                {"name": "Esteira - Caminhada Inclinada / Trote", "sets": 1, "reps": "25 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Bicicleta Ergométrica HIIT", "sets": 1, "reps": "15 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Prancha Abdominal Isométrica", "sets": 3, "reps": "45 seg", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Abdominal Supra Remador", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45}
            ])),
            # Novos treinos adicionados
            ("Treino E - Ombros & Trapézio (Delts & Traps)", "Ombros", json.dumps([
                {"name": "Desenvolvimento Militar com Barra", "sets": 4, "reps": "8-10", "weight_kg": 30.0, "rest_sec": 90},
                {"name": "Elevação Lateral com Halteres", "sets": 4, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Elevação Frontal com Halteres", "sets": 3, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Crucifixo Invertido (Posterior)", "sets": 4, "reps": "12-15", "weight_kg": 10.0, "rest_sec": 60},
                {"name": "Ento com Barra (Trapézio)", "sets": 4, "reps": "10-12", "weight_kg": 40.0, "rest_sec": 75},
                {"name": "Face Pull na Polia", "sets": 3, "reps": "15-20", "weight_kg": 15.0, "rest_sec": 60},
                {"name": "Ento com Halteres", "sets": 3, "reps": "12-15", "weight_kg": 12.0, "rest_sec": 60}
            ])),
            ("Treino F - Bíceps & Tríceps (Braços)", "Braços", json.dumps([
                {"name": "Rosca Direta com Barra", "sets": 4, "reps": "8-12", "weight_kg": 20.0, "rest_sec": 75},
                {"name": "Rosca Alternada com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 10.0, "rest_sec": 60},
                {"name": "Rosca Scott na Polia", "sets": 3, "reps": "12-15", "weight_kg": 15.0, "rest_sec": 60},
                {"name": "Rosca Martelo com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 10.0, "rest_sec": 60},
                {"name": "Tríceps Corda no Cross", "sets": 4, "reps": "10-12", "weight_kg": 20.0, "rest_sec": 60},
                {"name": "Tríceps Testa com Barra", "sets": 3, "reps": "10-12", "weight_kg": 15.0, "rest_sec": 60},
                {"name": "Tríceps Francês com Halteres", "sets": 3, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Mergulho entre Bancos (Tríceps)", "sets": 3, "reps": "12-15", "weight_kg": 0.0, "rest_sec": 60}
            ])),
            ("Treino G - Costas & Ombros (Costas & Delts)", "Costas e Ombros", json.dumps([
                {"name": "Puxada Frontal Alta", "sets": 4, "reps": "8-12", "weight_kg": 45.0, "rest_sec": 90},
                {"name": "Remada Curvada com Barra", "sets": 4, "reps": "8-10", "weight_kg": 40.0, "rest_sec": 90},
                {"name": "Remada Unilateral com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 16.0, "rest_sec": 75},
                {"name": "Puxada com Triângulo (Close Grip)", "sets": 3, "reps": "10-12", "weight_kg": 35.0, "rest_sec": 75},
                {"name": "Desenvolvimento com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 14.0, "rest_sec": 75},
                {"name": "Elevação Lateral", "sets": 4, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Crucifixo Invertido", "sets": 3, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60},
                {"name": "Face Pull na Polia", "sets": 3, "reps": "15-20", "weight_kg": 15.0, "rest_sec": 60}
            ])),
            ("Treino H - Pernas & Glúteos (Legs & Glutes)", "Pernas e Glúteos", json.dumps([
                {"name": "Agachamento Livre com Barra", "sets": 4, "reps": "8-10", "weight_kg": 50.0, "rest_sec": 120},
                {"name": "Leg Press 45º", "sets": 4, "reps": "10-12", "weight_kg": 120.0, "rest_sec": 90},
                {"name": "Cadeira Extensora", "sets": 3, "reps": "12-15", "weight_kg": 40.0, "rest_sec": 60},
                {"name": "Mesa Flexora", "sets": 4, "reps": "10-12", "weight_kg": 35.0, "rest_sec": 60},
                {"name": "Stiff com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 18.0, "rest_sec": 75},
                {"name": "Cadeira Adutora", "sets": 3, "reps": "12-15", "weight_kg": 30.0, "rest_sec": 60},
                {"name": "Cadeira Abdutora", "sets": 3, "reps": "12-15", "weight_kg": 30.0, "rest_sec": 60},
                {"name": "Panturrilha em Pé", "sets": 4, "reps": "15-20", "weight_kg": 45.0, "rest_sec": 45},
                {"name": "Panturrilha Sentado", "sets": 4, "reps": "15-20", "weight_kg": 35.0, "rest_sec": 45}
            ])),
            ("Treino I - Peito & Costas (Push & Pull)", "Peito e Costas", json.dumps([
                {"name": "Supino Reto com Barra", "sets": 4, "reps": "8-12", "weight_kg": 40.0, "rest_sec": 90},
                {"name": "Puxada Frontal Alta", "sets": 4, "reps": "8-12", "weight_kg": 45.0, "rest_sec": 90},
                {"name": "Supino Inclinado com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 18.0, "rest_sec": 75},
                {"name": "Remada Baixa no Triângulo", "sets": 4, "reps": "10-12", "weight_kg": 40.0, "rest_sec": 75},
                {"name": "Crossover / Peck Deck", "sets": 3, "reps": "12-15", "weight_kg": 25.0, "rest_sec": 60},
                {"name": "Remada Curvada com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 16.0, "rest_sec": 75},
                {"name": "Desenvolvimento com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 14.0, "rest_sec": 75},
                {"name": "Crucifixo Invertido", "sets": 3, "reps": "12-15", "weight_kg": 8.0, "rest_sec": 60}
            ])),
            ("Treino J - Full Body (Corpo Inteiro)", "Full Body", json.dumps([
                {"name": "Agachamento Livre com Barra", "sets": 4, "reps": "8-10", "weight_kg": 50.0, "rest_sec": 120},
                {"name": "Supino Reto com Barra", "sets": 4, "reps": "8-12", "weight_kg": 40.0, "rest_sec": 90},
                {"name": "Remada Curvada com Barra", "sets": 4, "reps": "8-10", "weight_kg": 40.0, "rest_sec": 90},
                {"name": "Desenvolvimento com Halteres", "sets": 3, "reps": "10-12", "weight_kg": 14.0, "rest_sec": 75},
                {"name": "Leg Press 45º", "sets": 4, "reps": "10-12", "weight_kg": 120.0, "rest_sec": 90},
                {"name": "Puxada Frontal Alta", "sets": 4, "reps": "8-12", "weight_kg": 45.0, "rest_sec": 90},
                {"name": "Cadeira Extensora", "sets": 3, "reps": "12-15", "weight_kg": 40.0, "rest_sec": 60},
                {"name": "Mesa Flexora", "sets": 4, "reps": "10-12", "weight_kg": 35.0, "rest_sec": 60},
                {"name": "Rosca Direta com Barra", "sets": 3, "reps": "10-12", "weight_kg": 20.0, "rest_sec": 60},
                {"name": "Tríceps Corda no Cross", "sets": 3, "reps": "10-12", "weight_kg": 20.0, "rest_sec": 60},
                {"name": "Panturrilha em Pé", "sets": 4, "reps": "15-20", "weight_kg": 45.0, "rest_sec": 45}
            ])),
            ("Treino K - HIIT & Cardio (Queima de Gordura)", "HIIT e Cardio", json.dumps([
                {"name": "Esteira - Corrida Intervalada", "sets": 1, "reps": "20 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Bicicleta Ergométrica HIIT", "sets": 1, "reps": "15 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Polichinelos", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Burpees", "sets": 3, "reps": "15 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Mountain Climbers", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Pular Corda", "sets": 3, "reps": "2 min", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Abdominal Supra Remador", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Prancha Abdominal Isométrica", "sets": 3, "reps": "45 seg", "weight_kg": 0.0, "rest_sec": 45}
            ])),
            ("Treino L - Yoga & Mobilidade (Flexibilidade)", "Yoga e Mobilidade", json.dumps([
                {"name": "Saudação ao Sol (Surya Namaskar)", "sets": 5, "reps": "1 ciclo", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura do Guerreiro I", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura do Guerreiro II", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura do Triângulo", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura do Cachorro Olhando para Baixo", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura da Criança", "sets": 3, "reps": "1 min", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Postura do Lótus (Meditação)", "sets": 1, "reps": "10 min", "weight_kg": 0.0, "rest_sec": 0}
            ])),
            ("Treino M - Funcional (Treino Funcional)", "Funcional", json.dumps([
                {"name": "Agachamento com Salto", "sets": 4, "reps": "12-15", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Flexão de Braço", "sets": 4, "reps": "12-15", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Afundo Alternado", "sets": 3, "reps": "12 cada", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Prancha com Toque no Ombro", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Abdominal Bicicleta", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Mountain Climbers", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Burpees", "sets": 3, "reps": "15 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Polichinelos", "sets": 3, "reps": "30 seg", "weight_kg": 0.0, "rest_sec": 30}
            ])),
            ("Treino N - Calistenia (Peso Corporal)", "Calistenia", json.dumps([
                {"name": "Flexão de Braço", "sets": 4, "reps": "12-15", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Agachamento Livre", "sets": 4, "reps": "15-20", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Afundo Alternado", "sets": 3, "reps": "12 cada", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Prancha Abdominal Isométrica", "sets": 3, "reps": "45 seg", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Abdominal Supra Remador", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Abdominal Infra na Paralela", "sets": 3, "reps": "15-20", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Mergulho entre Bancos (Tríceps)", "sets": 3, "reps": "12-15", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Barra Fixa (ou Assistida)", "sets": 3, "reps": "8-12", "weight_kg": 0.0, "rest_sec": 90}
            ])),
            ("Treino O - Pilates (Core & Controle)", "Pilates", json.dumps([
                {"name": "The Hundred (Cem)", "sets": 1, "reps": "100 reps", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Roll Up (Rolamento)", "sets": 3, "reps": "10 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Single Leg Stretch (Alongamento de Perna)", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Double Leg Stretch (Alongamento Duplo)", "sets": 3, "reps": "10 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Scissors (Tesoura)", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Shoulder Bridge (Ponte de Ombros)", "sets": 3, "reps": "10 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Swan (Cisne)", "sets": 3, "reps": "10 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Side Leg Lifts (Elevação Lateral de Perna)", "sets": 3, "reps": "15 reps", "weight_kg": 0.0, "rest_sec": 45}
            ])),
            ("Treino P - CrossFit (WOD)", "CrossFit", json.dumps([
                {"name": "Wall Balls (Bolas na Parede)", "sets": 4, "reps": "15 reps", "weight_kg": 6.0, "rest_sec": 60},
                {"name": "Box Jumps (Saltos na Caixa)", "sets": 4, "reps": "12 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Kettlebell Swings", "sets": 4, "reps": "15 reps", "weight_kg": 16.0, "rest_sec": 60},
                {"name": "Burpees", "sets": 4, "reps": "15 reps", "weight_kg": 0.0, "rest_sec": 45},
                {"name": "Thrusters (Arremesso)", "sets": 4, "reps": "12 reps", "weight_kg": 25.0, "rest_sec": 75},
                {"name": "Pull-ups (Barra Fixa)", "sets": 4, "reps": "8-12", "weight_kg": 0.0, "rest_sec": 90},
                {"name": "Double Unders (Pular Corda Duplo)", "sets": 3, "reps": "50 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Sit-ups (Abdominais)", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 45}
            ])),
            ("Treino Q - Natação (Swimming)", "Natação", json.dumps([
                {"name": "Nado Crawl", "sets": 4, "reps": "50m", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Nado Costas", "sets": 4, "reps": "50m", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Nado Peito", "sets": 4, "reps": "50m", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Nado Borboleta", "sets": 2, "reps": "25m", "weight_kg": 0.0, "rest_sec": 90},
                {"name": "Travessia Contínua", "sets": 1, "reps": "20 min", "weight_kg": 0.0, "rest_sec": 0}
            ])),
            ("Treino R - Corrida (Running)", "Corrida", json.dumps([
                {"name": "Aquecimento - Caminhada", "sets": 1, "reps": "5 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Trote Leve", "sets": 1, "reps": "10 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Corrida Moderada", "sets": 1, "reps": "20 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Sprint Intervalado", "sets": 4, "reps": "1 min", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Desaceleração - Caminhada", "sets": 1, "reps": "5 min", "weight_kg": 0.0, "rest_sec": 0}
            ])),
            ("Treino S - Ciclismo (Cycling)", "Ciclismo", json.dumps([
                {"name": "Aquecimento - Pedalada Leve", "sets": 1, "reps": "10 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Pedalada Moderada", "sets": 1, "reps": "30 min", "weight_kg": 0.0, "rest_sec": 0},
                {"name": "Subida (Alta Cadência)", "sets": 4, "reps": "5 min", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Sprint Final", "sets": 2, "reps": "1 min", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Desaceleração - Pedalada Leve", "sets": 1, "reps": "5 min", "weight_kg": 0.0, "rest_sec": 0}
            ])),
            ("Treino T - Artes Marciais (Luta)", "Artes Marciais", json.dumps([
                {"name": "Aquecimento - Polichinelos", "sets": 3, "reps": "1 min", "weight_kg": 0.0, "rest_sec": 30},
                {"name": "Sombra (Shadow Boxing)", "sets": 3, "reps": "3 min", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Jab & Cross", "sets": 4, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Hook & Uppercut", "sets": 4, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Kicks (Chutes)", "sets": 4, "reps": "15 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Defesa (Esquivas)", "sets": 3, "reps": "20 reps", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Mancinho (Saco de Pancadas)", "sets": 3, "reps": "3 min", "weight_kg": 0.0, "rest_sec": 60},
                {"name": "Alongamento Final", "sets": 1, "reps": "5 min", "weight_kg": 0.0, "rest_sec": 0}
            ]))
        ]
        for name, focus, ex_json in presets:
            cursor.execute("""
                INSERT INTO workout_templates (user_id, name, focus_area, is_preset, exercises_json)
                VALUES (1, ?, ?, 1, ?)
            """, (name, focus, ex_json))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados SQLite atualizado com suporte a multiusuário com sucesso!")
