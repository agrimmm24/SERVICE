from rocketry import Rocketry
from rocketry.conds import every
import httpx
import os
import asyncio
from datetime import datetime

# Initialize Rocketry
app = Rocketry(config={'task_execution': 'async'})

@app.task(every('14 minutes'))
async def keep_alive_ping():
    """
    Pings the server's own health endpoint to prevent Render from 
    spinning down the free tier instance.
    """
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        print(f"[{datetime.now()}] Keep-alive: RENDER_EXTERNAL_URL not set. Skipping ping.")
        return

    health_url = f"{url.rstrip('/')}/api/health"
    print(f"[{datetime.now()}] Keep-alive: Pinging {health_url}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(health_url, timeout=10.0)
            if response.status_code == 200:
                print(f"[{datetime.now()}] Keep-alive: Ping successful.")
            else:
                print(f"[{datetime.now()}] Keep-alive: Ping failed with status {response.status_code}.")
    except Exception as e:
        print(f"[{datetime.now()}] Keep-alive: Error during ping: {e}")

if __name__ == "__main__":
    app.run()
