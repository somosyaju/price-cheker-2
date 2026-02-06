from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import tempfile
import pandas as pd
import pdfplumber
import re
from unidecode import unidecode

app = FastAPI()
templates = Jinja2Templates(directory="templates")


def normalize(text):
    if not text:
        return ""
    text = unidecode(text.upper())
    text = re.sub(r"[-_]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/check")
async def check(pdf: UploadFile = File(...), excel: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False) as p:
        p.write(await pdf.read())
        pdf_path = p.name

    with tempfile.NamedTemporaryFile(delete=False) as e:
        e.write(await excel.read())
        excel_path = e.name

    # Excel
    df = pd.read_excel(excel_path)
    excel_data = {
        normalize(r["producto"]): {
            "precio_final": float(r["precio_final"])
        }
        for _, r in df.iterrows()
    }

    # PDF
    pdf_data = {}
    with pdfplumber.open(pdf_path) as pdf_file:
        text = "\n".join(page.extract_text() or "" for page in pdf_file.pages)

    blocks = re.split(r"\n(?=[A-Z]{3,})", text)

    for b in blocks:
        m = re.search(r"(.+?)\n.*?Precio final\s*\$ ?([\d\.,]+)", b, re.S)
        if not m:
            continue
        name = normalize(m.group(1))
        price = float(m.group(2).replace(".", "").replace(",", "."))
        pdf_data[name] = price

    # Comparación
    for name, price in pdf_data.items():
        if name in excel_data:
            if round(price, 2) != round(excel_data[name]["precio_final"], 2):
                return {
                    "resultado": (
                        f"Sí: hay un error comparándolo con el Excel. "
                        f"El producto {name} tiene precio PDF ${price} "
                        f"y Excel ${excel_data[name]['precio_final']}."
                    )
                }

    return {
        "resultado": "No: no hay errores de precio comparándolo con el Excel."
    }
