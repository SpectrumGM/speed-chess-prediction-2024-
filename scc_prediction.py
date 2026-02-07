# ============================================================
# ЯЧЕЙКА 1: Импорты и настройка
# ============================================================
# Запусти эту ячейку первой — она подключает все библиотеки

import requests          # для запросов к Chess.com API
import pandas as pd      # для работы с таблицами
import numpy as np       # для математики (массивы, статистика)
import time              # для пауз между запросами к API
import os                # для работы с файлами и папками
import json              # для работы с JSON данными
from collections import defaultdict  # удобный словарь с значением по умолчанию

# Создаём папку для данных если её нет
os.makedirs("../data", exist_ok=True)

print("✅ Все библиотеки загружены!")


# ============================================================
# ЯЧЕЙКА 2: Список игроков и турнирная сетка
# ============================================================

# Словарь: имя игрока → ник на Chess.com
players = {
    "Magnus Carlsen": "MagnusCarlsen",
    "Tuan Minh Le": "wonderfultime",
    "Jan-Krzysztof Duda": "Polish_fighter3000",
    "Arjun Erigaisi": "GHANDEEVAM2003",
    "Wesley So": "GMWSO",
    "Denis Lazavik": "DenLaz",
    "Maxime Vachier-Lagrave": "LyonBeast",
    "Hans Niemann": "HansOnTwitch",
    "Hikaru Nakamura": "Hikaru",
    "Jose Martinez": "Jospem",
    "Ian Nepomniachtchi": "lachesisQ",
    "Nodirbek Abdusattorov": "ChessWarrior7197",
    "Alireza Firouzja": "Firouzja2003",
    "Alexander Grischuk": "Grischuk",
    "Fabiano Caruana": "FabianoCaruana",
    "Alexey Sarana": "mishanick",
}

# Обратный словарь: ник (в нижнем регистре) → имя
# Нужен чтобы по нику из API найти настоящее имя
username_to_name = {v.lower(): k for k, v in players.items()}

# Турнирная сетка Round 1 (1/8 финала)
# Каждый tuple — пара (Игрок A, Игрок B)
bracket_r1 = [
    ("Magnus Carlsen", "Tuan Minh Le"),           # Матч A
    ("Jan-Krzysztof Duda", "Arjun Erigaisi"),     # Матч B
    ("Wesley So", "Denis Lazavik"),                 # Матч C
    ("Maxime Vachier-Lagrave", "Hans Niemann"),    # Матч D
    ("Hikaru Nakamura", "Jose Martinez"),           # Матч E
    ("Ian Nepomniachtchi", "Nodirbek Abdusattorov"), # Матч F
    ("Alireza Firouzja", "Alexander Grischuk"),    # Матч G
    ("Fabiano Caruana", "Alexey Sarana"),           # Матч H
]

# Четвертьфинальные пары (победители матчей):
# I: Winner A vs Winner B
# J: Winner C vs Winner D
# K: Winner E vs Winner F
# L: Winner G vs Winner H

# Полуфиналы:
# Winner I vs Winner J
# Winner K vs Winner L

print(f"✅ {len(players)} игроков загружено")
print(f"✅ {len(bracket_r1)} матчей в Round 1")
for i, (a, b) in enumerate(bracket_r1):
    print(f"   Матч {chr(65+i)}: {a} vs {b}")


# ============================================================
# ЯЧЕЙКА 3: Сбор рейтингов
# ============================================================
# Этот код ты уже запускал. Он берёт текущие рейтинги с Chess.com.
# Но нам нужны рейтинги НА МОМЕНТ ТУРНИРА (до 25 июля 2024).
# К сожалению, Chess.com API даёт только текущие рейтинги.
# Поэтому мы используем текущие как приближение + добавим h2h данные.

ratings_data = []
for name, username in players.items():
    url = f"https://api.chess.com/pub/player/{username}/stats"
    headers = {"User-Agent": "SpeedChessPredictor/1.0"}
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        stats = resp.json()
        row = {
            "name": name,
            "username": username,
            "bullet_rating": stats.get("chess_bullet", {}).get("last", {}).get("rating"),
            "bullet_best": stats.get("chess_bullet", {}).get("best", {}).get("rating"),
            "blitz_rating": stats.get("chess_blitz", {}).get("last", {}).get("rating"),
            "blitz_best": stats.get("chess_blitz", {}).get("best", {}).get("rating"),
            "rapid_rating": stats.get("chess_rapid", {}).get("last", {}).get("rating"),
        }
        ratings_data.append(row)
        print(f"✓ {name}")
    else:
        print(f"✗ {name} — error {resp.status_code}")
    time.sleep(0.5)

# Добавляем Firouzja вручную (API возвращает 404)
ratings_data.append({
    "name": "Alireza Firouzja",
    "username": "Firouzja2003",
    "bullet_rating": 3309,
    "bullet_best": 3360,
    "blitz_rating": 3250,
    "blitz_best": 3315,
    "rapid_rating": None,
})

df_ratings = pd.DataFrame(ratings_data)
df_ratings.to_csv("../data/players_ratings.csv", index=False)

print(f"\n✅ Рейтинги собраны для {len(df_ratings)} игроков:\n")
print(df_ratings[["name", "blitz_rating", "bullet_rating"]].to_string(index=False))


# ============================================================
# ЯЧЕЙКА 4: Сбор истории партий (head-to-head)
# ============================================================
# 
# ЭТО САМАЯ ВАЖНАЯ ЧАСТЬ!
# 
# Мы скачиваем ВСЕ партии каждого игрока с Chess.com за 2023-2024 годы
# (до июля 2024), и ищем партии где ОППОНЕНТ тоже из наших 16 игроков.
#
# Chess.com API работает так:
# 1. GET /pub/player/{username}/games/archives → список месяцев с партиями
# 2. GET /pub/player/{username}/games/2024/07 → все партии за июль 2024
#
# Это займёт несколько минут — много запросов к API.

# Множество (set) всех ников в нижнем регистре — для быстрого поиска
our_players_lower = set(v.lower() for v in players.values())

# Сюда будем складывать все h2h партии
all_games = []

# Множество уже обработанных пар (чтобы не считать одну партию дважды)
processed_game_ids = set()

print("Начинаю сбор партий... Это займёт 5-10 минут.\n")

for name, username in players.items():
    print(f"📥 Скачиваю партии {name} ({username})...")
    
    # Шаг 1: Получаем список архивов (месяцев)
    archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
    headers = {"User-Agent": "SpeedChessPredictor/1.0"}
    resp = requests.get(archives_url, headers=headers)
    
    if resp.status_code != 200:
        print(f"  ⚠️ Не удалось получить архивы для {name}")
        continue
    
    archives = resp.json().get("archives", [])
    
    # Фильтруем: берём только 2023 и 2024 до июля
    # URL архива выглядит так: https://api.chess.com/pub/player/hikaru/games/2024/07
    relevant_archives = []
    for archive_url in archives:
        # Извлекаем год и месяц из URL
        parts = archive_url.split("/")
        year = int(parts[-2])
        month = int(parts[-1])
        
        # Берём 2023-2024, но не позже июля 2024
        if year == 2023:
            relevant_archives.append(archive_url)
        elif year == 2024 and month <= 7:
            relevant_archives.append(archive_url)
    
    games_found = 0
    
    # Шаг 2: Скачиваем партии за каждый месяц
    for archive_url in relevant_archives:
        resp = requests.get(archive_url, headers=headers)
        if resp.status_code != 200:
            continue
        
        games = resp.json().get("games", [])
        
        for game in games:
            # Проверяем: это блиц или буллет?
            time_class = game.get("time_class", "")
            if time_class not in ["blitz", "bullet"]:
                continue  # пропускаем рапид, дэйли и др.
            
            # Кто играл?
            white_user = game.get("white", {}).get("username", "").lower()
            black_user = game.get("black", {}).get("username", "").lower()
            
            # Оба игрока должны быть из наших 16
            if white_user not in our_players_lower or black_user not in our_players_lower:
                continue
            
            # Уникальный ID партии (чтобы не дублировать)
            game_url = game.get("url", "")
            if game_url in processed_game_ids:
                continue
            processed_game_ids.add(game_url)
            
            # Извлекаем результаты
            white_result = game.get("white", {}).get("result", "")
            black_result = game.get("black", {}).get("result", "")
            white_rating = game.get("white", {}).get("rating", 0)
            black_rating = game.get("black", {}).get("rating", 0)
            
            # Определяем кто победил
            # "win" = победа, "checkmated"/"timeout"/"resigned" и т.д. = поражение
            if white_result == "win":
                result = 1  # белые победили
            elif black_result == "win":
                result = 0  # чёрные победили
            else:
                result = 0.5  # ничья
            
            # Получаем настоящие имена
            white_name = username_to_name.get(white_user, white_user)
            black_name = username_to_name.get(black_user, black_user)
            
            all_games.append({
                "white": white_name,
                "black": black_name,
                "white_rating": white_rating,
                "black_rating": black_rating,
                "result": result,  # 1 = белые выиграли, 0 = чёрные, 0.5 = ничья
                "time_class": time_class,
                "time_control": game.get("time_control", ""),
                "date": game.get("end_time", 0),
            })
            games_found += 1
        
        time.sleep(0.3)  # пауза между запросами
    
    print(f"  → Найдено {games_found} партий против наших игроков")
    time.sleep(0.5)

df_games = pd.DataFrame(all_games)
df_games.to_csv("../data/h2h_games.csv", index=False)

print(f"\n✅ Всего собрано {len(df_games)} партий между нашими 16 игроками")
print(f"   Блиц: {len(df_games[df_games['time_class']=='blitz'])}")
print(f"   Буллет: {len(df_games[df_games['time_class']=='bullet'])}")


# ============================================================
# ЯЧЕЙКА 5: Анализ собранных данных
# ============================================================
# Посмотрим что мы собрали

print("=" * 60)
print("СТАТИСТИКА СОБРАННЫХ ПАРТИЙ")
print("=" * 60)

# Сколько партий у каждого игрока
print("\n📊 Количество партий каждого игрока (как белые + как чёрные):")
for name in players.keys():
    as_white = len(df_games[df_games["white"] == name])
    as_black = len(df_games[df_games["black"] == name])
    total = as_white + as_black
    print(f"   {name}: {total} партий ({as_white} белыми, {as_black} чёрными)")

# H2H для матчей Round 1
print("\n📊 Head-to-head для матчей Round 1:")
for player_a, player_b in bracket_r1:
    # Партии где A белые, B чёрные
    ab = df_games[(df_games["white"] == player_a) & (df_games["black"] == player_b)]
    # Партии где B белые, A чёрные
    ba = df_games[(df_games["white"] == player_b) & (df_games["black"] == player_a)]
    
    a_wins = len(ab[ab["result"] == 1]) + len(ba[ba["result"] == 0])
    b_wins = len(ab[ab["result"] == 0]) + len(ba[ba["result"] == 1])
    draws = len(ab[ab["result"] == 0.5]) + len(ba[ba["result"] == 0.5])
    total = a_wins + b_wins + draws
    
    if total > 0:
        a_winrate = a_wins / total * 100
        print(f"   {player_a} vs {player_b}: {a_wins}-{draws}-{b_wins} ({total} партий, {player_a} winrate: {a_winrate:.1f}%)")
    else:
        print(f"   {player_a} vs {player_b}: НЕТ ПАРТИЙ")


# ============================================================
# ЯЧЕЙКА 6: Feature Engineering (Создание фичей)
# ============================================================
#
# Это КЛЮЧЕВОЙ шаг. Мы берём сырые данные и создаём из них
# ФИЧИ (features) — числовые характеристики, которые модель
# будет использовать для предсказания.
#
# Для каждой пары игроков (A vs B) создаём:
# 1. Разница blitz рейтингов (A - B)
# 2. Разница bullet рейтингов (A - B)
# 3. H2H winrate A против B в блиц
# 4. H2H winrate A против B в буллет
# 5. Общее количество партий между ними
# 6. Разница лучших рейтингов (best)

def get_rating(name, col):
    """Получить рейтинг игрока по имени и столбцу"""
    row = df_ratings[df_ratings["name"] == name]
    if len(row) == 0:
        return None
    return row[col].values[0]

def get_h2h_stats(player_a, player_b, time_class=None):
    """
    Получить статистику h2h между двумя игроками.
    
    Возвращает: (wins_a, draws, wins_b, total_games)
    
    time_class: "blitz", "bullet", или None (все)
    """
    # Фильтруем по time_class если указан
    if time_class:
        games = df_games[df_games["time_class"] == time_class]
    else:
        games = df_games
    
    # A белые, B чёрные
    ab = games[(games["white"] == player_a) & (games["black"] == player_b)]
    # B белые, A чёрные
    ba = games[(games["white"] == player_b) & (games["black"] == player_a)]
    
    a_wins = len(ab[ab["result"] == 1]) + len(ba[ba["result"] == 0])
    b_wins = len(ab[ab["result"] == 0]) + len(ba[ba["result"] == 1])
    draws = len(ab[ab["result"] == 0.5]) + len(ba[ba["result"] == 0.5])
    total = a_wins + b_wins + draws
    
    return a_wins, draws, b_wins, total

def build_match_features(player_a, player_b):
    """
    Создать вектор фичей для матча player_a vs player_b.
    
    Возвращает словарь с фичами.
    """
    # Рейтинги
    blitz_a = get_rating(player_a, "blitz_rating")
    blitz_b = get_rating(player_b, "blitz_rating")
    bullet_a = get_rating(player_a, "bullet_rating")
    bullet_b = get_rating(player_b, "bullet_rating")
    blitz_best_a = get_rating(player_a, "blitz_best")
    blitz_best_b = get_rating(player_b, "blitz_best")
    bullet_best_a = get_rating(player_a, "bullet_best")
    bullet_best_b = get_rating(player_b, "bullet_best")
    
    # H2H статистика
    h2h_blitz = get_h2h_stats(player_a, player_b, "blitz")
    h2h_bullet = get_h2h_stats(player_a, player_b, "bullet")
    h2h_all = get_h2h_stats(player_a, player_b)
    
    # Winrate A в h2h (если есть партии)
    def winrate(wins_a, draws, wins_b, total):
        if total == 0:
            return 0.5  # если нет данных — считаем 50/50
        return (wins_a + 0.5 * draws) / total
    
    wr_blitz = winrate(*h2h_blitz)
    wr_bullet = winrate(*h2h_bullet)
    wr_all = winrate(*h2h_all)
    
    features = {
        "player_a": player_a,
        "player_b": player_b,
        
        # Разницы рейтингов (A - B). Положительное = A сильнее.
        "blitz_diff": (blitz_a or 0) - (blitz_b or 0),
        "bullet_diff": (bullet_a or 0) - (bullet_b or 0),
        "blitz_best_diff": (blitz_best_a or 0) - (blitz_best_b or 0),
        "bullet_best_diff": (bullet_best_a or 0) - (bullet_best_b or 0),
        
        # Средний рейтинг (показывает общий уровень матча)
        "avg_blitz": ((blitz_a or 0) + (blitz_b or 0)) / 2,
        "avg_bullet": ((bullet_a or 0) + (bullet_b or 0)) / 2,
        
        # H2H winrate (от 0 до 1, где 1 = A всегда побеждает)
        "h2h_winrate_blitz": wr_blitz,
        "h2h_winrate_bullet": wr_bullet,
        "h2h_winrate_all": wr_all,
        
        # Количество h2h партий (больше партий = надёжнее статистика)
        "h2h_games_blitz": h2h_blitz[3],
        "h2h_games_bullet": h2h_bullet[3],
        "h2h_games_total": h2h_all[3],
        
        # ELO expected score (формула из шахмат)
        # E = 1 / (1 + 10^((Rb - Ra)/400))
        "elo_expected_blitz": 1 / (1 + 10**((( blitz_b or 0) - (blitz_a or 0))/400)),
        "elo_expected_bullet": 1 / (1 + 10**(((bullet_b or 0) - (bullet_a or 0))/400)),
    }
    
    return features

# Тест: посмотрим фичи для одного матча
test_features = build_match_features("Hikaru Nakamura", "Jose Martinez")
print("Пример фичей для Hikaru vs Jose Martinez:")
for k, v in test_features.items():
    if k not in ["player_a", "player_b"]:
        print(f"   {k}: {v}")


# ============================================================
# ЯЧЕЙКА 7: Создание обучающей выборки
# ============================================================
#
# Теперь самое интересное. Нам нужен ДАТАСЕТ для обучения модели.
# 
# Каждая строка = одна партия между двумя нашими игроками.
# Фичи = разницы рейтингов, h2h статистика.
# Target = кто победил (1 = белые, 0 = чёрные).
#
# НО! Мы хотим предсказывать не отдельные партии, а МАТЧИ
# (серии из ~20-30 партий). Поэтому мы будем обучать модель
# на отдельных партиях, а потом через Monte Carlo моделировать
# целый матч.

training_data = []

for _, game in df_games.iterrows():
    # iterrows() — перебирает строки DataFrame одну за одной
    # _ — индекс строки (нам не нужен, поэтому _)
    # game — одна строка (как словарь)
    
    white = game["white"]
    black = game["black"]
    
    features = build_match_features(white, black)
    features["result"] = game["result"]  # 1, 0, или 0.5
    features["time_class"] = game["time_class"]
    
    training_data.append(features)

df_train = pd.DataFrame(training_data)

print(f"✅ Обучающая выборка: {len(df_train)} партий")
print(f"   Средний результат: {df_train['result'].mean():.3f}")
print(f"   (должно быть около 0.5 если данные сбалансированы)")
print(f"\nПервые 5 строк:")
print(df_train[["player_a", "player_b", "blitz_diff", "bullet_diff", 
                 "h2h_winrate_all", "result"]].head())


# ============================================================
# ЯЧЕЙКА 8: Обучение XGBoost модели
# ============================================================

# Устанавливаем XGBoost если ещё нет
# !pip install xgboost

from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

# Фичи, которые подаём в модель (только числовые столбцы)
feature_columns = [
    "blitz_diff", "bullet_diff",
    "blitz_best_diff", "bullet_best_diff",
    "avg_blitz", "avg_bullet",
    "h2h_winrate_blitz", "h2h_winrate_bullet", "h2h_winrate_all",
    "h2h_games_blitz", "h2h_games_bullet", "h2h_games_total",
    "elo_expected_blitz", "elo_expected_bullet",
]

# Для XGBoost нам нужна бинарная задача: победа или поражение
# Ничьи (0.5) превращаем в вероятности:
# result > 0.5 → класс 1 (белые победили)
# result < 0.5 → класс 0 (чёрные победили)
# result == 0.5 → пока уберём из обучения (или случайно распределим)

# Убираем ничьи для простоты обучения
df_train_no_draws = df_train[df_train["result"] != 0.5].copy()
df_train_no_draws["target"] = (df_train_no_draws["result"] == 1).astype(int)

X = df_train_no_draws[feature_columns].values  # матрица фичей (NumPy array)
y = df_train_no_draws["target"].values          # вектор целевых значений

print(f"Обучающая выборка (без ничьих): {len(X)} партий")
print(f"Побед белых: {y.sum()} ({y.mean()*100:.1f}%)")
print(f"Побед чёрных: {len(y) - y.sum()} ({(1-y.mean())*100:.1f}%)")

# Создаём модель XGBoost
# Объяснение каждого параметра:
model = XGBClassifier(
    n_estimators=200,        # 200 деревьев (каждое следующее исправляет ошибки предыдущих)
    max_depth=4,             # максимальная глубина каждого дерева (не слишком сложное)
    learning_rate=0.05,      # маленький шаг обучения (η) — медленно но точно
    subsample=0.8,           # каждое дерево видит 80% данных (защита от переобучения)
    colsample_bytree=0.8,    # каждое дерево видит 80% фичей
    reg_lambda=1.0,          # L2 регуляризация (λ из формулы)
    reg_alpha=0.1,           # L1 регуляризация
    random_state=42,         # фиксируем случайность для воспроизводимости
    eval_metric="logloss",   # метрика — binary cross-entropy
)

# Кросс-валидация (5 разбиений)
scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
print(f"\n📊 Cross-validation accuracy: {scores.mean():.3f} ± {scores.std():.3f}")
print(f"   По разбиениям: {[f'{s:.3f}' for s in scores]}")

# Обучаем финальную модель на ВСЕХ данных
model.fit(X, y)
print(f"\n✅ Модель обучена на {len(X)} партиях")

# Важность фичей — какие фичи модель считает самыми полезными
importances = model.feature_importances_
print("\n📊 Важность фичей (чем больше — тем важнее):")
for feat, imp in sorted(zip(feature_columns, importances), key=lambda x: -x[1]):
    bar = "█" * int(imp * 50)
    print(f"   {feat:25s} {imp:.3f} {bar}")


# ============================================================
# ЯЧЕЙКА 9: Функция предсказания матча
# ============================================================
#
# Здесь мы используем ОБУЧЕННУЮ модель для предсказания.
# Но помни — модель предсказывает одну ПАРТИЮ.
# Матч = серия из ~25-30 партий.
# Поэтому используем Monte Carlo симуляцию.

def predict_single_game(player_a, player_b):
    """
    Предсказать вероятность победы player_a (как белые) в одной партии.
    
    Возвращает: вероятность от 0 до 1
    """
    features = build_match_features(player_a, player_b)
    X_pred = np.array([[features[col] for col in feature_columns]])
    prob = model.predict_proba(X_pred)[0][1]  # вероятность класса 1 (победа белых)
    return prob

def simulate_match(player_a, player_b, n_simulations=10000):
    """
    Симулировать полный матч Speed Chess Championship.
    
    Матч состоит из 3 частей:
    - 75 мин 5+1 blitz (~15 партий)
    - 50 мин 3+1 blitz (~12 партий)  
    - 25 мин 1+1 bullet (~12 партий)
    
    Каждая партия: 1 очко за победу, 0.5 за ничью, 0 за поражение.
    
    Возвращает: (prob_a_wins, avg_score_a, avg_score_b)
    """
    # Вероятности для одной партии
    # A играет белыми
    prob_a_white = predict_single_game(player_a, player_b)
    # A играет чёрными (= 1 - prob B white wins)
    prob_a_black = 1 - predict_single_game(player_b, player_a)
    
    # Средняя вероятность победы A в одной партии (с учётом цвета)
    prob_a_win = (prob_a_white + prob_a_black) / 2
    prob_b_win = 1 - prob_a_win
    
    # Вероятность ничьей (оценка на основе уровня игроков)
    # На высоком уровне ~20-30% ничьих в блиц, ~10-15% в буллет
    draw_rate_blitz = 0.15
    draw_rate_bullet = 0.08
    
    a_match_wins = 0
    total_score_a = 0
    total_score_b = 0
    
    for _ in range(n_simulations):
        score_a = 0
        score_b = 0
        
        # Часть 1: 5+1 blitz (~15 партий)
        for game_num in range(15):
            r = np.random.random()
            if r < draw_rate_blitz:
                score_a += 0.5
                score_b += 0.5
            elif r < draw_rate_blitz + prob_a_win * (1 - draw_rate_blitz):
                score_a += 1
            else:
                score_b += 1
        
        # Часть 2: 3+1 blitz (~12 партий)
        for game_num in range(12):
            r = np.random.random()
            if r < draw_rate_blitz:
                score_a += 0.5
                score_b += 0.5
            elif r < draw_rate_blitz + prob_a_win * (1 - draw_rate_blitz):
                score_a += 1
            else:
                score_b += 1
        
        # Часть 3: 1+1 bullet (~12 партий)
        for game_num in range(12):
            r = np.random.random()
            if r < draw_rate_bullet:
                score_a += 0.5
                score_b += 0.5
            elif r < draw_rate_bullet + prob_a_win * (1 - draw_rate_bullet):
                score_a += 1
            else:
                score_b += 1
        
        # Тайбрейк если ничья
        if score_a == score_b:
            if np.random.random() < prob_a_win:
                score_a += 0.5  # символический +0.5 за тайбрейк
            else:
                score_b += 0.5
        
        if score_a > score_b:
            a_match_wins += 1
        
        total_score_a += score_a
        total_score_b += score_b
    
    prob_a_wins_match = a_match_wins / n_simulations
    avg_a = total_score_a / n_simulations
    avg_b = total_score_b / n_simulations
    
    return prob_a_wins_match, avg_a, avg_b

# Тест
print("Тестируем предсказание: Hikaru vs Jose Martinez")
prob, sa, sb = simulate_match("Hikaru Nakamura", "Jose Martinez", n_simulations=5000)
print(f"  P(Hikaru побеждает) = {prob*100:.1f}%")
print(f"  Средний счёт: {sa:.1f} - {sb:.1f}")


# ============================================================
# ЯЧЕЙКА 10: ПРЕДСКАЗАНИЕ ВСЕГО ТУРНИРА
# ============================================================

print("=" * 70)
print("🏆 SPEED CHESS CHAMPIONSHIP 2024 — ПРЕДСКАЗАНИЕ")
print("=" * 70)

N_SIM = 10000  # количество симуляций (больше = точнее, но дольше)

# =================== ROUND 1 (1/8 ФИНАЛА) ===================
print("\n🔸 ROUND 1 (1/8 финала)")
print("-" * 70)

r1_winners = []

for i, (player_a, player_b) in enumerate(bracket_r1):
    prob_a, score_a, score_b = simulate_match(player_a, player_b, N_SIM)
    
    winner = player_a if prob_a > 0.5 else player_b
    r1_winners.append(winner)
    
    # Красивый вывод
    marker_a = "🏆" if prob_a > 0.5 else "  "
    marker_b = "🏆" if prob_a <= 0.5 else "  "
    
    print(f"\n  Матч {chr(65+i)}: {player_a} vs {player_b}")
    print(f"  {marker_a} {player_a:30s} {prob_a*100:5.1f}%  (≈{score_a:.1f})")
    print(f"  {marker_b} {player_b:30s} {(1-prob_a)*100:5.1f}%  (≈{score_b:.1f})")
    print(f"  Предсказание: {winner} побеждает ≈{score_a:.1f}-{score_b:.1f}")

# =================== ЧЕТВЕРТЬФИНАЛЫ ===================
print("\n\n🔸 ЧЕТВЕРТЬФИНАЛЫ")
print("-" * 70)

bracket_qf = [
    (r1_winners[0], r1_winners[1]),  # Winner A vs Winner B
    (r1_winners[2], r1_winners[3]),  # Winner C vs Winner D
    (r1_winners[4], r1_winners[5]),  # Winner E vs Winner F
    (r1_winners[6], r1_winners[7]),  # Winner G vs Winner H
]

qf_winners = []
qf_losers = []

for i, (player_a, player_b) in enumerate(bracket_qf):
    prob_a, score_a, score_b = simulate_match(player_a, player_b, N_SIM)
    
    winner = player_a if prob_a > 0.5 else player_b
    loser = player_b if prob_a > 0.5 else player_a
    qf_winners.append(winner)
    qf_losers.append(loser)
    
    marker_a = "🏆" if prob_a > 0.5 else "  "
    marker_b = "🏆" if prob_a <= 0.5 else "  "
    
    print(f"\n  Матч {chr(73+i)}: {player_a} vs {player_b}")
    print(f"  {marker_a} {player_a:30s} {prob_a*100:5.1f}%  (≈{score_a:.1f})")
    print(f"  {marker_b} {player_b:30s} {(1-prob_a)*100:5.1f}%  (≈{score_b:.1f})")
    print(f"  Предсказание: {winner} побеждает ≈{score_a:.1f}-{score_b:.1f}")

# =================== ПОЛУФИНАЛЫ ===================
print("\n\n🔸 ПОЛУФИНАЛЫ")
print("-" * 70)

bracket_sf = [
    (qf_winners[0], qf_winners[1]),  # Winner I vs Winner J
    (qf_winners[2], qf_winners[3]),  # Winner K vs Winner L
]

sf_winners = []
sf_losers = []

for i, (player_a, player_b) in enumerate(bracket_sf):
    prob_a, score_a, score_b = simulate_match(player_a, player_b, N_SIM)
    
    winner = player_a if prob_a > 0.5 else player_b
    loser = player_b if prob_a > 0.5 else player_a
    sf_winners.append(winner)
    sf_losers.append(loser)
    
    marker_a = "🏆" if prob_a > 0.5 else "  "
    marker_b = "🏆" if prob_a <= 0.5 else "  "
    
    print(f"\n  Полуфинал {i+1}: {player_a} vs {player_b}")
    print(f"  {marker_a} {player_a:30s} {prob_a*100:5.1f}%  (≈{score_a:.1f})")
    print(f"  {marker_b} {player_b:30s} {(1-prob_a)*100:5.1f}%  (≈{score_b:.1f})")
    print(f"  Предсказание: {winner} побеждает ≈{score_a:.1f}-{score_b:.1f}")

# =================== МАТЧ ЗА 3-Е МЕСТО ===================
print("\n\n🔸 МАТЧ ЗА 3-Е МЕСТО")
print("-" * 70)

third_a, third_b = sf_losers[0], sf_losers[1]
prob_a, score_a, score_b = simulate_match(third_a, third_b, N_SIM)
third_place = third_a if prob_a > 0.5 else third_b
fourth_place = third_b if prob_a > 0.5 else third_a

marker_a = "🏆" if prob_a > 0.5 else "  "
marker_b = "🏆" if prob_a <= 0.5 else "  "

print(f"\n  {third_a} vs {third_b}")
print(f"  {marker_a} {third_a:30s} {prob_a*100:5.1f}%  (≈{score_a:.1f})")
print(f"  {marker_b} {third_b:30s} {(1-prob_a)*100:5.1f}%  (≈{score_b:.1f})")
print(f"  Предсказание: {third_place} побеждает ≈{score_a:.1f}-{score_b:.1f}")

# =================== ФИНАЛ ===================
print("\n\n🏆 ФИНАЛ")
print("-" * 70)

final_a, final_b = sf_winners[0], sf_winners[1]
prob_a, score_a, score_b = simulate_match(final_a, final_b, N_SIM)
champion = final_a if prob_a > 0.5 else final_b
runner_up = final_b if prob_a > 0.5 else final_a

marker_a = "🏆" if prob_a > 0.5 else "  "
marker_b = "🏆" if prob_a <= 0.5 else "  "

print(f"\n  {final_a} vs {final_b}")
print(f"  {marker_a} {final_a:30s} {prob_a*100:5.1f}%  (≈{score_a:.1f})")
print(f"  {marker_b} {final_b:30s} {(1-prob_a)*100:5.1f}%  (≈{score_b:.1f})")
print(f"  Предсказание: {champion} побеждает ≈{score_a:.1f}-{score_b:.1f}")

# =================== ИТОГОВЫЙ РЕЙТИНГ ===================
print("\n\n" + "=" * 70)
print("🏆 ИТОГОВЫЕ РЕЗУЛЬТАТЫ")
print("=" * 70)
print(f"\n  🥇 1-е место:  {champion}")
print(f"  🥈 2-е место:  {runner_up}")
print(f"  🥉 3-е место:  {third_place}")
print(f"  4-е место:     {fourth_place}")
print("\n" + "=" * 70)
