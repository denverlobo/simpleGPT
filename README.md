# simpleGPT

**Serve multiple LLMs locally using LangChain + llama-cpp-python, orchestrated with FastAPI and Docker.**  
*GPU with CUDA is recommended for best performance.*

---

## 📦 Project Overview

**simpleGPT** enables you to serve multiple Large Language Models (LLMs) on your local machine.  
Each model runs in its own isolated process, managed by a FastAPI orchestrator and containerized with Docker for easy deployment and resource control.  
A CUDA-capable GPU is highly recommended for optimal performance.

---

## 🧩 Architecture

**Main Components:**
- **Docker**: Containerization and resource isolation
- **Python**: Core programming language
- **llama-cpp-python**: LLM backend (GGUF models)
- **LangChain**: Model wrapper
- **FastAPI**: API orchestration
- **Uvicorn**: ASGI server

**How It Works:**

- llama-cpp-python uses a global context under the hood (via C++ bindings). Which is why when you try to load a second model, it clobbers or conflicts with the first one.
- The FastAPI orchestrator launches a separate process for each model. 
- Each model server listens on its own port (e.g., 8001, 8002, ...).
- The main API stays on `localhost:8000` and routes requests to the correct model subprocess based on the `model` parameter.


```
Client → localhost:8000/generate
             │
             └── FastAPI orchestrator
                     ├── model1_worker (port 8001)
                     ├── model2_worker (port 8002)
                     └── model3_worker (port 8003)
```
---

## 🛠️ Setup Guide

### 1️⃣ Get GGUF Models

- **Download from Hugging Face:**  
  Find pre-converted GGUF models (often quantized for llama.cpp) on [Hugging Face](https://huggingface.co/).  
  Look for models labeled as GGUF for compatibility.

- **Convert from Safetensors:**  
  If you have a model in safetensors format, use the conversion scripts from the [llama.cpp repository](https://github.com/ggerganov/llama.cpp) to convert to GGUF.

---

### 2️⃣ Organize Model Volumes

- Only **GGUF** format is supported (optimized for llama.cpp).
- Other formats (e.g., PyTorch, HF Transformers) are **not supported**.

**Directory Structure Example:**
```
C:/Users/<user>/models/
					│
					├──model1 (<model_folder>)
					│		 ├── model.gguf
					│		 └── <model_name>.txt (Empty file to identify the model once loaded on docker container)
					│
					└──model2 <model_folder>
							 ├── model.gguf
							 └── <model_name>.txt (Empty file to identify the model once loaded on docker container)
```

**Create Docker Volumes:**
```bash
docker volume create <model_name>
docker run --rm -v <model_name>:/data -v C:/Users/<user>/models/<model_folder>:/source alpine sh -c "cp -r /source/* /data/"
```

---



#### Worker Server (model_server.py)
```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup logic that loads the model

    @app.post("/invoke")
    async def invoke(request: Request):
        # code logic to invoke the LLM
```
 - This script runs a FastAPI app that loads a single model and exposes /invoke.

#### Orchestrator (main.py)
This script launches subprocesses for each model using multiprocessing.Process.
```python
    proc = Process(target=run_server, args=(config["path"], config["port"]))
    proc.start()
```
```python
	@app.post("/generate")
	async  def  invoke(request: Request):
		# logic to invoke the appropriate model
```
---
### 3️⃣  Docker Container Setup
Ensure model volumes are created before building the container.
The provided Dockerfile sets up all dependencies. For local deployment, install the pip dependencies from the *****requirements.txt*****. 
To enable **CUDA** support, set the appropriate environment variable **before installing** `llama-cpp-python`. If you encounter issues during installation, you can bypass the build process by downloading a **precompiled wheel** with CUDA support and installing it directly using `pip`

```bash
export CMAKE_ARGS="-DLLAMA_CUDA=on"
pip install llama-cpp-python
```

🚀 Running simpleGPT
Start the orchestrator locally:
```bash
pip install -r requirements.txt
python main.py
```


Build and run with Docker Compose:
```bash
docker compose up -d --build
```



🧪 Testing the API
Basic request:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "<model1>", "prompt": "What is the capital of France?"}'
```


With additional parameters:
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "<model1>", "prompt": "What is the capital of France?", "max_new_tokens": 200, "temperature": "0.7"}'
```

📝 Notes
Ensure all models are in GGUF format and properly mounted as Docker volumes.
For best performance, use a CUDA-capable GPU.
See the Dockerfile and source scripts for advanced configuration.