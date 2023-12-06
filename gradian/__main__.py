import asyncio
import engine
import loader

from websockets import WebSocketServerProtocol, serve

modules = loader.load_modules()
if len(modules) == 0:
    print("ERROR: no modules found!")
    exit(-1)

print("Loaded the following modules:")
for idx, module in enumerate(modules):
    print("module id:", idx, "-- module name:", module.NAME)

print()

manager = engine.EngineManager()

async def websocket_handler(websocket: WebSocketServerProtocol):
    try: 
        # If a game is being created
        if websocket.path.startswith("/create/"):
            module_id = int(websocket.path[len("/create/"):])
            module = modules[module_id]

            await manager.create(module, websocket)
            await websocket.wait_closed()

        # If a game is being joined
        elif websocket.path.startswith("/join/"):
            game_id = int(websocket.path[len("/join/"):])
            await manager.join(game_id, websocket)
            await websocket.wait_closed()

    except: 
        await websocket.close()

async def main():
    async with serve(websocket_handler, "", 4000):
        await asyncio.get_running_loop().create_future()

asyncio.run(main())