import pandas as pd
from datetime import datetime
import time


def salvar_excel(df, pasta, pasta_capa):
    if df.empty:
        print("⚠️ DataFrame vazio, nada a salvar.")
        return

    # ======================
    # SALVAR HORA A HORA
    # ======================
    df_final = df

    try:
        agora = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        nome_arquivo = f"{agora}.xlsx"
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
        caminho_pasta_completo = f"{pasta_capa}\\Loger Cancelamentos.xlsx"
        df_final.to_excel(caminho_pasta_completo, index=False)
        print(f"✅ Capa atualizada com {len(df_final)} registros: {caminho_pasta_completo}")
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo de capa em: {caminho_pasta_completo}")
        print(f"   Detalhe: {e}")
        raise