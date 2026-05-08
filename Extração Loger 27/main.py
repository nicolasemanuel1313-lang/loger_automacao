import pandas as pd
import json
from dotenv import load_dotenv
import os

from extrair_loger_27 import extrair_loger_27
from salvar_excel import salvar_excel

# Carrega as variáveis do arquivo .env
load_dotenv()

centros = json.loads(os.getenv("LOGER_CENTROS_27", "{}"))

PASTA_DESTINO = os.getenv("PASTA_DESTINO_27")
PASTA_CAPA = os.getenv("PASTA_CAPA_27")


def main():
    dfs = []

    for cod, nome in centros.items():
        print(f"\n{'='*50}")
        print(f"🔄 Extraindo centro: {cod} - {nome}")
        print(f"{'='*50}")
        try:
            df = extrair_loger_27(cod)
            if not df.empty:
                df['Centro'] = cod
                df['Nome Centro'] = nome
                dfs.append(df)
                print(f"✅ {cod} - {nome}: {len(df)} registros capturados!")
        except Exception as e:
            print(f"❌ Erro no centro {cod} - {nome}: {e}")
            
            raise # interrompe — não gera df parcial
    
    # só executa se TODOS os centros foram processados com sucesso
    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        salvar_excel(df_final, PASTA_DESTINO,PASTA_CAPA)
    else:
        print("\n⚠️ Nenhum dado capturado em nenhum centro!")


if __name__ == '__main__':
    main()