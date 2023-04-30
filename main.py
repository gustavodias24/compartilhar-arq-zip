from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/zipagem", response_class=HTMLResponse)
async def zipagem(request: Request, nome_zip: str = "semNome"):
    return templates.TemplateResponse("resultado.html", {"request": request, "nome": nome_zip.replace(" ", "")})
