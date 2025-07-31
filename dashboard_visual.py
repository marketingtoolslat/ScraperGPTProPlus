import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import os

def load_and_visualize(file_path="resultados.csv"):
    if not os.path.exists(file_path):
        return "No hay datos aún", None, None, None

    df = pd.read_csv(file_path)

    # Gráfico de nichos
    fig1, ax1 = plt.subplots()
    df["nicho"].value_counts().plot(kind="bar", ax=ax1, title="Distribución por Nicho")
    ax1.set_ylabel("Cantidad")

    # Gráfico de estilos
    fig2, ax2 = plt.subplots()
    df["estilo"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax2, title="Estilo de Copy")
    ax2.set_ylabel("")

    # Gráfico de formatos
    fig3, ax3 = plt.subplots()
    df["formato"].value_counts().plot(kind="barh", ax=ax3, title="Tipos de Copy")

    return df, fig1, fig2, fig3

demo = gr.Interface(
    fn=load_and_visualize,
    inputs=[],
    outputs=[
        gr.Dataframe(label="Resultados"),
        gr.Plot(label="Gráfico por Nicho"),
        gr.Plot(label="Gráfico por Estilo"),
        gr.Plot(label="Gráfico por Formato")
    ],
    title="📊 ScraperGPT Pro++ Dashboard Visual",
    description="Visualización de resultados scrapeados con gráficas automáticas"
)

demo.launch(server_name="0.0.0.0", server_port=10000)
