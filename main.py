import requests
import pandas as pd

# ===============================
# 🔑 設定
# ===============================
ODDS_API_KEY = "459db2b0ceca5d2103a479358f6b163b"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1492283303217070080/lbrvzppTz-h9EcshXSHue6NOtAJY31CjT1jWPmS0U_2MV8Ps1O1zp--rPuoGF9LlNNGk  "

# ===============================
# 📊 假資料（之後可換API）
# ===============================
team_stats = {
    "Lakers": {"off":115,"def":112,"pace":100},
    "Warriors": {"off":118,"def":115,"pace":102},
    "Celtics": {"off":117,"def":110,"pace":99},
    "Bucks": {"off":116,"def":111,"pace":101},
}

# ===============================
# 📊 抓賠率
# ===============================
def get_odds():
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={ODDS_API_KEY}&regions=us&markets=h2h"
    res = requests.get(url)

    if res.status_code != 200:
        return pd.DataFrame()

    data = res.json()
    games = []

    for game in data:
        home = game["home_team"]
        away = game["away_team"]

        games.append({
            "home": home,
            "away": away
        })

    return pd.DataFrame(games)

# ===============================
# 🧠 真實模型
# ===============================
def predict(home, away):

    if home not in team_stats or away not in team_stats:
        return None

    A = team_stats[home]
    B = team_stats[away]

    pace = (A["pace"] + B["pace"]) / 200

    score_home = (A["off"] + B["def"]) / 2 * pace
    score_away = (B["off"] + A["def"]) / 2 * pace

    total = score_home + score_away
    diff = score_home - score_away

    prob = 0.55 + (diff / 50)

    return score_home, score_away, total, diff, prob

# ===============================
# ⭐ 星級
# ===============================
def get_star(prob):
    if prob >= 0.60:
        return 3
    elif prob >= 0.57:
        return 2
    else:
        return 1

# ===============================
# 🎯 分析
# ===============================
def analyze(df):

    results = []

    for _, row in df.iterrows():
        p = predict(row["home"], row["away"])

        if not p:
            continue

        sh, sa, total, diff, prob = p

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
# 🔗 串關
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
    send("❌ 無比賽")
else:

    result = analyze(df)

    if result.empty:
        send("無分析資料")
    else:

        parlay = build_parlay(result)

        msg = "🔥【NBA進階分析】🔥\n━━━━━━━━\n\n"

        for s in [3,2,1]:
            sub = result[result["star"] == s]
            if len(sub)>0:
                msg += f"⭐{s}星\n"
                for r in sub.itertuples():
                    msg += f"{r.match}\n👉 {r.pick}\n勝率:{round(r.prob*100,1)}%\n\n"

        msg += "━━━━━━━━\n🔥串關推薦\n"

        for i,(a,b) in enumerate(parlay,1):
            msg += f"\n第{i}組\n👉 {a['pick']}（{a['match']}）\n👉 {b['pick']}（{b['match']}）\n"

        send(msg)
