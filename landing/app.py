from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

app = FastAPI()

@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)