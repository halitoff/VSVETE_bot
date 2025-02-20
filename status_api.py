from fastapi import FastAPI
import json

app = FastAPI()

# Читаем статус бота из файла
def get_status():
    try:
        with open("bot_status.json", "r") as f:
            return json.load(f)
    except:
        return {"status": "⚠️ Нет данных"}

@app.get("/status")
def status():
    return get_status()

if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
