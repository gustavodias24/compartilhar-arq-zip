import base64

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from typing import List

import bson

from bson.objectid import ObjectId
from io import BytesIO

from zipfile import ZipFile, ZIP_DEFLATED

from decouple import config
from pymongo import MongoClient

import qrcode

# Configurar client mongo
client = MongoClient(
    "mongodb+srv://{}:{}@clusterurls.wwd3kag.mongodb.net/?retryWrites=true&w=majority".format(
        config("USER"),
        config("PASS")
    )
)

# Instância do banco de dados
db = client["zipagensdb"]
col = db["qrcodes"]

app = FastAPI()

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/download/{id_arq}")
async def get_arquivo(id_arq: str):
    dados = col.find_one({"_id": id_arq})
    if dados:
        stream = BytesIO(dados.get("zip"))

        # Crie uma resposta de streaming com o fluxo de bytes e o tipo MIME apropriado
        headers = {
            "Content-Disposition": "attachment; filename={}.zip".format(dados.get("filename"))
        }

        return StreamingResponse(stream, headers=headers, media_type="application/zip")
    else:
        raise HTTPException(status_code=404, detail="Arquivos não encontrados!")


@app.post("/zipagem", response_class=HTMLResponse)
async def zipagem(request: Request, nome_zip: str = Form(...), arquivos: List[UploadFile] = File(...)):

    # Salva os arquivos em um zip
    buffer_zip = BytesIO()
    with ZipFile(buffer_zip, 'w', ZIP_DEFLATED) as file:
        for arq in arquivos:
            file.writestr(arq.filename, arq.file.read())

    buffer_zip.getvalue()

    id_aleatorio = str(ObjectId())


    # Geral o qr_code
    url = "https://www.{}/download/{}".format(request.url.hostname, id_aleatorio)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    img_qr = qr.make_image(fill_color="black", back_color="white")

    with BytesIO() as output:
        img_qr.save(output)
        qr_img_bytes = output.getvalue()

    # Salvar no banco de dados

    obj_salvar = bson.encode({
        "_id": id_aleatorio,
        "url": url,
        "zip": buffer_zip.getvalue(),
        "qr_code": qr_img_bytes,
        "filename": nome_zip
    })

    col.insert_one(bson.decode(obj_salvar))

    return templates.TemplateResponse(
        "resultado.html",
        {"request": request,
         "nome": nome_zip.replace(" ", ""),
         "url": url,
         "qr_code": base64.b64encode(qr_img_bytes).decode()
         }
    )
