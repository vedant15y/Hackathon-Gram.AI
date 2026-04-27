import uvicorn

import server_fastapi


if __name__ == "__main__":
    uvicorn.run(server_fastapi.app, host="127.0.0.1", port=8000, log_level="info")
