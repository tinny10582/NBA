import requests

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1492283303217070080/lbrvzppTz-h9EcshXSHue6NOtAJY31CjT1jWPmS0U_2MV8Ps1O1zp--rPuoGF9LlNNGk"

msg = "🔥 NBA自動系統測試成功"

requests.post(DISCORD_WEBHOOK, json={"content": msg})

print(msg)
