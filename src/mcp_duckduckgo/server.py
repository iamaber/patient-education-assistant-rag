from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from bs4 import BeautifulSoup

app = FastAPI(title="DuckDuckGo-Medexbd MCP")


class CallRequest(BaseModel):
    tool: str
    arguments: dict


@app.post("/tools/call")
async def tools_call(req: CallRequest):
    if req.tool != "search":
        raise HTTPException(400, "Only tool 'search' is supported")

    drug = req.arguments.get("q", "").replace("Medexbd ", "").strip()
    if not drug:
        raise HTTPException(400, "Missing drug name")

    url = f"https://html.duckduckgo.com/html/?q=Medexbd+{drug.replace(' ', '+')}"
    async with httpx.AsyncClient(
        timeout=10, headers={"User-Agent": "Mozilla/5.0"}
    ) as client:
        r = await client.get(url)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    snippets = [
        {"text": res.text.strip(), "url": res.a["href"]}
        for res in soup.select(".result")
    ][:5]  # top-5 hits

    # Flatten to MCP-style JSON
    return {
        "content": [
            {"type": "text", "text": f"{s['text']}\nSource: {s['url']}"}
            for s in snippets
        ]
    }
