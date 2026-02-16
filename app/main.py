from fastapi import FastAPI
from app.api.routes.summarize import router as summarize_router



app = FastAPI()
app.include_router(summarize_router)

@app.get("/")
def health():
    return {"status": "ok"}