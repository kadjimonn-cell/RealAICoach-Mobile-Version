"""Player 2 opponent bot v3 — retaliate mode + auto-reconnect (survives 60s proxy cap)."""
import asyncio
import json
import math
import sys
import time

import requests
import websockets

BASE = "https://admin-policy-hub.preview.emergentagent.com"
EMAIL = "p1.free.1779113329@example.com"
PASSWORD = "P1Free#2026!Aa"
ROOM = "iter815-enhancements-1"
DURATION = 900

target_id = None
target_pos = [0.0, 1.7, 0.0]
i_died = False
i_am_alive = True
retaliating = False


def log(*args):
    print(f"[{time.strftime('%H:%M:%S')}]", *args, flush=True)


class Api:
    def __init__(self):
        self.s = requests.Session()
        r = self.s.post(f"{BASE}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
        r.raise_for_status()
        self.token = r.json().get("session_token") or self.s.cookies.get("session_token")
        self.uid = r.json()["user_id"]
        self.h = {"Authorization": f"Bearer {self.token}"}

    def join_room(self):
        j = self.s.post(f"{BASE}/api/games-station/rooms/join", headers=self.h,
                        json={"room_name": ROOM, "player_name": "OpponentBot", "model": "roboty"}, timeout=30)
        j.raise_for_status()
        log("REST join:", j.json()["room_id"])

    def ticket(self):
        return self.s.post(f"{BASE}/api/auth/ws-ticket", headers=self.h, json={"channel": "fps_game"}, timeout=30).json()["ticket"]


async def session(api, start):
    global target_id, target_pos, i_died, i_am_alive, retaliating
    url = f"{BASE.replace('https://', 'wss://')}/api/ws/fps/{ROOM}/{api.uid}?ticket={api.ticket()}"
    async with websockets.connect(url, ping_interval=None) as ws:
        log("WS CONNECTED")

        async def sender():
            while True:
                if target_id:
                    pos = [target_pos[0], 1.7, target_pos[2] - 6.0]
                else:
                    pos = [math.sin(time.time()) * 2, 1.7, 6.0]
                await ws.send(json.dumps({"type": "state", "pos": pos, "rot": [math.pi, 0], "anim": "idle"}))
                if retaliating and i_am_alive and target_id:
                    await ws.send(json.dumps({"type": "shoot"}))
                    await ws.send(json.dumps({"type": "hit", "target_id": target_id}))
                    await asyncio.sleep(0.45)
                else:
                    await asyncio.sleep(0.1)

        send_task = asyncio.create_task(sender())
        try:
            while time.time() - start < DURATION:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=10)
                except asyncio.TimeoutError:
                    continue
                msg = json.loads(raw)
                mt = msg.get("type")
                if mt == "joined":
                    others = msg.get("players", [])
                    log("JOINED resumed=", msg.get("resumed"), "others:", [(p["user_id"][:8], p["name"]) for p in others])
                    for p in others:
                        target_id = p["user_id"]
                        target_pos = list(p["pos"])
                elif mt == "player_joined":
                    p = msg["player"]
                    target_id = p["user_id"]
                    target_pos = list(p["pos"])
                    log("PLAYER_JOINED:", p["name"])
                elif mt == "state" and msg.get("user_id") == target_id:
                    target_pos = list(msg["pos"])
                elif mt == "damage":
                    log("DAMAGE: target", msg["target_id"][:8], "hp", msg["hp"], "by", msg["by"][:8])
                elif mt == "kill":
                    log("KILL:", msg["killer_name"], "eliminated", msg["victim_name"])
                    if msg["victim_id"] == api.uid:
                        i_died = True
                        i_am_alive = False
                        log(">>> Bot eliminated — will retaliate after respawn")
                    if msg["victim_id"] == target_id:
                        retaliating = False
                        log(">>> P1 eliminated — retaliation done")
                elif mt == "respawn":
                    if msg["user_id"] == api.uid:
                        i_am_alive = True
                        if i_died:
                            retaliating = True
                            log(">>> RETALIATING")
                    else:
                        log("RESPAWN:", msg["user_id"][:8])
                elif mt == "player_left":
                    log("PLAYER_LEFT:", msg.get("name"))
                    target_id = None
        finally:
            send_task.cancel()


async def main():
    api = Api()
    api.join_room()
    start = time.time()
    while time.time() - start < DURATION:
        try:
            await session(api, start)
            break
        except Exception as exc:
            log("session dropped:", type(exc).__name__, "— reconnecting")
            await asyncio.sleep(0.5)
    log("SESSION END")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        log("BOT ERROR:", repr(exc))
        sys.exit(1)
