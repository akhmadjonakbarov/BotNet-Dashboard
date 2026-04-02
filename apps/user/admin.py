from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from apps.user.models import User
from config.security import get_password_hash


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, ]
    column_searchable_list = [User.username]

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        # data: The raw dictionary from the form
        # model: The existing database object (if is_created is False)
        # is_created: True if it's a new record, False if it's an update

        if not is_created:
            print(f"Updating user: {model.username}")

        # Example: Automatically hash a password if it was changed
        if "password" in data:
            data["password"] = get_password_hash(data["password"])
