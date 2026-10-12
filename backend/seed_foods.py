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
    {"name": "Whey Protein Isolado 90%", "category": "Suplementos", "portion_name": "1 scoop (30g)", "portion_grams": 30.0, "calories": 370.0, "protein": 90.0, "carbs": 1.0, "fat": 0.5, "fiber": 0.0},
    {"name": "Creatina Monohidratada", "category": "Suplementos", "portion_name": "1 dosador (5g)", "portion_grams": 5.0, "calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Barra de Proteína (Média Nacional)", "category": "Suplementos", "portion_name": "1 barra (40g)", "portion_grams": 40.0, "calories": 375.0, "protein": 35.0, "carbs": 30.0, "fat": 12.5, "fiber": 7.5},
    {"name": "Café Preto sem Açúcar", "category": "Bebidas", "portion_name": "1 xícara (100ml)", "portion_grams": 100.0, "calories": 2.0, "protein": 0.1, "carbs": 0.3, "fat": 0.0, "fiber": 0.0},
    {"name": "Açúcar Branco Refinado", "category": "Açúcares e Doces", "portion_name": "1 colher de sopa (15g)", "portion_grams": 15.0, "calories": 387.0, "protein": 0.0, "carbs": 99.5, "fat": 0.0, "fiber": 0.0},
    {"name": "Doce de Leite Pastoso", "category": "Açúcares e Doces", "portion_name": "1 colher de sopa (20g)", "portion_grams": 20.0, "calories": 325.0, "protein": 7.0, "carbs": 55.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Chocolate Meio Amargo 70%", "category": "Açúcares e Doces", "portion_name": "3 quadradinhos (25g)", "portion_grams": 25.0, "calories": 560.0, "protein": 8.8, "carbs": 46.0, "fat": 39.0, "fiber": 11.2},
    {"name": "Água de Coco Natural", "category": "Bebidas", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 20.0, "protein": 0.2, "carbs": 4.8, "fat": 0.1, "fiber": 0.5},
    {"name": "Suco de Laranja Integral", "category": "Bebidas", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 45.0, "protein": 0.7, "carbs": 10.5, "fat": 0.1, "fiber": 0.2},

    # --- FAST FOOD & LANCHES OFICIAIS (Tabelas Oficiais das Redes) ---
    # McDonald's
    {"name": "McDonald's - Big Mac", "category": "Fast Food", "portion_name": "1 sanduíche (215g)", "portion_grams": 215.0, "calories": 234.0, "protein": 12.1, "carbs": 20.5, "fat": 11.6, "fiber": 1.4},
    {"name": "McDonald's - Quarteirão com Queijo", "category": "Fast Food", "portion_name": "1 sanduíche (200g)", "portion_grams": 200.0, "calories": 261.5, "protein": 15.5, "carbs": 19.0, "fat": 14.0, "fiber": 1.0},
    {"name": "McDonald's - McChicken", "category": "Fast Food", "portion_name": "1 sanduíche (180g)", "portion_grams": 180.0, "calories": 272.0, "protein": 11.7, "carbs": 25.0, "fat": 13.3, "fiber": 1.1},
    {"name": "McDonald's - Cheeseburger", "category": "Fast Food", "portion_name": "1 sanduíche (115g)", "portion_grams": 115.0, "calories": 260.0, "protein": 13.9, "carbs": 28.7, "fat": 10.4, "fiber": 1.3},
    {"name": "McDonald's - McFritas Média", "category": "Fast Food", "portion_name": "1 porção (105g)", "portion_grams": 105.0, "calories": 274.0, "protein": 3.8, "carbs": 36.2, "fat": 13.3, "fiber": 3.8},
    {"name": "McDonald's - McNuggets (10 un)", "category": "Fast Food", "portion_name": "10 unidades (165g)", "portion_grams": 165.0, "calories": 254.5, "protein": 14.5, "carbs": 15.8, "fat": 14.5, "fiber": 0.6},
    {"name": "McDonald's - Casquinha de Baunilha", "category": "Fast Food", "portion_name": "1 unidade (100g)", "portion_grams": 100.0, "calories": 170.0, "protein": 4.0, "carbs": 29.0, "fat": 4.5, "fiber": 0.0},
    {"name": "McDonald's - McFlurry Ovomaltine", "category": "Fast Food", "portion_name": "1 copo (180g)", "portion_grams": 180.0, "calories": 228.0, "protein": 4.4, "carbs": 36.1, "fat": 7.2, "fiber": 0.5},

    # Burger King
    {"name": "Burger King - Whopper", "category": "Fast Food", "portion_name": "1 sanduíche (290g)", "portion_grams": 290.0, "calories": 226.5, "protein": 9.7, "carbs": 18.3, "fat": 13.1, "fiber": 1.4},
    {"name": "Burger King - BK Cheddar", "category": "Fast Food", "portion_name": "1 sanduíche (185g)", "portion_grams": 185.0, "calories": 281.0, "protein": 13.0, "carbs": 19.5, "fat": 16.8, "fiber": 1.1},
    {"name": "Burger King - Batata Frita Média", "category": "Fast Food", "portion_name": "1 porção (120g)", "portion_grams": 120.0, "calories": 266.7, "protein": 3.3, "carbs": 36.7, "fat": 12.5, "fiber": 3.3},
    {"name": "Burger King - Onion Rings Média", "category": "Fast Food", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 315.0, "protein": 3.0, "carbs": 38.0, "fat": 17.0, "fiber": 3.0},

    # Subway
    {"name": "Subway - Frango Teriyaki 15cm", "category": "Fast Food", "portion_name": "1 sanduíche (230g)", "portion_grams": 230.0, "calories": 160.9, "protein": 11.3, "carbs": 23.5, "fat": 2.2, "fiber": 2.2},
    {"name": "Subway - B.M.T. Italiano 15cm", "category": "Fast Food", "portion_name": "1 sanduíche (220g)", "portion_grams": 220.0, "calories": 186.4, "protein": 9.1, "carbs": 20.0, "fat": 7.7, "fiber": 1.8},
    {"name": "Subway - Frango Defumado Cream Cheese 15cm", "category": "Fast Food", "portion_name": "1 sanduíche (240g)", "portion_grams": 240.0, "calories": 172.9, "protein": 11.7, "carbs": 18.8, "fat": 5.4, "fiber": 1.7},

    # Habib's
    {"name": "Habib's - Esfiha de Carne", "category": "Fast Food", "portion_name": "1 unidade (60g)", "portion_grams": 60.0, "calories": 241.7, "protein": 9.2, "carbs": 30.0, "fat": 9.7, "fiber": 1.7},
    {"name": "Habib's - Esfiha de Queijo", "category": "Fast Food", "portion_name": "1 unidade (60g)", "portion_grams": 60.0, "calories": 275.0, "protein": 10.3, "carbs": 26.7, "fat": 14.2, "fiber": 1.3},
    {"name": "Habib's - Kibe Frito com Carne", "category": "Fast Food", "portion_name": "1 unidade (75g)", "portion_grams": 75.0, "calories": 246.7, "protein": 11.3, "carbs": 21.3, "fat": 13.1, "fiber": 2.7},

    # Pizzas e Lanches Típicos Brasileiros
    {"name": "Pizza - Fatia Calabresa", "category": "Pizzas e Massas", "portion_name": "1 fatia média (100g)", "portion_grams": 100.0, "calories": 270.0, "protein": 11.5, "carbs": 28.0, "fat": 12.5, "fiber": 1.8},
    {"name": "Pizza - Fatia Mussarela", "category": "Pizzas e Massas", "portion_name": "1 fatia média (100g)", "portion_grams": 100.0, "calories": 260.0, "protein": 12.0, "carbs": 26.0, "fat": 12.0, "fiber": 1.5},
    {"name": "Pizza - Fatia Frango com Catupiry", "category": "Pizzas e Massas", "portion_name": "1 fatia média (110g)", "portion_grams": 110.0, "calories": 250.0, "protein": 12.7, "carbs": 24.5, "fat": 11.4, "fiber": 1.6},
    {"name": "Pastel de Feira de Carne", "category": "Salgados", "portion_name": "1 unidade (120g)", "portion_grams": 120.0, "calories": 316.7, "protein": 9.2, "carbs": 31.7, "fat": 16.7, "fiber": 1.7},
    {"name": "Coxinha de Frango com Catupiry", "category": "Salgados", "portion_name": "1 unidade grande (130g)", "portion_grams": 130.0, "calories": 300.0, "protein": 9.2, "carbs": 32.3, "fat": 14.6, "fiber": 1.9},
    {"name": "Pão de Queijo Mineiro", "category": "Salgados", "portion_name": "1 unidade média (50g)", "portion_grams": 50.0, "calories": 330.0, "protein": 7.6, "carbs": 38.0, "fat": 17.0, "fiber": 1.6},
    {"name": "Açaí com Banana e Granola", "category": "Sobremesas e Lanches", "portion_name": "1 tigela (300g)", "portion_grams": 300.0, "calories": 140.0, "protein": 2.0, "carbs": 24.0, "fat": 4.0, "fiber": 2.3},

    # Outback & Giraffas & Popeyes
    {"name": "Outback - Junior Ribs (Meia Costela BBQ)", "category": "Restaurantes", "portion_name": "1 porção (300g)", "portion_grams": 300.0, "calories": 216.7, "protein": 15.0, "carbs": 7.3, "fat": 14.0, "fiber": 0.3},
    {"name": "Outback - Aussie Cheese Fries (Individual)", "category": "Restaurantes", "portion_name": "1 porção (150g)", "portion_grams": 150.0, "calories": 326.7, "protein": 9.3, "carbs": 25.3, "fat": 21.3, "fiber": 2.7},
    {"name": "Giraffas - Prato Bife a Cavalo", "category": "Restaurantes", "portion_name": "1 prato executivo (350g)", "portion_grams": 350.0, "calories": 165.7, "protein": 10.9, "carbs": 16.6, "fat": 6.0, "fiber": 1.7},
    {"name": "Popeyes - The Sandwich (Frango Crocante)", "category": "Fast Food", "portion_name": "1 sanduíche (220g)", "portion_grams": 220.0, "calories": 313.6, "protein": 12.7, "carbs": 22.7, "fat": 19.1, "fiber": 1.4},

    # --- MAIS FAST FOOD (KFC, Bob's, China in Box) ---
    {"name": "KFC - Original Recipe Drumstick", "category": "Fast Food", "portion_name": "1 sobrecoxa (120g)", "portion_grams": 120.0, "calories": 280.0, "protein": 22.0, "carbs": 8.0, "fat": 18.0, "fiber": 0.5},
    {"name": "KFC - Crispy Chicken Sandwich", "category": "Fast Food", "portion_name": "1 sanduíche (200g)", "portion_grams": 200.0, "calories": 450.0, "protein": 18.0, "carbs": 42.0, "fat": 22.0, "fiber": 2.0},
    {"name": "KFC - Batata Frita Média", "category": "Fast Food", "portion_name": "1 porção (110g)", "portion_grams": 110.0, "calories": 320.0, "protein": 4.0, "carbs": 38.0, "fat": 16.0, "fiber": 3.5},
    {"name": "Bob's - Big Bob Cheddar", "category": "Fast Food", "portion_name": "1 sanduíche (250g)", "portion_grams": 250.0, "calories": 520.0, "protein": 24.0, "carbs": 45.0, "fat": 26.0, "fiber": 2.5},
    {"name": "Bob's - Batata Frita Crocante", "category": "Fast Food", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 290.0, "protein": 3.0, "carbs": 35.0, "fat": 15.0, "fiber": 3.0},
    {"name": "China in Box - Yakisoba de Frango", "category": "Fast Food", "portion_name": "1 porção (350g)", "portion_grams": 350.0, "calories": 420.0, "protein": 22.0, "carbs": 55.0, "fat": 12.0, "fiber": 3.0},
    {"name": "China in Box - Rolinho Primavera (4 un)", "category": "Fast Food", "portion_name": "4 unidades (120g)", "portion_grams": 120.0, "calories": 240.0, "protein": 6.0, "carbs": 28.0, "fat": 11.0, "fiber": 2.0},

    # --- MAIS ALIMENTOS BRASILEIROS (TACO/IBGE) ---
    {"name": "Pão de Queijo (Queijo Minas)", "category": "Salgados", "portion_name": "1 unidade média (40g)", "portion_grams": 40.0, "calories": 130.0, "protein": 4.0, "carbs": 16.0, "fat": 6.0, "fiber": 0.5},
    {"name": "Feijoada Completa (1 concha)", "category": "Pratos Brasileiros", "portion_name": "1 concha (200g)", "portion_grams": 200.0, "calories": 280.0, "protein": 14.0, "carbs": 32.0, "fat": 10.0, "fiber": 8.0},
    {"name": "Feijoada - Couve Refogada", "category": "Verduras e Legumes", "portion_name": "2 colheres de sopa (40g)", "portion_grams": 40.0, "calories": 45.0, "protein": 2.0, "carbs": 5.0, "fat": 2.5, "fiber": 2.0},
    {"name": "Feijoada - Farofa", "category": "Farinhas e Massas", "portion_name": "1 colher de sopa (15g)", "portion_grams": 15.0, "calories": 65.0, "protein": 0.5, "carbs": 10.0, "fat": 3.0, "fiber": 1.0},
    {"name": "Feijoada - Arroz Branco", "category": "Cereais e Grãos", "portion_name": "1 colher de sopa (25g)", "portion_grams": 25.0, "calories": 130.0, "protein": 2.5, "carbs": 28.0, "fat": 0.2, "fiber": 1.5},
    {"name": "Moqueca de Peixe", "category": "Pratos Brasileiros", "portion_name": "1 porção (250g)", "portion_grams": 250.0, "calories": 320.0, "protein": 28.0, "carbs": 12.0, "fat": 18.0, "fiber": 3.0},
    {"name": "Acarajé (Feijão Fradinho)", "category": "Pratos Brasileiros", "portion_name": "1 unidade (150g)", "portion_grams": 150.0, "calories": 380.0, "protein": 10.0, "carbs": 35.0, "fat": 20.0, "fiber": 6.0},
    {"name": "Vatapá (Camarão e Pão)", "category": "Pratos Brasileiros", "portion_name": "1 porção (150g)", "portion_grams": 150.0, "calories": 290.0, "protein": 12.0, "carbs": 22.0, "fat": 16.0, "fiber": 4.0},
    {"name": "Pamonha (Doce ou Salgada)", "category": "Pratos Brasileiros", "portion_name": "1 unidade (200g)", "portion_grams": 200.0, "calories": 240.0, "protein": 5.0, "carbs": 45.0, "fat": 4.0, "fiber": 3.0},
    {"name": "Canjica (Mungunzá)", "category": "Pratos Brasileiros", "portion_name": "1 porção (200g)", "portion_grams": 200.0, "calories": 180.0, "protein": 4.0, "carbs": 38.0, "fat": 2.0, "fiber": 2.5},
    {"name": "Pudim de Leite Condensado", "category": "Sobremesas e Lanches", "portion_name": "1 fatia (100g)", "portion_grams": 100.0, "calories": 320.0, "protein": 6.0, "carbs": 50.0, "fat": 10.0, "fiber": 0.0},
    {"name": "Brigadeiro de Colher", "category": "Sobremesas e Lanches", "portion_name": "1 colher de sopa (25g)", "portion_grams": 25.0, "calories": 110.0, "protein": 2.0, "carbs": 18.0, "fat": 5.0, "fiber": 1.0},
    {"name": "Quindim", "category": "Sobremesas e Lanches", "portion_name": "1 unidade (50g)", "portion_grams": 50.0, "calories": 220.0, "protein": 4.0, "carbs": 28.0, "fat": 12.0, "fiber": 0.5},
    {"name": "Cocada Baiana", "category": "Sobremesas e Lanches", "portion_name": "1 unidade (40g)", "portion_grams": 40.0, "calories": 180.0, "protein": 2.0, "carbs": 25.0, "fat": 9.0, "fiber": 1.5},
    {"name": "Bolo de Cenoura com Chocolate", "category": "Sobremesas e Lanches", "portion_name": "1 fatia (80g)", "portion_grams": 80.0, "calories": 280.0, "protein": 4.0, "carbs": 42.0, "fat": 12.0, "fiber": 1.5},
    {"name": "Pão de Mel", "category": "Sobremesas e Lanches", "portion_name": "1 fatia (60g)", "portion_grams": 60.0, "calories": 220.0, "protein": 4.0, "carbs": 35.0, "fat": 8.0, "fiber": 2.0},
    {"name": "Rapadura", "category": "Açúcares e Doces", "portion_name": "1 pedaço (20g)", "portion_grams": 20.0, "calories": 75.0, "protein": 0.0, "carbs": 19.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Café com Leite (Coado)", "category": "Bebidas", "portion_name": "1 xícara (200ml)", "portion_grams": 200.0, "calories": 65.0, "protein": 3.5, "carbs": 8.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Café com Açúcar", "category": "Bebidas", "portion_name": "1 xícara (100ml)", "portion_grams": 100.0, "calories": 40.0, "protein": 0.2, "carbs": 9.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Refrigerante Cola (Lata)", "category": "Bebidas", "portion_name": "1 lata (350ml)", "portion_grams": 350.0, "calories": 139.0, "protein": 0.0, "carbs": 35.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Refrigerante Guaraná (Lata)", "category": "Bebidas", "portion_name": "1 lata (350ml)", "portion_grams": 350.0, "calories": 149.0, "protein": 0.0, "carbs": 37.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Suco de Laranja com Açúcar", "category": "Bebidas", "portion_name": "1 copo (250ml)", "portion_grams": 250.0, "calories": 112.0, "protein": 1.5, "carbs": 26.0, "fat": 0.2, "fiber": 0.5},
    {"name": "Cerveja Pilsen (Lata)", "category": "Bebidas", "portion_name": "1 lata (350ml)", "portion_grams": 350.0, "calories": 148.0, "protein": 1.5, "carbs": 12.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Vinho Tinto Seco (Taça)", "category": "Bebidas", "portion_name": "1 taça (150ml)", "portion_grams": 150.0, "calories": 125.0, "protein": 0.1, "carbs": 4.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Caipirinha (Cachaça)", "category": "Bebidas", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 220.0, "protein": 0.0, "carbs": 25.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Energético (Lata)", "category": "Bebidas", "portion_name": "1 lata (250ml)", "portion_grams": 250.0, "calories": 112.0, "protein": 0.0, "carbs": 28.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Chocolate Quente", "category": "Bebidas", "portion_name": "1 xícara (200ml)", "portion_grams": 200.0, "calories": 180.0, "protein": 6.0, "carbs": 28.0, "fat": 6.0, "fiber": 1.0},
    {"name": "Vitamina de Banana com Leite", "category": "Bebidas", "portion_name": "1 copo (300ml)", "portion_grams": 300.0, "calories": 210.0, "protein": 8.0, "carbs": 38.0, "fat": 4.0, "fiber": 2.0},
    {"name": "Shake de Morango", "category": "Bebidas", "portion_name": "1 copo (300ml)", "portion_grams": 300.0, "calories": 280.0, "protein": 6.0, "carbs": 50.0, "fat": 6.0, "fiber": 1.5},
    {"name": "Água Tônica", "category": "Bebidas", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 80.0, "protein": 0.0, "carbs": 20.0, "fat": 0.0, "fiber": 0.0},
    {"name": "Chá Verde sem Açúcar", "category": "Bebidas", "portion_name": "1 xícara (200ml)", "portion_grams": 200.0, "calories": 2.0, "protein": 0.0, "carbs": 0.5, "fat": 0.0, "fiber": 0.0},
    {"name": "Chá de Camomila", "category": "Bebidas", "portion_name": "1 xícara (200ml)", "portion_grams": 200.0, "calories": 2.0, "protein": 0.0, "carbs": 0.5, "fat": 0.0, "fiber": 0.0},
    {"name": "Leite com Chocolate (Achocolatado)", "category": "Bebidas", "portion_name": "1 copo (200ml)", "portion_grams": 200.0, "calories": 140.0, "protein": 5.0, "carbs": 22.0, "fat": 4.0, "fiber": 0.5},
    {"name": "Iogurte de Morango", "category": "Laticínios", "portion_name": "1 pote (170g)", "portion_grams": 170.0, "calories": 100.0, "protein": 4.0, "carbs": 16.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Queijo Prato", "category": "Laticínios", "portion_name": "1 fatia (20g)", "portion_grams": 20.0, "calories": 70.0, "protein": 5.0, "carbs": 0.5, "fat": 5.5, "fiber": 0.0},
    {"name": "Presunto", "category": "Carnes e Aves", "portion_name": "1 fatia (20g)", "portion_grams": 20.0, "calories": 30.0, "protein": 5.0, "carbs": 0.5, "fat": 1.5, "fiber": 0.0},
    {"name": "Mortadela", "category": "Carnes e Aves", "portion_name": "1 fatia (20g)", "portion_grams": 20.0, "calories": 55.0, "protein": 3.0, "carbs": 1.0, "fat": 4.5, "fiber": 0.0},
    {"name": "Salsicha", "category": "Carnes e Aves", "portion_name": "1 unidade (30g)", "portion_grams": 30.0, "calories": 90.0, "protein": 3.5, "carbs": 1.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Linguiça Toscana", "category": "Carnes e Aves", "portion_name": "1 unidade (60g)", "portion_grams": 60.0, "calories": 180.0, "protein": 10.0, "carbs": 2.0, "fat": 15.0, "fiber": 0.0},
    {"name": "Bacon", "category": "Carnes e Aves", "portion_name": "2 fatias (20g)", "portion_grams": 20.0, "calories": 90.0, "protein": 4.0, "carbs": 0.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Carne Seca (Charque)", "category": "Carnes e Aves", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 220.0, "protein": 28.0, "carbs": 0.0, "fat": 10.0, "fiber": 0.0},
    {"name": "Costela de Porco", "category": "Carnes e Aves", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 280.0, "protein": 22.0, "carbs": 0.0, "fat": 20.0, "fiber": 0.0},
    {"name": "Linguiça de Frango", "category": "Carnes e Aves", "portion_name": "1 unidade (60g)", "portion_grams": 60.0, "calories": 120.0, "protein": 8.0, "carbs": 1.0, "fat": 9.0, "fiber": 0.0},
    {"name": "Peito de Peru", "category": "Carnes e Aves", "portion_name": "1 fatia (20g)", "portion_grams": 20.0, "calories": 25.0, "protein": 5.0, "carbs": 0.5, "fat": 0.5, "fiber": 0.0},
    {"name": "Salame", "category": "Carnes e Aves", "portion_name": "2 fatias (20g)", "portion_grams": 20.0, "calories": 70.0, "protein": 4.0, "carbs": 0.5, "fat": 6.0, "fiber": 0.0},
    {"name": "Atum em Óleo", "category": "Pescados", "portion_name": "1 lata (120g)", "portion_grams": 120.0, "calories": 200.0, "protein": 24.0, "carbs": 0.0, "fat": 11.0, "fiber": 0.0},
    {"name": "Sardinha em Óleo", "category": "Pescados", "portion_name": "1 lata (80g)", "portion_grams": 80.0, "calories": 180.0, "protein": 18.0, "carbs": 0.0, "fat": 11.0, "fiber": 0.0},
    {"name": "Bacalhau", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 150.0, "protein": 28.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Camarão", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 90.0, "protein": 20.0, "carbs": 0.0, "fat": 1.5, "fiber": 0.0},
    {"name": "Polvo", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 80.0, "protein": 15.0, "carbs": 2.0, "fat": 1.0, "fiber": 0.0},
    {"name": "Lula", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 90.0, "protein": 16.0, "carbs": 3.0, "fat": 1.5, "fiber": 0.0},
    {"name": "Ostras", "category": "Pescados", "portion_name": "6 unidades (100g)", "portion_grams": 100.0, "calories": 70.0, "protein": 8.0, "carbs": 4.0, "fat": 2.0, "fiber": 0.0},
    {"name": "Mexilhão", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 85.0, "protein": 12.0, "carbs": 4.0, "fat": 2.0, "fiber": 0.0},
    {"name": "Lagosta", "category": "Pescados", "portion_name": "1 porção (150g)", "portion_grams": 150.0, "calories": 130.0, "protein": 26.0, "carbs": 0.0, "fat": 2.0, "fiber": 0.0},
    {"name": "Caranguejo", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 90.0, "protein": 18.0, "carbs": 0.0, "fat": 1.5, "fiber": 0.0},
    {"name": "Siri", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 85.0, "protein": 16.0, "carbs": 0.0, "fat": 1.5, "fiber": 0.0},
    {"name": "Tainha", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 140.0, "protein": 20.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Robalo", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 110.0, "protein": 22.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Dourado do Mar", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 130.0, "protein": 24.0, "carbs": 0.0, "fat": 3.5, "fiber": 0.0},
    {"name": "Garoupa", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 120.0, "protein": 23.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Namorado", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 115.0, "protein": 22.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Pescada Branca", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 105.0, "protein": 21.0, "carbs": 0.0, "fat": 2.0, "fiber": 0.0},
    {"name": "Anchova", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 125.0, "protein": 23.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Cavalinha", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 140.0, "protein": 22.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Sardinha Fresca", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 160.0, "protein": 20.0, "carbs": 0.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Truta", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 135.0, "protein": 22.0, "carbs": 0.0, "fat": 4.5, "fiber": 0.0},
    {"name": "Linguado", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 100.0, "protein": 20.0, "carbs": 0.0, "fat": 2.0, "fiber": 0.0},
    {"name": "Badejo", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 115.0, "protein": 22.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Mero", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 125.0, "protein": 24.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Pargo", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 130.0, "protein": 23.0, "carbs": 0.0, "fat": 3.5, "fiber": 0.0},
    {"name": "Bacalhau Fresco", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 140.0, "protein": 26.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Cação", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 120.0, "protein": 22.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Tubarão", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 130.0, "protein": 24.0, "carbs": 0.0, "fat": 3.5, "fiber": 0.0},
    {"name": "Ararati", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 110.0, "protein": 20.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Pirarucu", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 125.0, "protein": 23.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Tambaqui", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 140.0, "protein": 22.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Pintado", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 135.0, "protein": 24.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Surubim", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 130.0, "protein": 23.0, "carbs": 0.0, "fat": 3.5, "fiber": 0.0},
    {"name": "Dourado", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 125.0, "protein": 22.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Piau", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 115.0, "protein": 20.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Lambari", "category": "Pescados", "portion_name": "1 porção (100g)", "portion_grams": 100.0, "calories": 100.0, "protein": 18.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0},
    {"name": "Tilápia Defumada", "category": "Pescados", "portion_name": "1 filé (100g)", "portion_grams": 100.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Salmão Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 160.0, "protein": 20.0, "carbs": 0.0, "fat": 9.0, "fiber": 0.0},
    {"name": "Atum Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 120.0, "protein": 22.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Bacalhau Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Sardinha Defumada", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 150.0, "protein": 20.0, "carbs": 0.0, "fat": 7.0, "fiber": 0.0},
    {"name": "Cavalinha Defumada", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 160.0, "protein": 22.0, "carbs": 0.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Anchova Defumada", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 22.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Truta Defumada", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 150.0, "protein": 24.0, "carbs": 0.0, "fat": 6.0, "fiber": 0.0},
    {"name": "Linguado Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 130.0, "protein": 22.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Badejo Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Mero Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 150.0, "protein": 26.0, "carbs": 0.0, "fat": 6.0, "fiber": 0.0},
    {"name": "Pargo Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 160.0, "protein": 24.0, "carbs": 0.0, "fat": 7.0, "fiber": 0.0},
    {"name": "Bacalhau Fresco Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 170.0, "protein": 28.0, "carbs": 0.0, "fat": 8.0, "fiber": 0.0},
    {"name": "Cação Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Tubarão Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 150.0, "protein": 26.0, "carbs": 0.0, "fat": 6.0, "fiber": 0.0},
    {"name": "Jarati Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 130.0, "protein": 22.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Pirarucu Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Tambaqui Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 160.0, "protein": 24.0, "carbs": 0.0, "fat": 7.0, "fiber": 0.0},
    {"name": "Pintado Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 150.0, "protein": 26.0, "carbs": 0.0, "fat": 6.0, "fiber": 0.0},
    {"name": "Surubim Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 140.0, "protein": 24.0, "carbs": 0.0, "fat": 5.0, "fiber": 0.0},
    {"name": "Dourado Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 130.0, "protein": 22.0, "carbs": 0.0, "fat": 4.0, "fiber": 0.0},
    {"name": "Piau Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 120.0, "protein": 20.0, "carbs": 0.0, "fat": 3.0, "fiber": 0.0},
    {"name": "Lambari Defumado", "category": "Pescados", "portion_name": "1 porção (80g)", "portion_grams": 80.0, "calories": 110.0, "protein": 18.0, "carbs": 0.0, "fat": 2.5, "fiber": 0.0}
]

def seed_foods():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    inserted_count = 0
    for food in POPULAR_BRAZILIAN_FOODS:
        cursor.execute("SELECT id FROM foods WHERE name = ?", (food["name"],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO foods (name, category, portion_name, portion_grams, calories, protein, carbs, fat, fiber, is_custom)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                food["name"], food["category"], food["portion_name"], food["portion_grams"],
                food["calories"], food["protein"], food["carbs"], food["fat"], food["fiber"]
            ))
            inserted_count += 1

    conn.commit()
    cursor.execute("SELECT COUNT(*) as count FROM foods WHERE is_custom = 0")
    total = cursor.fetchone()["count"]
    print(f"Base de alimentos verificada: {inserted_count} novos inseridos. Total oficial: {total} alimentos com médias TACO/IBGE/USDA e Fast Food!")
    conn.close()

if __name__ == "__main__":
    seed_foods()
