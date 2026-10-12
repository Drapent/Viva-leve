import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database import get_connection

MISSION_TEMPLATES = [
    {"key": "prato_colorido", "title": "Prato Colorido", "description": "Coma pelo menos 2 vegetais ou folhas verdes no almoço ou jantar.", "points": 20},
    {"key": "meta_agua", "title": "Hidratacao Campea", "description": "Beba 2.000ml ou mais de agua durante o dia.", "points": 25},
    {"key": "scanner_ia", "title": "Raio-X Nutricional", "description": "Analise uma refeicao usando o Scanner de Foto com IA.", "points": 20},
    {"key": "proteina_alta", "title": "Super Proteina", "description": "Consuma uma refeicao nutritiva com pelo menos 30g de proteina.", "points": 20},
    {"key": "diario_completo", "title": "Diario Exemplar", "description": "Registre pelo menos 3 refeicoes completas no seu diario hoje.", "points": 30},
    {"key": "meta_calorias", "title": "Na Mosca", "description": "Fique dentro da sua meta calorica diaria (ate 100 kcal de tolerancia).", "points": 25},
    {"key": "treino_feito", "title": "Treino Concluido", "description": "Complete um treino hoje e registre no app.", "points": 40},
    {"key": "registrar_peso", "title": "Peso em Dia", "description": "Registre seu peso hoje para acompanhar sua evolucao.", "points": 15},
    {"key": "cafe_saudavel", "title": "Cafe da Manha Saudavel", "description": "Registre um cafe da manha com pelo menos 15g de proteina.", "points": 20},
    {"key": "almoco_colorido", "title": "Almoco Colorido", "description": "Faca um almoco com 3 cores diferentes de vegetais.", "points": 20},
    {"key": "jantar_leve", "title": "Jantar Leve", "description": "Faca um jantar com menos de 500 kcal.", "points": 20},
    {"key": "lanche_saudavel", "title": "Lanche Saudavel", "description": "Escolha um lanche com frutas ou oleaginosas.", "points": 15},
    {"key": "sem_refrigerante", "title": "Sem Refrigerante", "description": "Fique o dia todo sem beber refrigerante.", "points": 25},
    {"key": "agua_antes_refeicao", "title": "Agua Antes de Comer", "description": "Beba 1 copo de agua 30 min antes do almoco ou jantar.", "points": 15},
    {"key": "parar_comida", "title": "Parar de Comer", "description": "Pare de comer quando estiver satisfeito (80% cheio).", "points": 20},
    {"key": "mastigar_bem", "title": "Mastigar Bem", "description": "Mastigue cada garfada pelo menos 20 vezes.", "points": 15},
    {"key": "sem_sobremesa", "title": "Sem Sobremesa", "description": "Fique o dia todo sem sobremesas acucaradas.", "points": 25},
    {"key": "fruta_no_lanche", "title": "Fruta no Lanche", "description": "Coma pelo menos 1 fruta no lanche da tarde.", "points": 15},
    {"key": "proteina_no_cafe", "title": "Proteina no Cafe", "description": "Inclua proteina no cafe da manha (ovos, iogurte, queijo).", "points": 20},
    {"key": "comida_caseira", "title": "Comida Caseira", "description": "Faca pelo menos 1 refeicao caseira hoje.", "points": 20},
    {"key": "sem_fast_food", "title": "Sem Fast Food", "description": "Fique o dia todo sem comer fast food.", "points": 30},
    {"key": "verdura_no_almoco", "title": "Verdura no Almoco", "description": "Inclua verduras folhosas no almoco.", "points": 15},
    {"key": "legume_no_jantar", "title": "Legume no Jantar", "description": "Inclua legumes cozidos no jantar.", "points": 15},
    {"key": "sem_acucar", "title": "Sem Acucar", "description": "Fique o dia todo sem adicionar acucar nas bebidas.", "points": 25},
    {"key": "cha_verde", "title": "Cha Verde", "description": "Beba pelo menos 1 xicara de cha verde sem acucar.", "points": 15},
    {"key": "alongamento", "title": "Alongamento", "description": "Faca pelo menos 10 minutos de alongamento hoje.", "points": 20},
    {"key": "caminhada", "title": "Caminhada", "description": "Caminhe pelo menos 30 minutos hoje.", "points": 25},
    {"key": "dormir_bem", "title": "Dormir Bem", "description": "Durma pelo menos 7 horas esta noite.", "points": 20},
    {"key": "acordar_cedo", "title": "Acordar Cedo", "description": "Acorde antes das 7h da manha.", "points": 20},
    {"key": "sem_celular_mesa", "title": "Sem Celular a Mesa", "description": "Nao use o celular durante as refeicoes.", "points": 25},
    {"key": "cozinhar_em_casa", "title": "Cozinhar em Casa", "description": "Cozinhe pelo menos 1 refeicao em casa hoje.", "points": 20},
    {"key": "planejar_refeicao", "title": "Planejar Refeicao", "description": "Planeje sua proxima refeicao com antecedencia.", "points": 15},
    {"key": "comer_devagar", "title": "Comer Devagar", "description": "Coma pelo menos 1 refeicao em mais de 20 minutos.", "points": 20},
    {"key": "sem_snacks", "title": "Sem Snacks", "description": "Fique o dia todo sem comer snacks industrializados.", "points": 25},
    {"key": "proteina_em_todas", "title": "Proteina em Todas", "description": "Inclua proteina em todas as refeicoes do dia.", "points": 30},
    {"key": "carboidrato_bom", "title": "Carboidrato Bom", "description": "Escolha carboidratos integrais ou naturais (batata doce, mandioca).", "points": 20},
    {"key": "gordura_boa", "title": "Gordura Boa", "description": "Inclua gorduras boas (abacate, azeite, castanhas).", "points": 15},
    {"key": "fibra_alta", "title": "Fibra Alta", "description": "Consuma pelo menos 10g de fibras em uma refeicao.", "points": 20},
    {"key": "sem_alcool", "title": "Sem Alcool", "description": "Fique o dia todo sem beber alcool.", "points": 30},
    {"key": "feijao_todos_dias", "title": "Feijao Todos os Dias", "description": "Coma feijao pelo menos 1 vez hoje.", "points": 20},
    {"key": "carne_magra", "title": "Carne Magra", "description": "Escolha carne magra (frango, peixe, patinho).", "points": 20},
    {"key": "peixe", "title": "Peixe", "description": "Coma peixe pelo menos 1 vez hoje.", "points": 25},
    {"key": "sem_carne", "title": "Sem Carne", "description": "Fique o dia todo sem comer carne.", "points": 25},
    {"key": "pao_integral", "title": "Pao Integral", "description": "Escolha pao integral no lugar do pao branco.", "points": 15},
    {"key": "arroz_integral", "title": "Arroz Integral", "description": "Escolha arroz integral no lugar do branco.", "points": 15},
    {"key": "sem_sal_extra", "title": "Sem Sal Extra", "description": "Nao adicione sal extra nos alimentos.", "points": 20}
]

def get_week_range(target_date: Optional[datetime] = None) -> tuple[str, str, str, int]:
    """Retorna (week_key, start_date_str, end_date_str, days_remaining)"""
    dt = target_date or datetime.now()
    start_of_week = dt - timedelta(days=dt.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    days_remaining = 6 - dt.weekday()
    week_key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
    return week_key, start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d"), max(0, days_remaining)

def award_points(user_id: int, action_type: str, points: int, description: str = "", date_str: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    d = date_str or datetime.now().strftime("%Y-%m-%d")

    if action_type in ["streak_maintained", "water_goal_met", "calorie_goal_met"]:
        cursor.execute("SELECT id FROM user_points WHERE user_id = ? AND action_type = ? AND date = ?", (user_id, action_type, d))
        if cursor.fetchone():
            conn.close()
            return

    cursor.execute("""
        INSERT INTO user_points (user_id, date, action_type, points, description)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, d, action_type, points, description))
    conn.commit()
    conn.close()

def get_or_create_streak(user_id: int, today_str: Optional[str] = None) -> Dict[str, Any]:
    today = today_str or datetime.now().strftime("%Y-%m-%d")
    today_dt = datetime.strptime(today, "%Y-%m-%d")
    yesterday_str = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_streaks WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute("""
            INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_active_date, freezes_remaining)
            VALUES (?, 0, 0, '', 2)
        """, (user_id,))
        conn.commit()
        current_streak = 0
        longest_streak = 0
        last_active = ""
        freezes = 2
    else:
        current_streak = row["current_streak"]
        longest_streak = row["longest_streak"]
        last_active = row["last_active_date"] or ""
        freezes = row["freezes_remaining"]

    # Verificar atividade hoje no diário ou água
    cursor.execute("SELECT COUNT(*) as c FROM diary_entries WHERE user_id = ? AND date = ?", (user_id, today))
    diary_count = cursor.fetchone()["c"]
    cursor.execute("SELECT SUM(amount_ml) as total FROM water_entries WHERE user_id = ? AND date = ?", (user_id, today))
    water_row = cursor.fetchone()
    water_total = water_row["total"] or 0

    active_today = (diary_count > 0 or water_total > 0)

    if active_today:
        if last_active == today:
            pass  # Já registrado hoje
        elif last_active == yesterday_str:
            current_streak += 1
            if current_streak > longest_streak:
                longest_streak = current_streak
            last_active = today
            cursor.execute("""
                UPDATE user_streaks
                SET current_streak = ?, longest_streak = ?, last_active_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (current_streak, longest_streak, last_active, user_id))
            conn.commit()
            award_points(user_id, "streak_maintained", 30, f"Manteve a ofensiva acesa ({current_streak} dias)!", today)
        else:
            if last_active != "":
                diff_days = (today_dt - datetime.strptime(last_active, "%Y-%m-%d")).days
                if diff_days == 2 and freezes > 0:
                    freezes -= 1
                    current_streak += 1
                    if current_streak > longest_streak:
                        longest_streak = current_streak
                    last_active = today
                    cursor.execute("""
                        UPDATE user_streaks
                        SET current_streak = ?, longest_streak = ?, last_active_date = ?, freezes_remaining = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (current_streak, longest_streak, last_active, freezes, user_id))
                    conn.commit()
                    award_points(user_id, "streak_maintained", 30, f"Proteção de congelamento usada! Ofensiva salva ({current_streak} dias)", today)
                else:
                    current_streak = 1
                    last_active = today
                    cursor.execute("""
                        UPDATE user_streaks
                        SET current_streak = ?, last_active_date = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (current_streak, last_active, user_id))
                    conn.commit()
                    award_points(user_id, "streak_maintained", 15, "Nova sequência iniciada!", today)
            else:
                current_streak = 1
                if longest_streak == 0:
                    longest_streak = 1
                last_active = today
                cursor.execute("""
                    UPDATE user_streaks
                    SET current_streak = ?, longest_streak = ?, last_active_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (current_streak, longest_streak, last_active, user_id))
                conn.commit()
                award_points(user_id, "streak_maintained", 15, "Primeira sequência iniciada!", today)

    # Construir histórico dos últimos 7 dias
    history_7_days = []
    day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    for i in range(6, -1, -1):
        d_check = today_dt - timedelta(days=i)
        d_str = d_check.strftime("%Y-%m-%d")
        weekday_idx = d_check.weekday()
        cursor.execute("SELECT COUNT(*) as c FROM diary_entries WHERE user_id = ? AND date = ?", (user_id, d_str))
        c_diary = cursor.fetchone()["c"]
        cursor.execute("SELECT SUM(amount_ml) as total FROM water_entries WHERE user_id = ? AND date = ?", (user_id, d_str))
        w_total = cursor.fetchone()["total"] or 0
        is_lit = (c_diary > 0 or w_total > 0)
        history_7_days.append({
            "date": d_str,
            "day_name": day_names[weekday_idx],
            "is_lit": is_lit,
            "is_today": (d_str == today)
        })

    conn.close()

    if current_streak >= 14:
        flame_level = 3
        flame_title = "Fogo Cósmico 🔥⚡"
        flame_class = "flame-purple"
    elif current_streak >= 5:
        flame_level = 2
        flame_title = "Fogo Ardente 🔥"
        flame_class = "flame-orange"
    elif current_streak >= 1:
        flame_level = 1
        flame_title = "Chama Acesa 🔥"
        flame_class = "flame-yellow"
    else:
        flame_level = 0
        flame_title = "Foguinho Apagado"
        flame_class = "flame-grey"

    motivational_messages = [
        "Mantenha o foco hoje para não deixar a chama apagar!",
        "Você está criando um hábito de ferro. Continue firme!",
        "Cada dia conta! O segredo da consistência é nunca desistir.",
        "Seu corpo agradece cada refeição saudável e cada copo d'água!",
        "Incrível! Sua dedicação está inspirando toda a família!"
    ]
    motivational_msg = motivational_messages[min(current_streak, len(motivational_messages) - 1)]

    return {
        "user_id": user_id,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "active_today": active_today,
        "freezes_remaining": freezes,
        "flame_level": flame_level,
        "flame_title": flame_title,
        "flame_class": flame_class,
        "motivational_message": motivational_msg,
        "history_7_days": history_7_days
    }

def get_or_generate_missions(user_id: int, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
    today = date_str or datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM user_missions WHERE user_id = ? AND date = ?", (user_id, today))
    rows = cursor.fetchall()

    if not rows:
        # Selecionar 3 missões aleatórias baseadas no dia do ano (varia a cada dia)
        import random
        day_of_year = datetime.strptime(today, "%Y-%m-%d").timetuple().tm_yday
        random.seed(day_of_year + user_id)  # Mesmo dia = mesmas missões para o mesmo usuário
        selected = random.sample(MISSION_TEMPLATES, min(3, len(MISSION_TEMPLATES)))
        for tmpl in selected:
            cursor.execute("""
                INSERT INTO user_missions (user_id, date, mission_key, title, description, points, completed)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (user_id, today, tmpl["key"], tmpl["title"], tmpl["description"], tmpl["points"]))
        conn.commit()

        cursor.execute("SELECT * FROM user_missions WHERE user_id = ? AND date = ?", (user_id, today))
        rows = cursor.fetchall()

    missions = []
    cursor.execute("SELECT SUM(amount_ml) as total FROM water_entries WHERE user_id = ? AND date = ?", (user_id, today))
    water_row = cursor.fetchone()
    water_total = water_row["total"] or 0

    cursor.execute("SELECT COUNT(*) as c FROM diary_entries WHERE user_id = ? AND date = ?", (user_id, today))
    meals_count = cursor.fetchone()["c"]

    for r in rows:
        m = dict(r)
        if not m["completed"]:
            auto_complete = False
            if m["mission_key"] == "meta_agua" and water_total >= 2000:
                auto_complete = True
            elif m["mission_key"] == "diario_completo" and meals_count >= 3:
                auto_complete = True

            if auto_complete:
                cursor.execute("UPDATE user_missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?", (m["id"],))
                conn.commit()
                m["completed"] = 1
                award_points(user_id, "mission_completed", m["points"], f"Missão cumprida: {m['title']}", today)

        missions.append(m)

    conn.close()
    return missions

def complete_mission_manually(user_id: int, mission_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_missions WHERE id = ? AND user_id = ?", (mission_id, user_id))
    mission = cursor.fetchone()

    if not mission:
        conn.close()
        return {"success": False, "message": "Missão não encontrada."}

    if mission["completed"]:
        conn.close()
        return {"success": True, "message": "Missão já concluída anteriormente."}

    cursor.execute("UPDATE user_missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?", (mission_id,))
    conn.commit()

    award_points(user_id, "mission_completed", mission["points"], f"Missão cumprida: {mission['title']}", mission["date"])
    conn.close()

    return {
        "success": True,
        "message": f"Parabéns! Missão '{mission['title']}' concluída (+{mission['points']} pontos)!"
    }

def get_user_family(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, f.name, f.invite_code, f.created_by_user_id, fm.role, fm.joined_at
        FROM family_members fm
        JOIN families f ON f.id = fm.family_id
        WHERE fm.user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_family(user_id: int, family_name: str) -> Dict[str, Any]:
    name = family_name.strip()
    if not name:
        name = "Família VivaLeve"

    conn = get_connection()
    cursor = conn.cursor()

    # Verificar se o usuário já tem família
    cursor.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "Você já faz parte de um grupo familiar."}

    import secrets
    # Gerar código de convite único amigável (ex: SILVA-4821 ou VIVA-7829)
    prefix = "".join(c for c in name.split()[0].upper() if c.isalnum())[:5]
    if len(prefix) < 3:
        prefix = "VIVA"
    random_num = secrets.randbelow(9000) + 1000
    invite_code = f"{prefix}-{random_num}"

    cursor.execute("""
        INSERT INTO families (name, invite_code, created_by_user_id)
        VALUES (?, ?, ?)
    """, (name, invite_code, user_id))
    family_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO family_members (family_id, user_id, role)
        VALUES (?, ?, 'admin')
    """, (family_id, user_id))

    # Conceder pontos por criar a família
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO user_points (user_id, date, action_type, points, description)
        VALUES (?, ?, 'family_created', 50, ?)
    """, (user_id, today, f"🏆 Criação da {name} (+50 pts)"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Grupo '{name}' criado com sucesso!",
        "family": {
            "id": family_id,
            "name": name,
            "invite_code": invite_code,
            "role": "admin"
        }
    }

def join_family(user_id: int, invite_code: str) -> Dict[str, Any]:
    code = invite_code.strip().upper()
    if not code:
        return {"success": False, "message": "Informe um código de convite válido."}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "Você já faz parte de uma família. Saia da atual para entrar em outra."}

    cursor.execute("SELECT * FROM families WHERE UPPER(invite_code) = ?", (code,))
    family = cursor.fetchone()
    if not family:
        conn.close()
        return {"success": False, "message": f"Nenhuma família encontrada com o código '{code}'."}

    family_id = family["id"]
    cursor.execute("""
        INSERT INTO family_members (family_id, user_id, role)
        VALUES (?, ?, 'member')
    """, (family_id, user_id))

    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO user_points (user_id, date, action_type, points, description)
        VALUES (?, ?, 'family_joined', 30, ?)
    """, (user_id, today, f"Entrou na {family['name']} (+30 pts)"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"Você entrou na {family['name']} com sucesso! 🎉",
        "family": {
            "id": family_id,
            "name": family["name"],
            "invite_code": family["invite_code"],
            "role": "member"
        }
    }

def add_family_member_direct(admin_user_id: int, member_name: str, member_email: str, password: str = "familia123") -> Dict[str, Any]:
    """Permite ao administrador da família criar ou convidar um parente diretamente."""
    fam = get_user_family(admin_user_id)
    if not fam:
        return {"success": False, "message": "Você precisa criar uma família primeiro."}

    name = member_name.strip()
    email = member_email.strip().lower()

    if not name or not email:
        return {"success": False, "message": "Nome e e-mail do familiar são obrigatórios."}

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        target_uid = existing_user["id"]
        # Verificar se já é membro de alguma família
        cursor.execute("SELECT family_id FROM family_members WHERE user_id = ?", (target_uid,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "Este usuário já está cadastrado em uma família."}
    else:
        # Cadastrar novo membro
        import secrets, hashlib
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, salt)
            VALUES (?, ?, ?, ?)
        """, (name, email, pwd_hash, salt))
        target_uid = cursor.lastrowid

        # Perfil inicial
        cursor.execute("""
            INSERT INTO user_profile (user_id, name, gender, age, weight, height, activity_level, goal, target_calories, target_protein, target_carbs, target_fat, target_water)
            VALUES (?, ?, 'M', 28, 70.0, 170.0, 'moderado', 'emagrecer', 1900, 140, 180, 55, 2500)
        """, (target_uid, name))

        cursor.execute("""
            INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_active_date, freezes_remaining)
            VALUES (?, 1, 1, date('now'), 2)
        """, (target_uid,))

        cursor.execute("""
            INSERT INTO cheat_settings (user_id, meals_per_week, daily_bank_kcal, cheat_mode_active, active_date)
            VALUES (?, 1, 200.0, 0, '')
        """, (target_uid,))

    cursor.execute("""
        INSERT INTO family_members (family_id, user_id, role)
        VALUES (?, ?, 'member')
    """, (fam["id"], target_uid))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": f"{name} foi adicionado(a) à {fam['name']} com sucesso! 🎉",
        "member": {
            "id": target_uid,
            "name": name,
            "email": email
        }
    }

def leave_family(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM family_members WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Você saiu do grupo familiar."}

def get_family_battle(current_user_id: int, date_str: Optional[str] = None) -> Dict[str, Any]:
    today_dt = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
    week_key, start_date, end_date, days_remaining = get_week_range(today_dt)

    family = get_user_family(current_user_id)
    if not family:
        start_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m")
        end_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m")
        return {
            "in_family": False,
            "week_key": week_key,
            "week_display": f"Semana de {start_fmt} a {end_fmt}",
            "days_remaining": days_remaining,
            "ranking": []
        }

    family_id = family["id"]
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar apenas os membros reais DESTA família
    cursor.execute("""
        SELECT u.id, u.name, u.email, fm.role, fm.joined_at
        FROM family_members fm
        JOIN users u ON u.id = fm.user_id
        WHERE fm.family_id = ?
        ORDER BY fm.id ASC
    """, (family_id,))
    family_users = [dict(u) for u in cursor.fetchall()]

    ranking = []
    for u in family_users:
        uid = u["id"]

        cursor.execute("""
            SELECT SUM(points) as total_pts
            FROM user_points
            WHERE user_id = ? AND date >= ? AND date <= ?
        """, (uid, start_date, end_date))
        pts_row = cursor.fetchone()
        pts = pts_row["total_pts"] or 0

        cursor.execute("SELECT current_streak FROM user_streaks WHERE user_id = ?", (uid,))
        s_row = cursor.fetchone()
        streak = s_row["current_streak"] if s_row else 0

        cursor.execute("""
            SELECT COUNT(*) as c FROM diary_entries
            WHERE user_id = ? AND date >= ? AND date <= ?
        """, (uid, start_date, end_date))
        meals = cursor.fetchone()["c"]

        cursor.execute("""
            SELECT SUM(amount_ml) as total FROM water_entries
            WHERE user_id = ? AND date >= ? AND date <= ?
        """, (uid, start_date, end_date))
        water = cursor.fetchone()["total"] or 0

        badges = []
        if streak >= 5:
            badges.append("🔥 Mestre da Ofensiva")
        if water >= 10000:
            badges.append("💧 Peixe Humano")
        if meals >= 10:
            badges.append("🥗 Disciplina Ninja")

        ranking.append({
            "user_id": uid,
            "name": u["name"],
            "role": u["role"],
            "is_me": (uid == current_user_id),
            "points": pts,
            "streak": streak,
            "meals_logged": meals,
            "water_liters": round(water / 1000.0, 1),
            "badges": badges
        })

    ranking.sort(key=lambda x: (x["points"], x["streak"]), reverse=True)

    podium_medals = ["👑 1º Ouro", "🥈 2º Prata", "🥉 3º Bronze"]
    for i, member in enumerate(ranking):
        member["position"] = i + 1
        if i < 3:
            member["medal"] = podium_medals[i]
        else:
            member["medal"] = f"{i + 1}º Lugar"

    leader = ranking[0] if ranking else None
    is_current_user_leader = (leader and leader["user_id"] == current_user_id)

    # Buscar escolha do campeão para esta família específica
    cursor.execute("""
        SELECT * FROM family_cheat_choice 
        WHERE (family_id = ? OR family_id IS NULL) AND week_key = ?
        ORDER BY id DESC LIMIT 1
    """, (family_id, week_key))
    choice_row = cursor.fetchone()

    cheat_choice = None
    if choice_row:
        cheat_choice = {
            "winner_name": choice_row["winner_name"],
            "chosen_dish": choice_row["chosen_dish"],
            "restaurant_name": choice_row["restaurant_name"],
            "message": choice_row["message"],
            "updated_at": choice_row["updated_at"]
        }

    conn.close()

    start_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m")
    end_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m")
    week_display = f"Semana de {start_fmt} a {end_fmt}"

    return {
        "in_family": True,
        "family": family,
        "week_key": week_key,
        "week_display": week_display,
        "days_remaining": days_remaining,
        "leader": leader,
        "is_current_user_leader": is_current_user_leader,
        "cheat_choice": cheat_choice,
        "ranking": ranking
    }

def save_family_cheat_choice(user_id: int, chosen_dish: str, restaurant_name: str = "", message: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    u = cursor.fetchone()
    if not u:
        conn.close()
        return {"success": False, "message": "Usuário não encontrado."}
    user_name = u["name"]

    fam = get_user_family(user_id)
    family_id = fam["id"] if fam else 1

    week_key, _, _, _ = get_week_range()

    cursor.execute("""
        SELECT id FROM family_cheat_choice
        WHERE (family_id = ? OR family_id IS NULL) AND week_key = ?
    """, (family_id, week_key))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE family_cheat_choice
            SET family_id = ?, winner_user_id = ?, winner_name = ?, chosen_dish = ?, restaurant_name = ?, message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (family_id, user_id, user_name, chosen_dish, restaurant_name, message, existing["id"]))
    else:
        cursor.execute("""
            INSERT OR REPLACE INTO family_cheat_choice (week_key, family_id, winner_user_id, winner_name, chosen_dish, restaurant_name, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (week_key, family_id, user_id, user_name, chosen_dish, restaurant_name, message))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "👑 Escolha registrada com sucesso! A família inteira já pode ver sua decisão para o Dia do Lixo!"
    }

