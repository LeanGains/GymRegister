from fastapi import FastAPI

app = FastAPI(title="GymRegister API")

@app.get("/")
def read_root():
    return {"message": "GymRegister API"}