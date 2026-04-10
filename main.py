import requests
import pandas as pd

# ===============================
# 🔑 設定
# ===============================
ODDS_API_KEY = "459db2b0ceca5d2103a479358f6b163b"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1492283303217070080/lbrvzppTz-h9EcshXSHue6NOtAJY31CjT1jWPmS0U_2MV8Ps1O1zp--rPuoGF9LlNNGk"


# ===============================
# 📊 基礎球隊數據（可自行擴充）
# ===============================
team_stats = {
    "Lakers": {"off":115,"def":112,"pace":100},
    "Warriors": {"off":118,"def":115,"pace":102},
    "Celtics": {"off":117,"def":110,"pace":99},
    "Bucks": {"off":116,"def":111,"pace":101},
    "Nuggets": {"off":117,"def":112,"pace":98},
    "Suns": {"off":116,"def":113,"pace":100},
    "Heat": {"off":110,"def":108,"pace":96},
    "Clippers": {"off":114,"def":111,"pace":99},
}

# ===============================
# 📊 抓NBA賠率
# ===============================
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h"
    res = requests.get(url)

    if res.status_code != 200:
        return pd.DataFrame()

    data = res.json()
    games = []

    for game in data:
        games.append({
            "home": game["home_team"],
            "away": game["away_team"]
        })

    return pd.DataFrame(games)

# ===============================
# 🧠 預測模型（改良版）
# ===============================
def predict(home, away):

    # 👉 若沒有資料，自動補平均值（重點修正）
    if home not in team_stats:
        team_stats[home] = {"off":112,"def":112,"pace":100}
    if away not in team_stats:
        team_stats[away] = {"off":112,"def":112,"pace":100}

    A = team_stats[home]
    B = team_stats[away]

    pace = (A["pace"] + B["pace"]) / 200

    score_home = (A["off"] + B["def"]) / 2 * pace
    score_away = (B["off"] + A["def"]) / 2 * pace

    total = score_home + score_away
    diff = score_home - score_away

    prob = 0.5 + (diff / 40)

    return score_home, score_away, total, diff, prob

# ===============================
# ⭐ 星級評分
# ===============================
def get_star(prob):
    if prob >= 0.60:
        return 3
    elif prob >= 0.56:
        return 2
    else:
        return 1

# ===============================
# 🎯 分析
# ===============================
def analyze(df):

    results = []

    for _, row in df.iterrows():

        sh, sa, total, diff, prob = predict(row["home"], row["away"])

        pick_total = "大分" if total > 215 else "小分"
        pick_ml = row["home"] if diff > 0 else row["away"]

        star = get_star(prob)

        results.append({
            "match": f"{row['away']} vs {row['home']}",
            "pick": pick_total,
            "prob": prob,
            "star": star
        })

    return pd.DataFrame(results)

# ===============================
# 🔗 串關（固定2關）
# ===============================
def build_parlay(df):

    df = df.sort_values(by=["star","prob"], ascending=False)

    combos = []

    for i in range(len(df)):
        for j in range(i+1, len(df)):
            if df.iloc[i]["match"] != df.iloc[j]["match"]:
                combos.append((df.iloc[i], df.iloc[j]))

    return combos[:3]

# ===============================
# 📲 發送
# ===============================
def send(msg):
    requests.post(DISCORD_WEBHOOK, json={"content": msg})

# ===============================
# 🚀 主程式
# ===============================
df = get_odds()

if df.empty:
    send("❌ 今日無比賽或API錯誤")
else:

    result = analyze(df)

    parlay = build_parlay(result)

    msg = "🔥【NBA進階分析】🔥\n━━━━━━━━━━\n\n"

    for s in [3,2,1]:
        sub = result[result["star"] == s]
        if len(sub) > 0:
            msg += f"⭐{s}星\n"
            for r in sub.itertuples():
                msg += f"{r.match}\n👉 {r.pick}\n勝率:{round(r.prob*100,1)}%\n\n"

    msg += "━━━━━━━━━━\n🔥串2關推薦\n"

    for i,(a,b) in enumerate(parlay,1):
        msg += f"\n第{i}組\n👉 {a['pick']}（{a['match']}）\n👉 {b['pick']}（{b['match']}）\n"

    msg += "\n━━━━━━━━━━\n⚠️ 由高星開始下注"

    send(msg)

send("🔥 測試成功")
