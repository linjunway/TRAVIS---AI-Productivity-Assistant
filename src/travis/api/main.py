import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

app = FastAPI(title="travis")
llm = AsyncOpenAI(
    base_url=os.environ.get("LITELLM_BASE_URL", "http://localhost:4000"),
    api_key=os.environ["LITELLM_MASTER_KEY"],
)

RAW_MODELS = ("local-fast", "local-code", "cloud-nim", "cloud-openrouter", "cloud-review", "cloud-deepseek")
AGENT_MODEL = "travis-agent"   # selecting this in Open WebUI runs the loop


class ChatRequest(BaseModel):
    model: str = "local-fast"
    messages: list[dict]
    stream: bool = False
    temperature: float | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/v1/models")
async def models():
    ids = (*RAW_MODELS, AGENT_MODEL)
    return {"object": "list", "data": [{"id": m, "object": "model"} for m in ids]}


@app.post("/v1/chat/completions")
async def chat(req: ChatRequest):
    # Phase 3: the agent loop plugs in here, and only here.
    if req.model == AGENT_MODEL:
        raise HTTPException(501, "Agent loop not implemented yet (Phase 3)")

    # Pass-through for raw models
    kwargs = dict(model=req.model, messages=req.messages, temperature=req.temperature)
    if req.stream:
        stream = await llm.chat.completions.create(stream=True, **kwargs)

        async def gen():
            async for chunk in stream:
                yield f"data: {chunk.model_dump_json()}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")
    resp = await llm.chat.completions.create(**kwargs)
    return resp.model_dump()