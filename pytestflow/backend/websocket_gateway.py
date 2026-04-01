import asyncio
import json
import websockets
from pytestflow.backend.event_bus import event_bus
from pytestflow.backend.handlers import init_handlers
from pytestflow.core.runtime_control import runtime_control


async def websocket_handler(ws):
    path = ws.request.path

    if path != "/ws":
        await ws.close(code=1008, reason="Invalid path")
        return

    # Prepare per-connection queue and register subscriber before draining queued updates
    queue = asyncio.Queue()

    async def on_outbound(payload):
        await queue.put(payload)

    event_bus.on("outbound", on_outbound)

    # start outbound sender using the queue; the subscriber is already registered
    sender_task = asyncio.create_task(outbound_sender(ws, queue))

    # Drain existing queued updates so new connection receives pending messages
    loop = asyncio.get_running_loop()
    while True:
        update = await loop.run_in_executor(None, runtime_control.get_gui_update, 0)
        if not update:
            break
        await queue.put(update)

    try:
        async for message in ws:
            data = json.loads(message)
            cmd = data.get("cmd")
            args = data.get("args", {})

            if cmd:
                await event_bus.emit(cmd, args)

    except websockets.ConnectionClosed:
        pass
    finally:
        # cleanup: remove subscriber and cancel sender
        try:
            event_bus._subscribers["outbound"].remove(on_outbound)
        except Exception:
            pass
        sender_task.cancel()


async def outbound_sender(ws, queue: asyncio.Queue):
    try:
        while True:
            payload = await queue.get()
            try:
                await ws.send(json.dumps(payload))
            except Exception as e:
                print("WS send error:", repr(e))
                continue

    except websockets.ConnectionClosed:
        print("WS disconnected")


async def start_server(ws_host, ws_port):    
    loop = asyncio.get_running_loop()
    event_bus.set_loop(loop)
    asyncio.create_task(event_bus.start())  # starts processing the queue
    init_handlers()  # register handlers

    # Start background consumer for in-process GUI updates coming from steps
    async def consume_gui_updates():
        while True:
            # Only dequeue if there's at least one outbound subscriber (a connected client)
            if not event_bus._subscribers.get("outbound"):
                await asyncio.sleep(0.1)
                continue

            # run blocking get in executor
            update = await loop.run_in_executor(None, runtime_control.get_gui_update, 0.5)
            if update:
                await event_bus.emit("outbound", update)
            await asyncio.sleep(0)

    asyncio.create_task(consume_gui_updates())
    async with websockets.serve(websocket_handler, ws_host, ws_port):
        await asyncio.Future()
