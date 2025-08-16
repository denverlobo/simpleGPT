# model_worker.py
from fastapi import FastAPI, Request
import uvicorn
import sys
from langchain_community.llms import LlamaCpp
from config import *
from contextlib import asynccontextmanager
import time

llm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm
    model_path = sys.argv[1]
    print(f"\n🔄 Loading model: {model_path}", flush=True)
    start = time.time()
    llm = LlamaCpp(
                    model_path=model_path,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_NEW_TOKENS,
                    n_gpu_layers=N_GPU_LAYERS,
                    n_ctx=N_CTX,
                    top_p=TOP_P,
                    repeat_penalty=REPEAT_PENALTY,  
                    n_threads=CPU_CORES,
                    verbose=False
                )
    print(f"Model {model_path} loaded in {time.time() - start:.2f}s\n", flush=True)
            
    yield  # Application runs here
    print(f"Shutting down model server {model_path}...", flush=True)


app = FastAPI(lifespan=lifespan)

@app.post("/invoke")
async def invoke(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    if not llm:
        return {"error": "Model not loaded"}
    try:
        # Overrides per call
        temperature = body.get("temperature", TEMPERATURE)
        top_p = body.get("top_p", TOP_P)
        max_tokens = body.get("max_tokens", MAX_NEW_TOKENS)
        repeat_penalty = body.get("repeat_penalty", REPEAT_PENALTY)

        response = llm.invoke(
            prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repeat_penalty=repeat_penalty
            
        )
        
        return {"response": response}
    except Exception as e:
        print("Error occurred while invoking model", flush=True)
        return {"error": str(e)}

@app.get("/health")
async def health():
    global llm
    return { "model_loaded": llm is not None}

def run_server(model_path: str, port: int):
    sys.argv = ["model_server.py", model_path, str(port)]
    uvicorn.run(app, host="127.0.0.1", port=port)
