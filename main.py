#!/usr/bin/env python3
"""
自動偵測今日最高降雨機率，超過門檻就透過 Telegram 提醒帶傘。
所有敏感資訊都從環境變數讀取，絕不寫死在程式碼中。
"""

import os
import sys
import requests
from datetime import datetime

# ========== 設定區（可依需求修改） ==========
# 預設台北市（你可改成自己的經緯度）
LATITUDE = 25.0330
LONGITUDE = 121.5654
TIMEZONE = "Asia/Taipei"

# 降雨機率門檻（題目標題寫 70%，內文寫 60%，這裡預設 70，可自行調整）
RAIN_THRESHOLD = 70
# ==========================================


def get_today_max_precipitation_probability(lat: float, lon: float, timezone: str) -> int | None:
    """透過 Open-Meteo API 取得今日最高降雨機率"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_probability_max",
        "timezone": timezone,
        "forecast_days": 1,   # 只要今天
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # daily.precipitation_probability_max 是陣列，第一個元素就是今天
        probs = data.get("daily", {}).get("precipitation_probability_max", [])
        if not probs:
            print("API 回傳沒有降雨機率資料")
            return None

        return int(probs[0])
    except Exception as e:
        print(f"取得天氣資料失敗: {e}")
        return None


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """發送 Telegram 訊息（Token 與 Chat ID 從環境變數傳入）"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        print("Telegram 訊息發送成功")
        return True
    except Exception as e:
        print(f"發送 Telegram 失敗: {e}")
        return False


def main():
    # 從環境變數讀取敏感資訊（絕對不能寫死在程式碼）
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("錯誤：請設定環境變數 TELEGRAM_BOT_TOKEN 與 TELEGRAM_CHAT_ID")
        sys.exit(1)

    print(f"開始檢查今日降雨機率（門檻 {RAIN_THRESHOLD}%）...")
    print(f"地點：緯度 {LATITUDE}, 經度 {LONGITUDE}")

    rain_prob = get_today_max_precipitation_probability(LATITUDE, LONGITUDE, TIMEZONE)

    if rain_prob is None:
        print("無法取得降雨機率，結束")
        sys.exit(1)

    print(f"今日最高降雨機率：{rain_prob}%")

    if rain_prob >= RAIN_THRESHOLD:
        today = datetime.now().strftime("%Y-%m-%d")
        message = (
            f"☔ <b>記得帶傘喔！</b>\n\n"
            f"日期：{today}\n"
            f"今日最高降雨機率：<b>{rain_prob}%</b>\n"
            f"（已超過 {RAIN_THRESHOLD}% 門檻）"
        )
        success = send_telegram_message(bot_token, chat_id, message)
        if not success:
            sys.exit(1)
    else:
        print(f"降雨機率 {rain_prob}% 未達門檻，不發送通知")


if __name__ == "__main__":
    main()
