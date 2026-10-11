import json
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database import get_connection

# Catálogo rico de refeições da culinária brasileira saudável e saborosa
DISH_CATALOG = {
    "breakfast": [
        {
            "name": "Ovos Mexidos com Torrada Integral e Mamão",
            "description": "2 ovos mexidos cremosos, 2 fatias de pão 100% integral com azeite e fatia de mamão com chia.",
            "calories": 340, "protein": 19, "carbs": 32, "fat": 14,
            "tags": ["Rico em Proteína", "Fibras", "Fácil"],
            "family_tip": "Rende para toda a casa: dobre a quantidade de ovos na frigideira e sirva com suco de laranja natural."
        },
        {
            "name": "Tapioca com Queijo Minas e Café com Leite",
            "description": "Tapioca crocante com queijo minas frescal grelhado e orégano + café com leite desnatado.",
            "calories": 310, "protein": 16, "carbs": 38, "fat": 10,
            "tags": ["Sem Glúten", "Cálcio", "Tradicional"],
            "family_tip": "As crianças adoram tapioca recheada com banana e canela como opção doce saudável."
        },
        {
            "name": "Mingau de Aveia Proteico com Banana e Canela",
            "description": "Aveia em flocos cozida no leite com rodelas de banana madura, canela e toque de mel ou pasta de amendoim.",
            "calories": 360, "protein": 18, "carbs": 48, "fat": 9,
            "tags": ["Energia Duradoura", "Saciedade"],
            "family_tip": "Prato quentinho e aconchegante perfeito para manhãs em família."
        },
        {
            "name": "Panqueca de Banana com Aveia e Mel",
            "description": "Massa fofinha feita com banana amassada, ovo e aveia, dourada na frigideira com canela e mel.",
            "calories": 290, "protein": 14, "carbs": 42, "fat": 7,
            "tags": ["Sem Açúcar Refinado", "Doce do Bem"],
            "family_tip": "Faça minipanquecas em formato divertido para animar o café da manhã dos pequenos."
        },
        {
            "name": "Sanduíche Natural de Frango Desfiado",
            "description": "Pão integral com recheio de peito de frango desfiado temperado com ricota, cenoura ralada e alface.",
            "calories": 330, "protein": 28, "carbs": 30, "fat": 8,
            "tags": ["Super Proteico", "Prático"],
            "family_tip": "Pode deixar a pasta de frango pronta na geladeira para a família toda montar seus lanches."
        },
        {
            "name": "Pão Francês na Chapa com Ovos Mexidos",
            "description": "Metade de pão francês quentinho com manteiga na chapa e ovos mexidos bem temperados com cheiro verde.",
            "calories": 320, "protein": 17, "carbs": 29, "fat": 13,
            "tags": ["Clássico da Padaria", "Sabor Brasileiro"],
            "family_tip": "O clássico do brasileiro, agora com equilíbrio de proteínas."
        },
        {
            "name": "Vitamina de Morango, Banana e Aveia",
            "description": "Vitamina batida bem gelada com morangos frescos, banana, aveia e leite desnatado ou vegetal.",
            "calories": 280, "protein": 13, "carbs": 44, "fat": 5,
            "tags": ["Refrescante", "Antioxidantes", "Rápido"],
            "family_tip": "Bata uma jarra grande no liquidificador para servir a todos antes de saírem para escola/trabalho."
        }
    ],
    "lunch": [
        {
            "name": "Frango Grelhado, Arroz Integral e Feijão Carioca",
            "description": "Filé de peito de frango grelhado suculento, arroz integral soltinho, concha de feijão carioca e salada de alface e tomate.",
            "calories": 510, "protein": 44, "carbs": 54, "fat": 11,
            "tags": ["Clássico Saudável", "Ferro", "Completo"],
            "family_tip": "O prato perfeito da família brasileira: feijão fresquinho agrada a todos."
        },
        {
            "name": "Filé de Tilápia com Purê de Batata Doce",
            "description": "Tilápia grelhada com crosta de ervas finas, purê aveludado de batata doce e brócolis cozido no vapor.",
            "calories": 440, "protein": 39, "carbs": 42, "fat": 10,
            "tags": ["Leve", "Digestão Fácil", "Ômega 3"],
            "family_tip": "Peixe branco suave que as crianças aceitam facilmente; asse vários filés de uma vez."
        },
        {
            "name": "Carne Moída Refogada com Abobrinha e Feijão Preto",
            "description": "Patinho moído refogado com alho, cebola, cenoura e cubos de abobrinha, acompanhado de arroz e feijão preto.",
            "calories": 530, "protein": 42, "carbs": 52, "fat": 14,
            "tags": ["Sabor Caseiro", "Prático"],
            "family_tip": "Excelente para cozinhar em grande quantidade para o almoço de domingo ou marmitas da semana."
        },
        {
            "name": "Moqueca Leve de Peixe com Arroz e Salada",
            "description": "Pedaços nobres de peixe cozidos com pimentões coloridos, tomate, cebola, leite de coco light e coentro, com arroz branco e vinagrete.",
            "calories": 460, "protein": 37, "carbs": 45, "fat": 13,
            "tags": ["Típico Brasileiro", "Rico em Sabor"],
            "family_tip": "Traga a panela de barro para a mesa: refeição que une a família com aroma irresistível."
        },
        {
            "name": "Bife de Alcatra Grelhado com Mandioca e Vinagrete",
            "description": "Bife macio de alcatra na chapa, mandioca cozida com azeite e vinagrete fresco de tomate e cebola roxa.",
            "calories": 520, "protein": 45, "carbs": 48, "fat": 13,
            "tags": ["Energia Pura", "Sem Glúten"],
            "family_tip": "Cozinhe a mandioca até derreter e sirva no capricho com tempero verde."
        },
        {
            "name": "Sobrecoxa Assada com Batatas Rústicas e Feijão",
            "description": "Sobrecoxa desossada e marinada com páprica e limão, assada com gomos de batatas e feijão carioca.",
            "calories": 500, "protein": 41, "carbs": 46, "fat": 15,
            "tags": ["Crocante", "Reconfortante"],
            "family_tip": "Prato de uma assadeira só: suja pouca louça na cozinha familiar."
        },
        {
            "name": "Strogonoff Fit de Frango com Arroz e Salada",
            "description": "Tiras de frango ao molho caseiro de tomate com creme de ricota e champignon, com arroz branco e salada verde.",
            "calories": 480, "protein": 43, "carbs": 47, "fat": 12,
            "tags": ["Queridinho da Família", "Versão Saudável"],
            "family_tip": "Substitui o creme de leite por ricota ou iogurte: o sabor fica idêntico e muito mais leve."
        }
    ],
    "snack": [
        {
            "name": "Iogurte Natural com Frutas e Castanhas",
            "description": "Pote de iogurte natural desnatado, morangos ou uvas fatiadas e castanhas de caju picadas.",
            "calories": 210, "protein": 15, "carbs": 22, "fat": 6,
            "tags": ["Probióticos", "Gorduras Boas"],
            "family_tip": "Deixe potinhos montados na geladeira para toda a família lanchar à tarde sem recorrer a biscoitos."
        },
        {
            "name": "Crepioca de Queijo Minas e Orégano",
            "description": "Massa fininha e dourada de 1 ovo com 2 colheres de goma de tapioca recheada com queijo minas.",
            "calories": 220, "protein": 17, "carbs": 18, "fat": 8,
            "tags": ["Rápido", "Crocante por Fora"],
            "family_tip": "Prepara em 3 minutos na frigideira antiaderente."
        },
        {
            "name": "Maçã Fatiada com Pasta de Amendoim",
            "description": "Maçã crocante em fatias com 1 colher de sopa de pasta de amendoim 100% integral e canela em pó.",
            "calories": 200, "protein": 7, "carbs": 25, "fat": 8,
            "tags": ["Doce Saudável", "Saciedade"],
            "family_tip": "As crianças adoram passar as fatias de fruta na pasta."
        },
        {
            "name": "Wrap Integral com Queijo Branco e Tomate",
            "description": "Tortilha integral recheada com queijo minas, tomate cereja fatiado e folhas de manjericão.",
            "calories": 230, "protein": 14, "carbs": 24, "fat": 7,
            "tags": ["Prático", "Sabor Pizza"],
            "family_tip": "Aquecer 1 minuto na frigideira faz o queijo derreter suavemente."
        },
        {
            "name": "Salada de Frutas Frescas com Chia",
            "description": "Tigela colorida de melancia, abacaxi, maçã e laranja com sementes de chia salpicadas.",
            "calories": 170, "protein": 4, "carbs": 38, "fat": 2,
            "tags": ["Super Hidratação", "Vitaminas"],
            "family_tip": "Faça uma travessa no domingo e mantenha na geladeira com gotas de limão para conservar."
        },
        {
            "name": "Ovo Cozido Temperado e Torradinhas",
            "description": "2 ovos cozidos com azeite, flor de sal e pimenta do reino acompanhados de mini torradas integrais.",
            "calories": 210, "protein": 15, "carbs": 14, "fat": 10,
            "tags": ["Proteína Pura", "Sem Fome"],
            "family_tip": "Snack perfeito para levar no carro ou consumir antes do treino."
        },
        {
            "name": "Vitamina de Abacate com Limão",
            "description": "Creme geladinho de abacate batido com leite desnatado, gotas de limão e adoçante natural.",
            "calories": 220, "protein": 8, "carbs": 18, "fat": 12,
            "tags": ["Gordura Boa", "Aveludado"],
            "family_tip": "O toque do limão corta a gordura do abacate e deixa super refrescante."
        }
    ],
    "dinner": [
        {
            "name": "Omelete Recheada de Espinafre e Queijo",
            "description": "Omelete fofa com 3 ovos, folhas frescas de espinafre refogado, tomate picado e queijo minas derretido.",
            "calories": 360, "protein": 28, "carbs": 6, "fat": 23,
            "tags": ["Baixo Carboidrato", "Leve para Dormir"],
            "family_tip": "Jantar rápido e leve que não pesa no estômago antes de dormir."
        },
        {
            "name": "Sopa Nutritiva de Legumes com Frango",
            "description": "Caldo caseiro dourado com peito de frango desfiado, cenoura, mandioquinha, abobrinha e cheiro verde.",
            "calories": 320, "protein": 32, "carbs": 30, "fat": 7,
            "tags": ["Aconchegante", "Fácil Digestão"],
            "family_tip": "Uma panela grande alimenta a família toda e rende sobras deliciosas."
        },
        {
            "name": "Salada Caesar Fit com Tiras de Frango",
            "description": "Mix de alface americana, peito de frango grelhado em tiras, croutons integrais e molho leve de iogurte.",
            "calories": 380, "protein": 38, "carbs": 18, "fat": 14,
            "tags": ["Refrescante", "Gourmet Saudável"],
            "family_tip": "Deixe cada membro da família temperar e montar seu prato na mesa."
        },
        {
            "name": "Filé de Salmão Grelhado com Purê de Abóbora",
            "description": "Posta de salmão grelhado com crosta crocante, purê cremoso de abóbora cabotiá e salada de rúcula.",
            "calories": 420, "protein": 36, "carbs": 26, "fat": 18,
            "tags": ["Ômega 3", "Cena Nobre"],
            "family_tip": "Perfeito para uma sexta-feira à noite especial em família."
        },
        {
            "name": "Escondidinho Fit de Mandioca com Carne Moída",
            "description": "Massa cremosa de mandioca recheada com carne moída magra bem temperada, gratinada com queijo.",
            "calories": 430, "protein": 36, "carbs": 44, "fat": 11,
            "tags": ["Comida de Verdade", "Gratinado"],
            "family_tip": "Coloque a travessa no forno e sirva quentinho para todos."
        },
        {
            "name": "Hambúrguer Caseiro de Patinho no Prato com Salada",
            "description": "2 hambúrgueres artesanais de carne 100% patinho, ovo frito na água e salada completa com tomate e palmito.",
            "calories": 410, "protein": 42, "carbs": 12, "fat": 18,
            "tags": ["Mata a Vontade", "Muito Proteico"],
            "family_tip": "Dá a sensação de lanchonete sem sair da dieta nem furar o bolso."
        },
        {
            "name": "Berinjela Recheada com Frango e Parmesão",
            "description": "Canoas de berinjela assadas recheadas com frango desfiado suculento ao molho de tomate e parmesão ralado.",
            "calories": 340, "protein": 34, "carbs": 18, "fat": 12,
            "tags": ["Criativo", "Low Carb"],
            "family_tip": "Uma forma gostosa de fazer a família comer mais legumes de maneira sofisticada."
        }
    ],
    "cheat_options": [
        {
            "name": "🍕 Noite da Pizza Artesanal em Família",
            "description": "Pizzas de massa leve com queijos de qualidade e sabores preferidos da casa para comemorar a vitória na semana.",
            "family_tip": "Quem ganhou a coroa da Batalha Familiar escolhe os sabores!"
        },
        {
            "name": "🍔 Hambúrguer Gourmet com Batata Rústica",
            "description": "Hambúrguer suculento no pão brioche com queijo derretido, molho especial e porção de batatas.",
            "family_tip": "Dia de satisfação merecida após cumprir as metas de água e refeições da semana."
        },
        {
            "name": "🍣 Festival de Sushi e Culinária Japonesa",
            "description": "Combinados de salmão, sashimis frescos, uramakis e pratos quentes.",
            "family_tip": "Opção saborosa e rica em proteínas para comemorar em família."
        },
        {
            "name": "🥩 Churrasco em Família no Fim de Semana",
            "description": "Cortes nobres grelhados na brasa com pão de alho, queijo coalho e farofa crocante.",
            "family_tip": "A reunião clássica de domingo celebrando o campeão da rodada!"
        },
        {
            "name": "🍝 Festival Italiano de Massas Frescas",
            "description": "Talharim ou nhoque artesanal com molho à bolonhesa ou quatro queijos e sobremesa especial.",
            "family_tip": "Massa caseira compartilhada com amor e sem culpa consciente."
        }
    ]
}

DAYS_ORDER = [
    ("segunda", "Segunda-feira", "🌱 Início Focado"),
    ("terca", "Terça-feira", "⚡ Mantendo o Ritmo"),
    ("quarta", "Quarta-feira", "🥗 Meio de Semana Saudável"),
    ("quinta", "Quinta-feira", "🔥 Foco Total"),
    ("sexta", "Sexta-feira", "🎉 Sextou Nutritivo"),
    ("sabado", "Sábado", "✨ Fim de Semana Equilibrado"),
    ("domingo", "Domingo", "👑 Dia do Lixo & Família")
]

def get_current_week_key() -> str:
    dt = datetime.now()
    return f"{dt.year}-W{dt.isocalendar()[1]:02d}"

def generate_weekly_menu_data(target_calories: float = 2000, mode: str = "individual") -> Dict[str, Any]:
    """Gera um cardápio semanal completo de 7 dias com variedade garantida."""
    days = {}
    
    b_pool = DISH_CATALOG["breakfast"][:]
    l_pool = DISH_CATALOG["lunch"][:]
    s_pool = DISH_CATALOG["snack"][:]
    d_pool = DISH_CATALOG["dinner"][:]

    random.shuffle(b_pool)
    random.shuffle(l_pool)
    random.shuffle(s_pool)
    random.shuffle(d_pool)

    cheat_pool = DISH_CATALOG["cheat_options"][:]
    random.shuffle(cheat_pool)

    for i, (day_key, day_label, day_subtitle) in enumerate(DAYS_ORDER):
        b = dict(b_pool[i % len(b_pool)])
        l = dict(l_pool[i % len(l_pool)])
        s = dict(s_pool[i % len(s_pool)])
        d = dict(d_pool[i % len(d_pool)])

        is_weekend = (day_key in ["sabado", "domingo"])
        cheat_dish = dict(cheat_pool[i % len(cheat_pool)]) if is_weekend else None

        day_total_cal = b["calories"] + l["calories"] + s["calories"] + d["calories"]
        day_total_p = b["protein"] + l["protein"] + s["protein"] + d["protein"]
        day_total_c = b["carbs"] + l["carbs"] + s["carbs"] + d["carbs"]
        day_total_f = b["fat"] + l["fat"] + s["fat"] + d["fat"]

        days[day_key] = {
            "key": day_key,
            "label": day_label,
            "subtitle": day_subtitle,
            "is_weekend": is_weekend,
            "meals": {
                "breakfast": b,
                "lunch": l,
                "snack": s,
                "dinner": d
            },
            "cheat_suggestion": cheat_dish,
            "totals": {
                "calories": day_total_cal,
                "protein": day_total_p,
                "carbs": day_total_c,
                "fat": day_total_f
            }
        }

    return {
        "mode": mode,
        "week_key": get_current_week_key(),
        "generated_at": datetime.now().isoformat(),
        "days": days
    }

def get_or_create_weekly_menu(user_id: int, mode: str = "individual", force_regenerate: bool = False) -> Dict[str, Any]:
    week_key = get_current_week_key()
    conn = get_connection()
    cursor = conn.cursor()

    family_id = None
    if mode == "family":
        cursor.execute("SELECT family_id FROM family_members WHERE user_id = ?", (user_id,))
        frow = cursor.fetchone()
        if frow:
            family_id = frow["family_id"]

    cursor.execute("""
        SELECT * FROM weekly_menus 
        WHERE user_id = ? AND week_key = ? AND mode = ?
    """, (user_id, week_key, mode))
    row = cursor.fetchone()

    if row and not force_regenerate:
        menu_data = json.loads(row["menu_data"])
        conn.close()
        return menu_data

    cursor.execute("SELECT target_calories FROM user_profile WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    prof = cursor.fetchone()
    target_cal = float(prof["target_calories"]) if prof and prof["target_calories"] else 2000.0

    new_menu = generate_weekly_menu_data(target_calories=target_cal, mode=mode)
    menu_json = json.dumps(new_menu, ensure_ascii=False)

    if row:
        cursor.execute("""
            UPDATE weekly_menus 
            SET menu_data = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (menu_json, row["id"]))
    else:
        cursor.execute("""
            INSERT INTO weekly_menus (user_id, family_id, week_key, mode, menu_data)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, family_id, week_key, mode, menu_json))

    conn.commit()
    conn.close()
    return new_menu

def swap_dish(user_id: int, mode: str, day_key: str, meal_type: str) -> Dict[str, Any]:
    """Troca uma refeição específica por outra opção saborosa da mesma categoria."""
    week_key = get_current_week_key()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM weekly_menus 
        WHERE user_id = ? AND week_key = ? AND mode = ?
    """, (user_id, week_key, mode))
    row = cursor.fetchone()

    if not row:
        conn.close()
        menu = get_or_create_weekly_menu(user_id, mode)
        return swap_dish(user_id, mode, day_key, meal_type)

    menu_data = json.loads(row["menu_data"])
    days = menu_data.get("days", {})

    if day_key not in days or meal_type not in days[day_key]["meals"]:
        conn.close()
        return {"success": False, "message": "Dia ou refeição inválida."}

    current_dish = days[day_key]["meals"][meal_type]
    candidates = DISH_CATALOG.get(meal_type, [])

    available = [d for d in candidates if d["name"] != current_dish.get("name")]
    if not available:
        available = candidates

    new_dish = dict(random.choice(available))
    days[day_key]["meals"][meal_type] = new_dish

    b = days[day_key]["meals"]["breakfast"]
    l = days[day_key]["meals"]["lunch"]
    s = days[day_key]["meals"]["snack"]
    d = days[day_key]["meals"]["dinner"]

    days[day_key]["totals"] = {
        "calories": b["calories"] + l["calories"] + s["calories"] + d["calories"],
        "protein": b["protein"] + l["protein"] + s["protein"] + d["protein"],
        "carbs": b["carbs"] + l["carbs"] + s["carbs"] + d["carbs"],
        "fat": b["fat"] + l["fat"] + s["fat"] + d["fat"]
    }

    menu_json = json.dumps(menu_data, ensure_ascii=False)
    cursor.execute("""
        UPDATE weekly_menus 
        SET menu_data = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (menu_json, row["id"]))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "dish": new_dish,
        "new_dish": new_dish,
        "menu": menu_data,
        "day_totals": days[day_key]["totals"],
        "message": f"Sugestão trocada com sucesso para: {new_dish['name']}! ✨"
    }

def log_menu_dish_to_diary(user_id: int, date_str: str, meal_type: str, dish_name: str) -> Dict[str, Any]:
    """Lança um prato do cardápio semanal diretamente no diário do dia."""
    found_dish = None
    for m_type, dishes in DISH_CATALOG.items():
        if m_type == "cheat_options":
            continue
        for d in dishes:
            if d["name"] == dish_name:
                found_dish = d
                break
        if found_dish:
            break

    if not found_dish:
        found_dish = {
            "name": dish_name,
            "calories": 400.0,
            "protein": 25.0,
            "carbs": 40.0,
            "fat": 12.0
        }

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO diary_entries (user_id, date, meal_type, food_name, amount_grams, calories, protein, carbs, fat, fiber, notes)
        VALUES (?, ?, ?, ?, 250, ?, ?, ?, ?, 3.0, 'Adicionado via Assistente de Cardápio Semanal')
    """, (user_id, date_str, meal_type, found_dish["name"], found_dish["calories"], found_dish["protein"], found_dish["carbs"], found_dish["fat"]))

    entry_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO user_points (user_id, date, action_type, points, description)
        VALUES (?, ?, 'meal_logged', 10, ?)
    """, (user_id, date_str, f"Refeição do Cardápio: {found_dish['name']}"))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "entry_id": entry_id,
        "message": f"'{found_dish['name']}' lançado no seu diário com sucesso (+10 pts)! 🥗"
    }
