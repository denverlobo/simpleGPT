# main.py
from fastapi import FastAPI, Request
from multiprocessing import Process
import httpx
from contextlib import asynccontextmanager
from model_server import run_server
from config import *
import asyncio
import uvicorn

processes = {}

async def wait_for_ready(port: int, timeout: int = MODEL_LOAD_TIMEOUT):
    url = f"http://127.0.0.1:{port}/health"
    for i in range(timeout):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                if resp.status_code == 200 and resp.json().get("model_loaded"):
                    print(f"✅ Model on port {port} is ready.", flush=True)
                    return True
        except Exception:
            pass
        if (i+1) % 4 == 0:
            print(f"⏳ Waiting for model on port {port} to be ready... ({(i+1)*5}s)", flush=True) # Prints every 20secs
        await asyncio.sleep(5)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    for name, config in MODELS.items():
        print(f"🚀 Launching {name} on port {config['port']}", flush=True)
        proc = Process(target=run_server, args=(config["path"], config["port"]))
        try:
            proc.start()
        except Exception as e:
            print(f"Error launching {name}: {e}", flush=True)
            continue
        processes[name] = proc

        # Wait for model to be ready before continuing
        ready = await wait_for_ready(config["port"])
        if not ready:
            print(f"❌ {name} failed to become ready — skipping remaining models.", flush=True)
            break
        
    yield  # App runs here

    # Shutdown logic
    for proc in processes.values():
        proc.terminate()

app = FastAPI(lifespan=lifespan)

@app.post("/generate")
async def invoke(request: Request):
    body = await request.json()
    model = body.get("model")
    prompt = body.get("prompt")

    if model not in MODELS:
        return {"error": f"Unknown model: {model}"}

    port = MODELS[model]["port"]
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(f"http://127.0.0.1:{port}/invoke", json={"prompt": prompt})
            return response.json()
    except httpx.ReadTimeout:
        return {"error": f"Model {model} timed out while generating response."}



# To check if the status of models loading. 
@app.get("/health")
async def health():
    results = {}    
    async with httpx.AsyncClient() as client:
        for name, config in MODELS.items():
            try:
                r = await client.get(f"http://127.0.0.1:{config['port']}/health", timeout=2.0)
                data = r.json()
                results[f'{name}_loaded'] = data["model_loaded"]
            except Exception as e:
                results[f'{name}_loaded'] = False
    return results

if __name__ == "__main__":
    uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=False, log_level=LOG_LEVEL)

