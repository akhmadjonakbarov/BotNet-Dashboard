from sqlalchemy import select

from apps.zombie.models import Log, Command
from config.database import async_session_maker


class ResponseProcess:

    @staticmethod
    async def process_zombie_response(zombie_id: str, cmd_id: int, output: str):
        print("[+] Handles the heavy lifting of DB logging and status updates.")
        async with async_session_maker() as session:
            try:
                new_log = Log(
                    zombie_id=int(zombie_id),
                    command_id=int(cmd_id),
                    output_data=str(output)
                )
                session.add(new_log)

                query = select(Command).where(Command.id == int(cmd_id))
                result = await session.execute(query)
                command = result.scalar_one_or_none()

                if command:
                    command.status = "completed"

                await session.commit()
            except Exception as e:
                await session.rollback()
                print(f"[!] DB Error processing response for zombie {zombie_id}: {e}")
