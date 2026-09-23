from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Halisi backend is alive"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

