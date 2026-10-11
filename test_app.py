import io
import sys
import secrets
from pathlib import Path

# Adicionar backend ao path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_server_info_and_version():
    res = client.get("/api/server-info")
    assert res.status_code == 200
    info = res.json()
    assert "version" in info
    assert "local_ip" in info
    assert "mobile_url" in info
    print(f"[OK] Teste de Server Info e Live-Update passou (IP: {info['local_ip']}, Versao: {info['version']})!")

def test_auth():
    unique_email = f"user_{secrets.token_hex(4)}@teste.com"
    reg_res = client.post("/api/auth/register", json={
        "name": "Maria Silva",
        "email": unique_email,
        "password": "senhaSegura123"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert "token" in reg_data
    user_id = reg_data["user"]["id"]

    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "senhaSegura123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True
    assert login_data["user"]["id"] == user_id
    # Teste de redefinição de senha
    reset_res = client.post("/api/auth/reset-password", json={
        "email": unique_email,
        "new_password": "novaSenha123"
    })
    assert reset_res.status_code == 200
    assert reset_res.json()["success"] is True

    # Teste de login com a nova senha
    relogin_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "novaSenha123"
    })
    assert relogin_res.status_code == 200
    assert relogin_res.json()["user"]["id"] == user_id

    # Teste de isolamento de aparelhos: recent-account NÃO vaza usuários para novos aparelhos
    recent_res = client.get("/api/auth/recent-account")
    assert recent_res.status_code == 200
    assert recent_res.json()["success"] is False
    assert recent_res.json()["user"] is None

    # Teste de segurança: quick-login desautorizado é bloqueado
    quick_res = client.post("/api/auth/quick-login", json={"user_id": 18})
    assert quick_res.status_code == 200
    assert quick_res.json()["success"] is False

    print("[OK] Teste de Cadastro, Login, Redefinição e Isolamento Seguro de Aparelhos passou!")
    return user_id

def test_profile(user_id=1):
    res = client.get(f"/api/profile?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "target_calories" in data
    assert "calculated" in data
    assert data["calculated"]["bmr"] > 1000
    print("[OK] Teste de Perfil e calculo de TMB/GET passou com sucesso!")

def test_foods():
    res = client.get("/api/foods?q=Arroz")
    assert res.status_code == 200
    foods = res.json()
    assert len(foods) > 0
    assert any("Arroz" in f["name"] for f in foods)
    print(f"[OK] Teste de busca de alimentos TACO passou ({len(foods)} resultados encontrados)!")

def test_diary_flow(user_id=1):
    entry_payload = {
        "user_id": user_id,
        "date": "2026-09-22",
        "meal_type": "lunch",
        "food_name": "Arroz Branco Cozido",
        "amount_grams": 150.0,
        "calories": 195.0,
        "protein": 3.75,
        "carbs": 42.3,
        "fat": 0.3,
        "fiber": 2.4,
        "notes": "Almoço de teste"
    }
    add_res = client.post("/api/diary", json=entry_payload)
    assert add_res.status_code == 200
    entry_id = add_res.json()["id"]

    get_res = client.get(f"/api/diary?date=2026-09-22&user_id={user_id}")
    assert get_res.status_code == 200
    diary_data = get_res.json()
    assert diary_data["summary"]["consumed_calories"] >= 195
    assert len(diary_data["meals"]["lunch"]["items"]) >= 1

    del_res = client.delete(f"/api/diary/{entry_id}")
    assert del_res.status_code == 200
    print("[OK] Teste de fluxo completo do Diario Alimentar passou com sucesso!")

def test_water(user_id=1):
    res = client.post("/api/water", json={"user_id": user_id, "date": "2026-09-22", "amount_ml": 500})
    assert res.status_code == 200
    assert res.json()["total_water"] >= 500
    print("[OK] Teste de registro de hidratacao passou com sucesso!")

def test_cheat_day(user_id=1):
    res = client.get(f"/api/cheat-day?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "banked_calories_pool" in data
    assert "cheat_day_calorie_allowance" in data
    assert "damage_control_checklist" in data

    toggle_res = client.post("/api/cheat-day/toggle", json={"user_id": user_id, "active": True})
    assert toggle_res.status_code == 200
    assert toggle_res.json()["cheat_mode_active"] is True

    client.post("/api/cheat-day/toggle", json={"user_id": user_id, "active": False})
    print("[OK] Teste do Sistema do Dia do Lixo e Banco Calorico passou com sucesso!")

def test_restaurants():
    res = client.get("/api/restaurants?lat=-23.5505&lng=-46.6333")
    assert res.status_code == 200
    restaurants = res.json()
    assert len(restaurants) >= 5
    first = restaurants[0]
    assert "diet_dishes" in first
    assert "cheat_dishes" in first
    assert first["distance_km"] is not None
    print(f"[OK] Teste de Restaurantes e Recomendacoes passou ({len(restaurants)} locais com opcoes Dieta vs Dia do Lixo)!")

def test_photo_scan():
    import time
    # Teste do status da IA integrada e links
    info_res = client.get("/api/ai/info?user_id=1")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert info_data["ia_integrada_ativa"] is True
    assert "link_groq" in info_data
    assert "link_gemini" in info_data
    assert "console.groq.com" in info_data["link_groq"]
    assert "aistudio.google.com" in info_data["link_gemini"]
    print(f"[OK] Teste de Status da IA Integrada e Links passou ({info_data['ia_provedor']})!")

    mock_file = io.BytesIO(b"FAKE_IMAGE_BYTES_FOR_TESTING")
    t0 = time.perf_counter()
    res = client.post(
        "/api/ai/scan-food",
        files={"file": ("test.jpg", mock_file, "image/jpeg")}
    )
    elapsed = time.perf_counter() - t0
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "total_calories" in data
    assert len(data["items"]) > 0
    assert elapsed < 3.0, f"Tempo de resposta da IA foi de {elapsed:.2f}s, esperado < 3.0s!"
    print(f"[OK] Teste do Scanner de Refeicoes por Foto passou ({data['detected_dish']}: {data['total_calories']} kcal em {elapsed:.3f}s)!")

    # Teste do Chat Nutricionista com IA
    t0_chat = time.perf_counter()
    chat_res = client.post("/api/ai/chat", json={
        "user_id": 1,
        "message": "Qual melhor lanche da tarde proteico?"
    })
    chat_elapsed = time.perf_counter() - t0_chat
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert chat_data["success"] is True
    assert len(chat_data["reply"]) > 10
    assert chat_elapsed < 4.0
    print(f"[OK] Teste do Chat Nutri com IA passou em {chat_elapsed:.3f}s!")

    # Teste do Analisador de Cardapio com IA
    t0_menu = time.perf_counter()
    menu_res = client.post("/api/restaurants/ai-analyze", json={
        "restaurant_name": "Outback Steakhouse",
        "menu_text": "Picanha, batata frita, salada caesar, costela ao molho barbecue"
    })
    menu_elapsed = time.perf_counter() - t0_menu
    assert menu_res.status_code == 200
    menu_data = menu_res.json()
    assert menu_data["success"] is True
    assert len(menu_data["diet_recommendations"]) > 0
    assert len(menu_data["cheat_recommendations"]) > 0
    assert menu_elapsed < 4.0
    print(f"[OK] Teste do Analisador de Cardapio com IA passou em {menu_elapsed:.3f}s!")

def test_gamification_streak(user_id=1):
    res = client.get(f"/api/gamification/streak?user_id={user_id}")
    assert res.status_code == 200
    data = res.json()
    assert "current_streak" in data
    assert "flame_level" in data
    assert "history_7_days" in data
    assert len(data["history_7_days"]) == 7
    print(f"[OK] Teste do Foguinho/Ofensiva estilo Duolingo/TikTok passou (Nível: {data['flame_title']})!")

def test_daily_missions(user_id=1):
    res = client.get(f"/api/gamification/missions?user_id={user_id}")
    assert res.status_code == 200
    missions = res.json()
    assert len(missions) >= 3
    first = missions[0]
    complete_res = client.post(f"/api/gamification/missions/{first['id']}/complete", json={"user_id": user_id})
    assert complete_res.status_code == 200
    assert complete_res.json()["success"] is True
    print(f"[OK] Teste de Missoes Diarias Ludicas passou ({len(missions)} missoes carregadas e validadas)!")

def test_real_family_system():
    # 1. Usuário cria conta
    user_a_email = f"fam_a_{secrets.token_hex(4)}@teste.com"
    reg_a = client.post("/api/auth/register", json={"name": "Pai Carlos", "email": user_a_email, "password": "senhaSegura123"})
    assert reg_a.status_code == 200
    user_a_id = reg_a.json()["user"]["id"]

    # Sem família inicialmente
    battle_init = client.get(f"/api/gamification/family-battle?user_id={user_a_id}").json()
    assert battle_init["in_family"] is False

    # Criar família
    create_res = client.post("/api/family/create", json={"user_id": user_a_id, "family_name": "Família Silva"})
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["success"] is True
    invite_code = create_data["family"]["invite_code"]
    assert "-" in invite_code and len(invite_code) >= 7

    # Segundo usuário entra pelo código
    user_b_email = f"fam_b_{secrets.token_hex(4)}@teste.com"
    reg_b = client.post("/api/auth/register", json={"name": "Mãe Ana", "email": user_b_email, "password": "senhaSegura123"})
    assert reg_b.status_code == 200
    user_b_id = reg_b.json()["user"]["id"]

    join_res = client.post("/api/family/join", json={"user_id": user_b_id, "invite_code": invite_code})
    assert join_res.status_code == 200
    assert join_res.json()["success"] is True

    # Adicionar terceiro membro diretamente
    add_res = client.post("/api/family/add-member", json={
        "admin_user_id": user_a_id,
        "member_name": "Filho Pedro",
        "member_email": f"pedro_{secrets.token_hex(4)}@teste.com",
        "password": "senhaSegura123"
    })
    assert add_res.status_code == 200
    assert add_res.json()["success"] is True

    # Verificar que o ranking agora lista exatamente os 3 membros reais da família
    battle_updated = client.get(f"/api/gamification/family-battle?user_id={user_a_id}").json()
    assert battle_updated["in_family"] is True
    assert len(battle_updated["ranking"]) == 3
    names = [m["name"] for m in battle_updated["ranking"]]
    assert "Pai Carlos" in names
    assert "Mãe Ana" in names
    assert "Filho Pedro" in names
    # Garantir que NÃO existem membros fictícios
    assert not any("Beatriz" in n for n in names)

    # Escolha do Dia do Lixo pelo Líder
    choice_res = client.post("/api/gamification/family-battle/cheat-choice", json={
        "user_id": user_a_id,
        "chosen_dish": "Pizza Napolitana Quatro Queijos",
        "restaurant_name": "Don Vincenzo",
        "message": "Comemorando nossa vitória na semana!"
    })
    assert choice_res.status_code == 200
    assert choice_res.json()["success"] is True

    updated_battle = client.get(f"/api/gamification/family-battle?user_id={user_a_id}").json()
    assert updated_battle["cheat_choice"] is not None
    assert updated_battle["cheat_choice"]["chosen_dish"] == "Pizza Napolitana Quatro Queijos"

    print(f"[OK] Teste do Sistema de Família Real (criação, código {invite_code}, membros reais e escolha do Dia do Lixo) passou!")
    return user_a_id

def test_weekly_menu_assistant(user_id=1):
    # Gerar cardápio individual
    res = client.get(f"/api/menu/weekly?user_id={user_id}&mode=individual")
    assert res.status_code == 200
    menu = res.json()
    assert "days" in menu
    assert len(menu["days"]) == 7
    assert "segunda" in menu["days"]
    assert "domingo" in menu["days"]
    segunda = menu["days"]["segunda"]
    assert "meals" in segunda
    assert "breakfast" in segunda["meals"]
    assert "lunch" in segunda["meals"]
    assert "snack" in segunda["meals"]
    assert "dinner" in segunda["meals"]
    dish_orig = segunda["meals"]["lunch"]["name"]

    # Trocar prato (swap)
    swap_res = client.post("/api/menu/weekly/swap-dish", json={
        "user_id": user_id,
        "mode": "individual",
        "day_key": "segunda",
        "meal_type": "lunch"
    })
    assert swap_res.status_code == 200
    swap_data = swap_res.json()
    assert swap_data["success"] is True
    new_dish = swap_data["dish"]["name"]
    assert new_dish != dish_orig

    # Lançar no diário alimentar
    log_res = client.post("/api/menu/weekly/log-to-diary", json={
        "user_id": user_id,
        "date": "2026-09-23",
        "meal_type": "lunch",
        "dish_name": new_dish
    })
    assert log_res.status_code == 200
    assert log_res.json()["success"] is True

    # Verificar que entrou no diário de hoje
    diary_res = client.get(f"/api/diary?date=2026-09-23&user_id={user_id}")
    assert diary_res.status_code == 200
    diary_items = diary_res.json()["meals"]["lunch"]["items"]
    assert any(new_dish in item["food_name"] for item in diary_items)

    # Testar cardápio em modo família
    fam_res = client.get(f"/api/menu/weekly?user_id={user_id}&mode=family")
    assert fam_res.status_code == 200
    assert fam_res.json()["mode"] == "family"
    print(f"[OK] Teste do Assistente de Cardápio Semanal (Individual/Família, Troca de Prato e Lançamento no Diário) passou!")

def test_ios_integration():
    html_res = client.get("/")
    assert html_res.status_code == 200
    html = html_res.text
    assert 'name="apple-mobile-web-app-capable" content="yes"' in html
    assert 'name="apple-mobile-web-app-status-bar-style" content="black-translucent"' in html
    assert 'rel="apple-touch-icon"' in html
    assert 'viewport-fit=cover' in html
    assert 'mobile-tab-content-ios' in html
    assert 'Adicionar à Tela de Início' in html
    assert 'meal_assistant.js' in html
    print("[OK] Teste de Integração iOS (Meta tags Apple PWA, Safe-area insets, Guia Safari) passou!")

def test_apk_download():
    info_res = client.get("/api/download/apk-info")
    assert info_res.status_code == 200
    info = info_res.json()
    assert info["exists"] is True
    assert info["filename"] == "VivaLeve.apk"
    assert info["size_mb"] > 0

    download_res = client.get("/download/apk")
    assert download_res.status_code == 200
    assert download_res.headers.get("content-type") == "application/vnd.android.package-archive"
    assert len(download_res.content) > 1000000
    print(f"[OK] Teste de Download do Arquivo APK passou ({info['filename']}: {info['size_mb']} MB)! ")

if __name__ == "__main__":
    print("\nExecutando bateria de testes do VivaLeve v3.2...\n")
    test_server_info_and_version()
    user_id = test_auth()
    test_profile(user_id)
    test_foods()
    test_diary_flow(user_id)
    test_water(user_id)
    test_cheat_day(user_id)
    test_restaurants()
    test_photo_scan()
    test_gamification_streak(user_id)
    test_daily_missions(user_id)
    fam_user_id = test_real_family_system()
    test_weekly_menu_assistant(user_id)
    test_ios_integration()
    test_apk_download()
    
    # Teste do Wizard de Onboarding & Cálculo de Déficit Calórico
    calc_res = client.post("/api/profile/calculate-preview", json={
        "weight": 82.0,
        "height": 178.0,
        "age": 30,
        "gender": "M",
        "activity_level": "moderado",
        "goal": "emagrecer",
        "pace": "moderado"
    })
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["bmi"] == 25.9
    assert calc_data["bmi_status"] == "Sobrepeso leve"
    assert calc_data["cal_diff"] == -500
    assert calc_data["target_calories"] < calc_data["tdee"]
    assert calc_data["target_water"] > 2500

    # Teste de registro com respostas completas do questionário
    quiz_email = f"quiz_{secrets.token_hex(4)}@teste.com"
    quiz_res = client.post("/api/auth/register", json={
        "name": "Carlos Atleta",
        "email": quiz_email,
        "password": "senhaSegura123",
        "gender": "M",
        "age": 30,
        "weight": 82.0,
        "height": 178.0,
        "activity_level": "moderado",
        "goal": "emagrecer",
        "pace": "moderado"
    })
    assert quiz_res.status_code == 200
    q_user_id = quiz_res.json()["user"]["id"]
    prof_res = client.get(f"/api/profile?user_id={q_user_id}")
    assert prof_res.status_code == 200
    prof_data = prof_res.json()
    assert prof_data["weight"] == 82.0
    assert prof_data["goal"] == "emagrecer"
    assert prof_data["target_calories"] == calc_data["target_calories"]
    print(f"[OK] Teste do Questionário de Onboarding & Déficit Calórico passou (IMC: {calc_data['bmi']}, Meta: {prof_data['target_calories']} kcal/dia)!")

    # Teste de entrega dos arquivos estáticos e elementos no index.html
    html_res = client.get("/")
    assert html_res.status_code == 200
    assert "modal-onboarding-wizard" in html_res.text
    assert "calorie-gauge-circle" in html_res.text
    assert "modal-create-family" in html_res.text
    assert "tab-cardapio" in html_res.text
    assert "onboarding.js" in html_res.text
    assert "meal_assistant.js" in html_res.text
    assert "modal-reset-password" in html_res.text
    assert "auth-saved-accounts-container" in html_res.text

    print("\n========================================================")
    print("  TODOS OS 17 TESTES DO VIVALEVE V3.4 PASSARAM COM SUCESSO!  ")
    print("========================================================\n")

