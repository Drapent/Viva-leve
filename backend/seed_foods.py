import sqlite3
from database import get_connection, init_db

POPULAR_BRAZILIAN_FOODS = [
    # Cereais, Pães e Tubérculos
    {"name": "Arroz Branco Cozido", "category": "Cereais e Grãos", "portion_name": "1 colher de sopa (25g)", "portion_grams": 25.0, "calories": 130.0, "protein": 2.5, "carbs": 28.2, "fat": 0.2, "fiber": 1.6},
    {"name": "Arroz Integral Cozido", "category": "Cereais e Grãos", "portion_name": "1 colher de sopa (25g)", "portion_grams": 25.0, "calories": 124.0, "protein": 2.6, "carbs": 25.8, "fat": 1.0, "fiber": 2.7},
    {"name": "Feijão Carioca Cozido", "category": "Leguminosas", "portion_name": "1 concha média (100g)", "portion_grams": 100.0, "calories": 76.0, "protein": 4.8, "carbs": 13.6, "fat": 0.5, "fiber": 8.5},
    {"name": "Feijão Preto Cozido", "category": "Leguminosas", "portion_name": "1 concha média (100g)", "portion_grams": 100.0, "calories": 77.0, "protein": 4.5, "carbs": 14.0, "fat": 0.5, "fiber": 8.4},
    {"name": "Lentilha Cozida", "category": "Leguminosas", "portion_name": "1 concha (100g)", "portion_grams": 100.0, "calories": 93.0, "protein": 6.3, "carbs": 16.3, "fat": 0.4, "fiber": 3.8},
    {"name": "Grão-de-Bico Cozido", "category": "Leguminosas", "portion_name": "1 concha (100g)", "portion_grams": 100.0, "calories": 128.0, "protein": 7.0, "carbs": 21.0, "fat": 2.2, "fiber": 5.4},
    {"name": "Pão Francês", "category": "Pães", "portion_name": "1 unidade (50g)", "portion_grams": 50.0, "calories": 300.0, "protein": 8.0, "carbs": 58.6, "fat": 3.1, "fiber": 2.3},
    {"name": "Pão de Forma Integral", "category": "Pães", "portion_name": "2 fatias (50g)", "portion_grams": 50.0, "calories": 240.0, "protein": 9.4, "carbs": 44.0, "fat": 3.0, "fiber": 6.8},
    {"name": "Tapioca (Goma Pronta)", "category": "Farinhas e Massas", "portion_name": "1 unidade média (60g)", "portion_grams": 60.0, "calories": 240.0, "protein": 0.1, "carbs": 60.0, "fat": 0.0, "fiber": 0.4},
    {"name": "Cuscuz de Milho Cozido", "category": "Cereais e Grãos", "portion_name": "1 fatia/porção (100g)", "portion_grams": 100.0, "calories": 113.0, "protein": 2.2, "carbs": 25.4, "fat": 0.6, "fiber": 1.8},
    {"name": "Aveia em Flocos", "category": "Cereais e Grãos", "portion_name": "2 colheres de sopa (30g)", "portion_grams": 30.0, "calories": 394.0, "protein": 13.9, "carbs": 66.6, "fat": 8.5, "fiber": 9.1},
    {"name": "Batata Doce Cozida", "category": "Tubérculos", "portion_name": "1 unidade média (120g)", "portion_grams": 120.0, "calories": 77.0, "protein": 0.6, "carbs": 18.4, "fat": 0.1, "fiber": 2.2},
    {"name": "Batata Inglesa Cozida", "category": "Tubérculos", "portion_name": "1 unidade média (100g)", "portion_grams": 100.0, "calories": 52.0, "protein": 1.2, "carbs": 11.9, "fat": 0.0, "fiber": 1.3},
    {"name": "Mandioca / Aipim Cozido", "category": "Tubérculos", "portion_name": "1 pedaço médio (100g)", "portion_grams": 100.0, "calories": 125.0, "protein": 0.6, "carbs": 30.1, "fat": 0.3, "fiber": 1.6},
    {"name": "Macarrão Tradicional Cozido", "category": "Farinhas e Massas", "portion_name": "1 prato raso (140g)", "portion_grams": 140.0, "calories": 102.0, "protein": 3.0, "carbs": 21.0, "fat": 0.4, "fiber": 1.1},
    {"name": "Macarrão Integral Cozido", "category": "Farinhas e Massas", "portion_name": "1 prato raso (140g)", "portion_grams": 140.0, "calories": 124.0, "protein": 5.3, "carbs": 26.5, "fat": 0.9, "fiber": 3.9},

    # Carnes, Aves, Peixes e Ovos
    {"name": "Peito de Frango Grelhado", "category": "Carnes e Aves", "portion_name": "1 filé médio (100g)", "portion_grams": 100.0, "calories": 159.0, "protein": 32.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Sobrecoxa de Frango sem Pele Assada", "category": "Carnes e Aves", "portion_name": "1 pedaço (100g)", "portion_grams": 100.0, "calories": 180.0, "protein": 24.5, "carbs": 0.0, "fat": 9.2, "fiber": 0.0},
    {"name": "Carne Bovina Moída (Patinho)", "category": "Carnes e Aves", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 219.0, "protein": 35.9, "carbs": 0.0, "fat": 7.3, "fiber": 0.0},
    {"name": "Filé Mignon Bovino Grelhado", "category": "Carnes e Aves", "portion_name": "1 bife médio (100g)", "portion_grams": 100.0, "calories": 220.0, "protein": 32.8, "carbs": 0.0, "fat": 8.8, "fiber": 0.0},
    {"name": "Alcatra Grelhada", "category": "Carnes e Aves", "portion_name": "1 bife médio (100g)", "portion_grams": 100.0, "calories": 241.0, "protein": 31.9, "carbs": 0.0, "fat": 11.6, "fiber": 0.0},
    {"name": "Picanha Bovina sem Gordura", "category": "Carnes e Aves", "portion_name": "1 fatia média (100g)", "portion_grams": 100.0, "calories": 238.0, "protein": 28.5, "carbs": 0.0, "fat": 12.0, "fiber": 0.0},
    {"name": "Picanha Bovina com Gordura", "category": "Carnes e Aves", "portion_name": "1 fatia média (100g)", "portion_grams": 100.0, "calories": 330.0, "protein": 24.0, "carbs": 0.0, "fat": 26.0, "fiber": 0.0},
    {"name": "Ovo de Galinha Cozido", "category": "Ovos", "portion_name": "1 unidade grande (50g)", "portion_grams": 50.0, "calories": 146.0, "protein": 13.3, "carbs": 0.6, "fat": 9.5, "fiber": 0.0},
    {"name": "Ovo de Galinha Frito", "category": "Ovos", "portion_name": "1 unidade grande (50g)", "portion_grams": 50.0, "calories": 240.0, "protein": 15.6, "carbs": 1.2, "fat": 18.6, "fiber": 0.0},
    {"name": "Clara de Ovo Cozida", "category": "Ovos", "portion_name": "1 clara (30g)", "portion_grams": 30.0, "calories": 48.0, "protein": 10.9, "carbs": 0.7, "fat": 0.2, "fiber": 0.0},
    {"name": "Tilápia / Peixe Branco Grelhado", "category": "Pescados", "portion_name": "1 filé médio (100g)", "portion_grams": 100.0, "calories": 128.0, "protein": 26.1, "carbs": 0.0, "fat": 2.7, "fiber": 0.0},
    {"name": "Salmão Grelhado", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 229.0, "protein": 24.0, "carbs": 0.0, "fat": 14.5, "fiber": 0.0},
    {"name": "Atum Sólido em Água", "category": "Pescados", "portion_name": "1 lata drenada (120g)", "portion_grams": 120.0, "calories": 116.0, "protein": 26.0, "carbs": 0.0, "fat": 0.8, "fiber": 0.0},

    # Laticínios e Derivados
    {"name": "Leite Desnatado", "category": "Laticínios", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 35.0, "protein": 3.3, "carbs": 5.0, "fat": 0.2, "fiber": 0.0},
    {"name": "Leite Integral", "category": "Laticínios", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 60.0, "protein": 3.1, "carbs": 4.6, "fat": 3.2, "fiber": 0.0},
    {"name": "Iogurte Natural Desnatado", "category": "Laticínios", "portion_name": "1 pote (160g)", "portion_grams": 160.0, "calories": 41.0, "protein": 3.8, "carbs": 5.8, "fat": 0.3, "fiber": 0.0},
    {"name": "Queijo Minas Frescal", "category": "Laticínios", "portion_name": "1 fatia média (30g)", "portion_grams": 30.0, "calories": 264.0, "protein": 17.4, "carbs": 3.2, "fat": 20.2, "fiber": 0.0},
    {"name": "Queijo Cottage", "category": "Laticínios", "portion_name": "2 colheres de sopa (50g)", "portion_grams": 50.0, "calories": 98.0, "protein": 11.1, "carbs": 3.4, "fat": 4.3, "fiber": 0.0},
    {"name": "Queijo Mussarela", "category": "Laticínios", "portion_name": "1 fatia (20g)", "portion_grams": 20.0, "calories": 328.0, "protein": 22.6, "carbs": 3.0, "fat": 25.1, "fiber": 0.0},
    {"name": "Requeijão Cremoso Light", "category": "Laticínios", "portion_name": "1 colher de sopa (30g)", "portion_grams": 30.0, "calories": 170.0, "protein": 9.3, "carbs": 4.5, "fat": 12.0, "fiber": 0.0},

    # Frutas
    {"name": "Banana Prata", "category": "Frutas", "portion_name": "1 unidade média (70g)", "portion_grams": 70.0, "calories": 98.0, "protein": 1.3, "carbs": 26.0, "fat": 0.1, "fiber": 2.0},
    {"name": "Maçã Fuji com Casca", "category": "Frutas", "portion_name": "1 unidade média (130g)", "portion_grams": 130.0, "calories": 56.0, "protein": 0.3, "carbs": 15.2, "fat": 0.2, "fiber": 1.3},
    {"name": "Mamão Papaia", "category": "Frutas", "portion_name": "1/2 unidade (140g)", "portion_grams": 140.0, "calories": 40.0, "protein": 0.5, "carbs": 10.4, "fat": 0.1, "fiber": 1.0},
    {"name": "Morango Fresco", "category": "Frutas", "portion_name": "5 unidades (100g)", "portion_grams": 100.0, "calories": 30.0, "protein": 0.9, "carbs": 6.8, "fat": 0.3, "fiber": 1.7},
    {"name": "Abacaxi Pérola", "category": "Frutas", "portion_name": "1 fatia média (80g)", "portion_grams": 80.0, "calories": 48.0, "protein": 0.9, "carbs": 12.3, "fat": 0.1, "fiber": 1.0},
    {"name": "Laranja Pera", "category": "Frutas", "portion_name": "1 unidade média (120g)", "portion_grams": 120.0, "calories": 37.0, "protein": 1.0, "carbs": 8.9, "fat": 0.1, "fiber": 0.8},
    {"name": "Melancia", "category": "Frutas", "portion_name": "1 fatia média (200g)", "portion_grams": 200.0, "calories": 33.0, "protein": 0.9, "carbs": 8.1, "fat": 0.0, "fiber": 0.1},
    {"name": "Abacate", "category": "Frutas", "portion_name": "2 colheres de sopa (50g)", "portion_grams": 50.0, "calories": 96.0, "protein": 1.2, "carbs": 6.0, "fat": 8.4, "fiber": 6.3},
    {"name": "Uva Thompson / Roxa", "category": "Frutas", "portion_name": "1 cacho pequeno (100g)", "portion_grams": 100.0, "calories": 53.0, "protein": 0.7, "carbs": 13.6, "fat": 0.2, "fiber": 0.9},
    {"name": "Polpa de Açaí Pura (sem xarope)", "category": "Frutas", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 58.0, "protein": 0.8, "carbs": 6.2, "fat": 3.9, "fiber": 2.6},

    # Verduras e Legumes
    {"name": "Alface Americana / Crespa", "category": "Verduras e Legumes", "portion_name": "1 prato de sobremesa (50g)", "portion_grams": 50.0, "calories": 14.0, "protein": 1.3, "carbs": 2.4, "fat": 0.2, "fiber": 1.8},
    {"name": "Tomate Salada", "category": "Verduras e Legumes", "portion_name": "4 fatias (80g)", "portion_grams": 80.0, "calories": 15.0, "protein": 1.1, "carbs": 3.1, "fat": 0.2, "fiber": 1.2},
    {"name": "Cenoura Crua Ralada", "category": "Verduras e Legumes", "portion_name": "2 colheres de sopa (50g)", "portion_grams": 50.0, "calories": 34.0, "protein": 1.3, "carbs": 7.7, "fat": 0.2, "fiber": 3.2},
    {"name": "Brócolis Cozido", "category": "Verduras e Legumes", "portion_name": "4 floretes (80g)", "portion_grams": 80.0, "calories": 25.0, "protein": 2.1, "carbs": 4.4, "fat": 0.5, "fiber": 3.4},
    {"name": "Couve Manteiga Refogada", "category": "Verduras e Legumes", "portion_name": "2 colheres de sopa (50g)", "portion_grams": 50.0, "calories": 90.0, "protein": 1.7, "carbs": 8.7, "fat": 6.6, "fiber": 3.1},
    {"name": "Abobrinha Italiana Cozida", "category": "Verduras e Legumes", "portion_name": "3 colheres de sopa (80g)", "portion_grams": 80.0, "calories": 15.0, "protein": 1.1, "carbs": 3.0, "fat": 0.2, "fiber": 1.6},
    {"name": "Beterraba Cozida", "category": "Verduras e Legumes", "portion_name": "2 fatias médias (60g)", "portion_grams": 60.0, "calories": 32.0, "protein": 1.3, "carbs": 7.2, "fat": 0.1, "fiber": 1.9},

    # Gorduras e Oleaginosas
    {"name": "Azeite de Oliva Extra Virgem", "category": "Gorduras e Óleos", "portion_name": "1 colher de sopa (13ml)", "portion_grams": 13.0, "calories": 884.0, "protein": 0.0, "carbs": 0.0, "fat": 100.0, "fiber": 0.0},
    {"name": "Manteiga com Sal", "category": "Gorduras e Óleos", "portion_name": "1 ponta de faca (10g)", "portion_grams": 10.0, "calories": 726.0, "protein": 0.4, "carbs": 0.1, "fat": 82.4, "fiber": 0.0},
    {"name": "Pasta de Amendoim Integral", "category": "Gorduras e Óleos", "portion_name": "1 colher de sopa (20g)", "portion_grams": 20.0, "calories": 588.0, "protein": 25.0, "carbs": 20.0, "fat": 50.0, "fiber": 6.0},
    {"name": "Castanha-de-Caju Torrada", "category": "Oleaginosas", "portion_name": "1 punhado pequeno (25g)", "portion_grams": 25.0, "calories": 570.0, "protein": 18.5, "carbs": 29.1, "fat": 46.3, "fiber": 3.7},
    {"name": "Castanha-do-Pará / Brasil", "category": "Oleaginosas", "portion_name": "2 unidades (10g)", "portion_grams": 10.0, "calories": 656.0, "protein": 14.3, "carbs": 12.3, "fat": 66.4, "fiber": 7.5},

    # Suplementos e Diversos
    {"name": "Whey Protein 80% (Concentrado)", "category": "Suplementos", "portion_name": "1 scoop medidor (30g)", "portion_grams": 30.0, "calories": 400.0, "protein": 80.0, "carbs": 7.0, "fat": 6.0, "fiber": 0.0},
    {"name": "Creatina Monohidratada", "category": "Suplementos", "portion_name": "1 dosador (5g)", "portion_grams": 5.0, "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Café Preto sem Açúcar", "category": "Bebidas", "portion_name": "1 xícara (100ml)", "portion_grams": 100.0, "calories": 2.0, "protein": 0.1, "carbs": 0.3, "fat": 0.0, "fiber": 0.0},
    {"name": "Açúcar Branco Refinado", "category": "Açúcares e Doces", "portion_name": "1 colher de sopa (15g)", "portion_grams": 15.0, "calories": 387.0, "protein": 0.0, "carbs": 99.5, "fat": 0.0, "fiber": 0.0}
]

def seed_foods():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM foods WHERE is_custom = 0")
    count = cursor.fetchone()["count"]

    if count == 0:
        for food in POPULAR_BRAZILIAN_FOODS:
            cursor.execute("""
                INSERT INTO foods (name, category, portion_name, portion_grams, calories, protein, carbs, fat, fiber, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                food["name"], food["category"], food["portion_name"], food["portion_grams"],
                food["calories"], food["protein"], food["carbs"], food["fat"], food["fiber"]
            ))
        conn.commit()
        print(f"Inseridos {len(POPULAR_BRAZILIAN_FOODS)} alimentos da base TACO/IBGE!")
    else:
        print(f"Base de alimentos já possui {count} registros.")

    conn.close()

if __name__ == "__main__":
    seed_foods()
