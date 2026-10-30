from fastapi import FastAPI

app = FastAPI()

@app.get("/api")
async def getApi():
    return {"Hello": "World"}