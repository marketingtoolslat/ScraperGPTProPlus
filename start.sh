#!/bin/bash
echo "Instalando navegador headless con Playwright..."
python -m playwright install chromium
echo "Ejecutando interfaz Gradio con ScraperGPT Pro++..."
python3 dashboard_gradio.py
