import json
from database import get_connection, init_db

CURATED_RESTAURANTS = [
    {
        "name": "Sabor do Campo (Self-Service & Grelhados)",
        "category": "Self-Service",
        "cuisine": "Brasileira / A Quilo",
        "address": "Av. Principal, 450 - Centro",
        "latitude": -23.55052,
        "longitude": -46.633308,
        "price": "$$",
        "rating": 4.7,
        "tips": "No self-service, monte o prato seguindo a regra visual: 50% saladas variadas, 25% proteína magra grelhada e 25% carboidratos limpos (arroz, feijão ou batata).",
        "diet_dishes": [
            {
                "name": "Prato Equilibrado da Casa",
                "desc": "Peito de frango grelhado (150g) + 1 concha de feijão + 3 colheres de arroz integral + mix generoso de folhas, tomate e brócolis cozido.",
                "calories": 480,
                "protein": "42g",
                "carbs": "45g",
                "fat": "8g",
                "tag": "Alta Saciedade"
            },
            {
                "name": "Filé de Tilápia com Legumes no Vapor",
                "desc": "Filé de peixe grelhado com azeite discreto, acompanhado de cenoura, abobrinha e couve-flor no vapor.",
                "calories": 360,
                "protein": "38g",
                "carbs": "12g",
                "fat": "10g",
                "tag": "Low Carb"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Feijoada Completa com Torresmo e Couve",
                "desc": "Feijoada tradicional com costelinha, paio, arroz branco, farofa de bacon e torresmo crocante.",
                "calories": 1350,
                "protein": "55g",
                "carbs": "95g",
                "fat": "72g",
                "damage_control": "Beba 1 copo grande de água com limão antes de começar. Evite repetir a farofa e o torresmo e prefira refrigerante zero."
            },
            {
                "name": "Picanha na Chapa com Batata Frita e Queijo Coalho",
                "desc": "Picanha suculenta grelhada na manteiga com porção generosa de fritas e queijo coalho tostado.",
                "calories": 1200,
                "protein": "60g",
                "carbs": "55g",
                "fat": "78g",
                "damage_control": "Comece comendo a picanha e os queijos para ter saciedade proteica antes de se empanturrar com a batata frita."
            }
        ]
    },
    {
        "name": "Kyoto Sushi Lounge",
        "category": "Japonês",
        "cuisine": "Japonesa",
        "address": "Rua dos Pinheiros, 820",
        "latitude": -23.56150,
        "longitude": -46.68200,
        "price": "$$$",
        "rating": 4.9,
        "tips": "O peixe cru é uma excelente fonte de proteína pura e ômega-3. No foco, evite peças empanadas (hot roll) e molho tarê (que é puro açúcar).",
        "diet_dishes": [
            {
                "name": "Combinado Sashimi Puro (15 fatias)",
                "desc": "Sashimi misto de salmão, atum fresco e peixe branco com sunomono (pepino) e gengibre.",
                "calories": 320,
                "protein": "45g",
                "carbs": "4g",
                "fat": "12g",
                "tag": "Proteína Máxima"
            },
            {
                "name": "Temaki de Salmão Simples (Sem Arroz) ou com Pouco Arroz",
                "desc": "Alga nori crocante recheada com salmão em cubos e cebolinha fresca.",
                "calories": 210,
                "protein": "26g",
                "carbs": "3g",
                "fat": "9g",
                "tag": "Keto / Cetogênica"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Rodízio Completo com Hot Roll e Salmão Flambado com Cream Cheese",
                "desc": "Variedade irrestrita incluindo hot rolls fritos, uramakis especiais com maionese picante, shimeji na manteiga e tarê.",
                "calories": 1600,
                "protein": "65g",
                "carbs": "160g",
                "fat": "68g",
                "damage_control": "O rodízio japonês acumula muito sódio por causa do shoyu e calorias nos molhos doces. Peça shoyu light com redução de sódio e intercale copos de água."
            }
        ]
    },
    {
        "name": "Brava Burger & Beer",
        "category": "Hamburgueria",
        "cuisine": "Hamburgueria Artesanal",
        "address": "Rua Augusta, 1420",
        "latitude": -23.55320,
        "longitude": -46.65800,
        "price": "$$",
        "rating": 4.8,
        "tips": "Mesmo em hamburgueria artesanal dá para manter a dieta pedindo hambúrguer duplo sem pão (no prato com salada) ou escolhendo peito de frango.",
        "diet_dishes": [
            {
                "name": "Burger Salad Fit",
                "desc": "2 blends bovinos grelhados de 150g cada, queijo prato discreto, alface, tomate, picles no prato com salada verde.",
                "calories": 520,
                "protein": "54g",
                "carbs": "6g",
                "fat": "28g",
                "tag": "Low Carb / High Protein"
            },
            {
                "name": "Chicken Burger Simples",
                "desc": "Filé de frango grelhado no pão brioche com tomate, rúcula e mostarda dijon (sem maionese extra).",
                "calories": 420,
                "protein": "38g",
                "carbs": "36g",
                "fat": "11g",
                "tag": "Equilibrado"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Grand Smash Duplo com Bacon Caramelizado e Cheddar Inglês",
                "desc": "Dois hambúrgueres de 160g smash, piscina de cheddar cremoso, fatias crocantes de bacon, maionese trufada e batatas rústicas com páprica.",
                "calories": 1450,
                "protein": "58g",
                "carbs": "88g",
                "fat": "92g",
                "damage_control": "Opte por água com gás ou refrigerante zero. Saboreie cada mordida devagar e não coma a porção de batatas inteira se já estiver satisfeito."
            }
        ]
    },
    {
        "name": "Pizzaria Don Vincenzo",
        "category": "Pizzaria",
        "cuisine": "Italiana / Forno a Lenha",
        "address": "Alameda dos Anapurus, 1100 - Moema",
        "latitude": -23.60500,
        "longitude": -46.66100,
        "price": "$$$",
        "rating": 4.8,
        "tips": "Pizzas de massa fina com coberturas de vegetais e queijos magros ou rúcula com tomate seco são muito mais leves do que bordas recheadas de catupiry.",
        "diet_dishes": [
            {
                "name": "2 Fatias de Pizza de Rúcula com Tomate Seco (Massa Fina)",
                "desc": "Massa artesanal fina fermentada por 48h, molho de tomate pelado, mussarela discreta, rúcula fresca e tomate seco.",
                "calories": 440,
                "protein": "22g",
                "carbs": "46g",
                "fat": "16g",
                "tag": "Porção Controlada"
            },
            {
                "name": "2 Fatias de Marguerita Tradicional",
                "desc": "Molho de tomate artesanal, manjericão fresco, queijo de búfala e azeite extravirgem.",
                "calories": 410,
                "protein": "18g",
                "carbs": "44g",
                "fat": "15g",
                "tag": "Clássico Leve"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Pizza Quatro Queijos & Calabresa Especial com Borda de Catupiry",
                "desc": "4 a 5 fatias generosas com gorgonzola, provolone, parmesão, mussarela, calabresa artesanal defumada e borda vulcão de catupiry.",
                "calories": 1800,
                "protein": "70g",
                "carbs": "160g",
                "fat": "95g",
                "damage_control": "Coma uma salada fresca antes da primeira fatia. A fibra ajuda a reduzir a velocidade de absorção da glicose e evita pico excessivo de fome depois."
            }
        ]
    },
    {
        "name": "Verde & Grão Fresh Food",
        "category": "Saudável / Fit",
        "cuisine": "Saladas, Bowls & Açaí",
        "address": "Rua Oscar Freire, 320",
        "latitude": -23.56300,
        "longitude": -46.66900,
        "price": "$$",
        "rating": 4.9,
        "tips": "Lugar perfeito para bater meta de micronutrientes e fibras sem furar calorias. Fique atento apenas aos molhos prontos cremosos e granola doce.",
        "diet_dishes": [
            {
                "name": "Poke Tropical de Salmão e Quinoa",
                "desc": "Salmão fresco em cubos, quinoa real, edamame, manga, pepino, gergelim e molho ponzu leve cítrico.",
                "calories": 430,
                "protein": "34g",
                "carbs": "42g",
                "fat": "12g",
                "tag": "100% Fit"
            },
            {
                "name": "Bowl de Frango Crocante com Batata Doce e Abacate",
                "desc": "Tiras de frango grelhado na crosta de chia, cubos de batata doce assada, folhas nobres e 40g de abacate com limão.",
                "calories": 470,
                "protein": "40g",
                "carbs": "38g",
                "fat": "15g",
                "tag": "Hipertrofia Limpa"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Tigela de Açaí Especial 500ml com Nutella, Leite em Pó e Morango",
                "desc": "Açaí cremoso batido com guaraná, generosa camada de Nutella pura, leite Ninho e paçoca de amendoim.",
                "calories": 950,
                "protein": "16g",
                "carbs": "135g",
                "fat": "36g",
                "damage_control": "Uma refeição doce perfeita para o pós-treino intenso de pernas! Ajuda a repor estoques de glicogênio muscular com rápida digestão."
            }
        ]
    },
    {
        "name": "Al-Basha Gastronomia Árabe",
        "category": "Árabe",
        "cuisine": "Árabe & Mediterrânea",
        "address": "Av. Ibirapuera, 2200",
        "latitude": -23.59700,
        "longitude": -46.65700,
        "price": "$$",
        "rating": 4.7,
        "tips": "A culinária árabe é uma das mais amigáveis para a dieta: kafta grelhada, quibe assado, homus e tabule são ricos em nutrientes e proteínas.",
        "diet_dishes": [
            {
                "name": "Kafta Bovina Grelhada (2 espetos) com Tabule e Homus",
                "desc": "Espetos de carne bovina magra grelhada com hortelã e especiarias, salada fresca de tabule e 1 colher de pasta de grão-de-bico.",
                "calories": 460,
                "protein": "44g",
                "carbs": "22g",
                "fat": "18g",
                "tag": "Proteico & Leve"
            },
            {
                "name": "Quibe Assado Recheado com Salada Fattoush",
                "desc": "Fatia generosa de quibe assado ao forno com carne moída magra e salada de folhas com rabanete e sumac.",
                "calories": 390,
                "protein": "32g",
                "carbs": "28g",
                "fat": "12g",
                "tag": "Equilibrado"
            }
        ],
        "cheat_dishes": [
            {
                "name": "Festival de Esfihas Folhadas, Quibe Frito e Charutinho",
                "desc": "4 esfihas abertas de carne com queijo, 2 quibes fritos recheados com catupiry e porção de charutinho de folha de uva na manteiga.",
                "calories": 1400,
                "protein": "52g",
                "carbs": "120g",
                "fat": "76g",
                "damage_control": "Evite refrigerantes normais; prefira água ou chá gelado sem açúcar. Os folhados têm bastante manteiga, aproveite saboreando com calma."
            }
        ]
    }
]

def seed_restaurants():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM restaurants")
    count = cursor.fetchone()["count"]

    if count == 0:
        for r in CURATED_RESTAURANTS:
            cursor.execute("""
                INSERT INTO restaurants (name, category, cuisine, address, latitude, longitude, price, rating, diet_dishes, cheat_dishes, tips)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["name"], r["category"], r["cuisine"], r["address"],
                r["latitude"], r["longitude"], r["price"], r["rating"],
                json.dumps(r["diet_dishes"], ensure_ascii=False),
                json.dumps(r["cheat_dishes"], ensure_ascii=False),
                r["tips"]
            ))
        conn.commit()
        print(f"Inseridos {len(CURATED_RESTAURANTS)} restaurantes curados com opções de Dieta e Dia do Lixo!")
    else:
        print(f"Base de restaurantes já possui {count} registros.")

    conn.close()

if __name__ == "__main__":
    seed_restaurants()
