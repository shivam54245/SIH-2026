from fastapi import FastAPI
from typing import Optional

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.get("/greet/")
async def greetMe(name: Optional[str] = "User", age = 20) -> dict:
    return {"message": f"Hello {name}", "age": age}