from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

def extrair_loger_27(nomeCentro):
    url = os.getenv("URL_LOGER")
    user = os.getenv("LOGER_USER")
    password = os.getenv("LOGER_PASSWORD")

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False, channel='chrome')
            context = browser.new_context()
            page = context.new_page()

            # ======================
            # LOGIN
            # ======================
            try:
                page.goto(url)
                page.get_by_role("button", name="ACEITO").click()
                page.get_by_role("textbox", name="Usuário").fill(user)
                page.get_by_role("textbox", name="Senha").fill(password)
                page.get_by_role("button", name="Entrar").click()
                # Aguarda a tela de seleção de centro carregar
                page.get_by_role("textbox", name="Buscar por centro").wait_for(timeout=30000)
                print(f"✅ Login realizado com sucesso.")
            except Exception as e:
                print(f"❌ Erro na etapa de LOGIN: {e}")
                raise

            # ======================
            # SELEÇÃO DO CENTRO
            # ======================
            try:
                page.get_by_role("textbox", name="Buscar por centro").fill(nomeCentro)
                page.get_by_role("button", name=" Pesquisar").click()
                page.get_by_role("gridcell", name=nomeCentro).first.dblclick()
                # Aguarda o botão de Agendamento aparecer após selecionar o centro
                page.get_by_role("button", name="Agendamento De Carga").wait_for(timeout=30000)
                page.get_by_role("button", name="Agendamento De Carga").click()
                page.get_by_role("textbox", name="Acesso rápido").fill('27')
                page.get_by_role("button", name="search").click()
                # Aguarda o campo dataInicio carregar na página principal (tela 27 não usa iframe)
                page.locator("#dataInicio").wait_for(timeout=30000)
                print(f"✅ Centro {nomeCentro} selecionado com sucesso.")
            except Exception as e:
                print(f"❌ Erro ao aguardar tela 27 carregar {nomeCentro}: {e}")
                raise

            # ======================
            # EXTRAÇÃO VIA API COM COOKIES DE SESSÃO
            # ======================
            try:
                # Calcula as datas dinamicamente
                hoje = datetime.today()
                data_inicio = datetime(hoje.year, 1, 1).strftime('%Y-%m-%d')
                data_fim = hoje.strftime('%Y-%m-%d')

                print(f"📅 Período: {data_inicio} até {data_fim}")

                # Faz a requisição direta à API dentro do contexto do browser
                # usando fetch() com os cookies de sessão já autenticados
                dados = page.evaluate(f"""
                    async function() {{
                        const response = await fetch(
                            'https://loger.arcelormittal.com.br/loger.core/consulta/controlecancelamentoagendamento/pesquisar',
                            {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json'
                                }},
                                body: JSON.stringify({{
                                    dataInicio: '{data_inicio}',
                                    dataFim: '{data_fim}',
                                    pagingConfig: {{ page: 1, rows: 99999 }}
                                }})
                            }}
                        );
                        const json = await response.json();
                        return json.list;
                    }}
                """)

                if not dados:
                    raise ValueError("A API retornou lista vazia.")

                df = pd.DataFrame(dados)

                # Renomeia as colunas
                df = df.rename(columns={
                    'numeroTransporte':              'Transporte',
                    'transportadoraCodigo':          'Cód. Transportadora',
                    'transportadoraNome':            'Transportadora',
                    'dataHoraPlanejadaTransporte':   'Data Planejada',
                    'dataHoraAgendamento':           'Momento do Agendamento',
                    'dataHoraDesejadaAgendamento':   'Data Desejada',
                    'dataHoraRealizacaoAgendamento': 'Agendamento',
                    'dataHoraCancelamento':          'Cancelamento',
                    'codigoUsuarioCancelamento':     'Usuário',
                    'expedicao':                     'Expedição',
                    'motivo':                        'Motivo',
                    'observacao':                    'Observação',
                    'pesoAgendado':                  'Peso Agendado',
                })

                # Remove coluna de ID interno não necessária
                colunas_remover = ['transportadoraId']
                df = df.drop(columns=[c for c in colunas_remover if c in df.columns])

                print(f"✅ {len(df)} registros extraídos do centro {nomeCentro}.")
                print(df.head())

                return df

            except Exception as e:
                print(f"❌ Erro na etapa de EXTRAÇÃO {nomeCentro}: {e}")
                raise

    except Exception as e:
        print(f"❌ Erro geral no centro {nomeCentro}: {e}")
        raise