import gradio as gr
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# === Configuración de Google Sheets ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_NAME = "ScraperGPT_Resultados"

def connect_to_sheets():
    creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_credentials.json", SCOPE)
    client = gspread.authorize(creds)
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except:
        sheet = client.create(SHEET_NAME).sheet1
    return sheet

sheet = None
try:
    sheet = connect_to_sheets()
except Exception as e:
    print("Google Sheets desactivado:", e)

# === Funciones de inferencia ===
def infer_nicho(text):
    text = text.lower()
    if any(k in text for k in ["copywriter", "copywriting", "persuasão", "vendas"]):
        return "Copywriting"
    elif any(k in text for k in ["tráfego", "ads", "facebook ads", "google ads"]):
        return "Tráfego Pago"
    elif any(k in text for k in ["mentoria", "lançamento", "curso", "aula"]):
        return "Infoproductos / Educación"
    elif any(k in text for k in ["emagrecer", "peso", "nutrição", "corpo"]):
        return "Salud / Fitness"
    elif any(k in text for k in ["espiritualidad", "energía", "meditación"]):
        return "Espiritualidad / Desarrollo personal"
    else:
        return "Otro"

def infer_estilo(text):
    text = text.lower()
    if any(w in text for w in ["tú", "sientes", "transformación", "sueño", "miedo", "deseo"]):
        return "Emocional"
    elif any(w in text for w in ["resultado", "método", "estrategia", "prueba", "hecho"]):
        return "Racional"
    else:
        return "Mixto"

def infer_formato(text):
    length = len(text)
    if length > 400:
        return "Copy Largo"
    elif length < 100:
        return "Copy Corto"
    else:
        return "Copy Medio"

# === Scraper principal ===
def scrape_facebook_ad(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "es-ES,es;q=0.9"
            })
            page.goto(url, timeout=60000)
            page.wait_for_timeout(3000)
            page.mouse.wheel(0, 2000)
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text(separator=" ").lower()
        title = soup.title.string.strip() if soup.title else "Sin título"

        cta = "saiba mais" if "saiba mais" in text else "Otro"
        fecha = re.findall(r"(\d{1,2} de .*? de \d{4})", text)
        idioma = "Portugués" if "brasil" in text else "Desconocido"
        pais = "Brasil" if "brasil" in text else "Otro"
        total_ads = text.count("impressões")

        if total_ads < 3:
            return None  # filtrar si hay menos de 3

        data = {
            "titulo": title,
            "cta": cta,
            "fecha": fecha[0] if fecha else "Desconocida",
            "idioma": idioma,
            "pais": pais,
            "nicho": infer_nicho(text),
            "estilo": infer_estilo(text),
            "formato": infer_formato(text),
            "anuncios_activos": total_ads,
            "texto_visible": text[:1000]
        }

        # Exportar a CSV
        with open("resultados.csv", "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data.keys())
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(data)

        # Exportar a Google Sheets
        if sheet:
            sheet.append_row(list(data.values()))

        return list(data.values())
    except Exception as e:
        return [f"Error: {e}"] + [""] * 9

# === Interfaz Gradio ===
def batch_scrape(input_text):
    urls = [line.strip() for line in input_text.strip().split("\n") if line.strip()]
    results = []
    for url in urls:
        if url.isdigit():
            url = f"https://www.facebook.com/ads/library/?id={url}"
        result = scrape_facebook_ad(url)
        if result:
            results.append(result)
    return results

demo = gr.Interface(
    fn=batch_scrape,
    inputs=gr.Textbox(label="Pega uno o varios IDs o URLs (uno por línea)", lines=10, placeholder="Ej:
673902409146272"),
    outputs=gr.Dataframe(headers=[
        "Título", "CTA", "Fecha", "Idioma", "País", "Nicho/Subnicho",
        "Estilo", "Formato", "# Anuncios Activos", "Texto Visible (recorte)"
    ]),
    title="ScraperGPT Pro++ - Gradio Batch",
    description="Analiza múltiples anuncios de Facebook Ads por ID o URL. Exporta a CSV y Google Sheets automáticamente."
)

demo.launch(server_name="0.0.0.0", server_port=10000)
