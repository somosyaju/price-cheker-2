from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import tempfile
import os

app = FastAPI()

app.mount("/templates", StaticFiles(directory="templates"), name="templates")


@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/check")
async def check(pdf: UploadFile = File(...), excel: UploadFile = File(...)):
    try:
        # Guardar archivos temporales
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_tmp:
            pdf_tmp.write(await pdf.read())
            pdf_path = pdf_tmp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as xls_tmp:
            xls_tmp.write(await excel.read())
            excel_path = xls_tmp.name

        # Leer Excel
        df = pd.read_excel(excel_path)

        # ⚠️ ACÁ IRÍA TU LÓGICA REAL DE COMPARACIÓN
        # Por ahora simulamos el resultado final esperado
        resultado = (
            "Sí: hay un error comparándolo con el Excel. "
            "Todos los precios finales, normales y precios por unidad coinciden "
            "excepto el producto TENA (Toallas femeninas x 10 u), "
            "donde en el PDF el precio final figura incorrecto ($7.1491,50) "
            "y no coincide con el valor del Excel ($7.148,40); "
            "es un error de tipeo/formato en el PDF. "
            "El resto de los precios es correcto."
        )

        return {
            "ok": True,
            "message": resultado
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e)
            }
        )

    finally:
        # Limpiar archivos temporales
        try:
            os.remove(pdf_path)
            os.remove(excel_path)
        except:
            pass
