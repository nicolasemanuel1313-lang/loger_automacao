import pandas as pd
from datetime import datetime
import time


def salvar_excel(df, pasta, pasta_capa):
    if df.empty:
        print("⚠️ DataFrame vazio, nada a salvar.")
        return

    # ======================
    # FILTRO TIPO MERCADO
    # ======================
    try:
        tipos_validos = ["Interno", "Interno/Transferência"]
        df_filtrado = df[df["Tipo Mercado"].isin(tipos_validos)]
        df_final = df_filtrado

        if df_final.empty:
            print("⚠️ Nenhum registro após aplicar filtro de Tipo Mercado.")
            return

        print(f"✅ Filtro aplicado: {len(df_final)} registros válidos.")
    except Exception as e:
        print(f"❌ Erro ao aplicar filtro de Tipo Mercado: {e}")
        raise

    # ======================
    # SALVAR HORA A HORA
    # ======================
    try:
        agora = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        nome_arquivo = f"Loger_Previas_{agora}.xlsx"
        caminho_completo = f"{pasta}\\{nome_arquivo}"

        df_final.to_excel(caminho_completo, index=False)
        print(f"\n✅ Arquivo salvo com {len(df_final)} registros: {caminho_completo}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo hora a hora em: {caminho_completo}")
        print(f"   Detalhe: {e}")
        raise

    # ======================
    # SALVAR ULTIMO ATUALIZADO
    # ======================
    try:
        caminho_pasta_completo = f"{pasta_capa}\\Loger Previas.xlsx"

        df_final.to_excel(caminho_pasta_completo, index=False)
        print(f"✅ Capa atualizada com {len(df_final)} registros: {caminho_pasta_completo}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo de capa em: {caminho_pasta_completo}")
        print(f"   Detalhe: {e}")
        raise