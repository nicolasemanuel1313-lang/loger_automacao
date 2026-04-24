from playwright.sync_api import sync_playwright
import pandas as pd
import time
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

def extrair_base_loger(nomeCentro):
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
                page.get_by_role("textbox", name="Acesso rápido").fill('29')
                page.get_by_role("button", name="search").click()
                # Aguarda o iframe carregar
                page.wait_for_selector("iframe", timeout=30000)
                print(f"✅ Centro {nomeCentro} selecionado com sucesso.")
            except Exception as e:
                print(f"❌ Erro na etapa de SELEÇÃO DO CENTRO {nomeCentro}: {e}")
                raise

            # ======================
            # CLICAR EM CONSULTAR
            # ======================
            try:
                frame = page.frame_locator("iframe").first
                frame.locator("#btnConsultar").wait_for(timeout=30000)

                # Clica no Consultar via JavaScript dentro do iframe
                page.evaluate("""
                    var iframe = document.querySelector('iframe');
                    var doc = iframe.contentDocument || iframe.contentWindow.document;
                    doc.getElementById('btnConsultar').click();
                """)
                print(f"✅ Botão Consultar clicado com sucesso.")
            except Exception as e:
                print(f"❌ Erro na etapa de CLICAR EM CONSULTAR: {e}")
                raise

            # ======================
            # CAPTURAR TRANSPORTES
            # ======================
            try:
                # Aguarda as linhas de resultado aparecerem
                try:
                    frame.locator('#filaTransporteDisponibilidadeImediataGrid tr.jqgrow').first.wait_for(timeout=15000)
                except Exception:
                    print(f"⚠️ Centro {nomeCentro}: tabela vazia, nenhum transporte na fila.")
                    browser.close()
                    return pd.DataFrame()

                # Extrai todos os dados via API do jqGrid
                dados = page.evaluate("""
                    (function() {
                        var iframe = document.querySelector('iframe');
                        var win = iframe.contentWindow;

                        var grid = win.jQuery('#filaTransporteDisponibilidadeImediataGrid');
                        var ids = grid.jqGrid('getDataIDs');

                        var resultado = [];
                        ids.forEach(function(id) {
                            resultado.push(grid.jqGrid('getRowData', id));
                        });

                        return resultado;
                    })();
                """)

                df = pd.DataFrame(dados)

                # Renomeia as colunas
                df = df.rename(columns={
                    'transporte':           'Transporte',
                    'transportadora':       'Transportadora',
                    'placa':                'Placa',
                    'tipoMercado':          'Tipo Mercado',
                    'dataAgendamento':      'Data Agendamento',
                    'dataDisponibilidade':  'Data Disponibilidade',
                    'sequencia':            'Sequencia',
                    'liberacaoPrevia':      'Liberação Prévia',
                    'liberacaoAutomatica':  'Liberação Automática',
                    'dedicado':             'Dedicado',
                })

                # Dropar colunas adjacentes do jqGrid
                colunas_remover = [
                    'id','dataLiberacaoPrevia'
                ]
                df = df.drop(columns=[c for c in colunas_remover if c in df.columns])

                print(f"✅ {len(df)} registros capturados!")
                browser.close()
                return df

            except Exception as e:
                print(f"❌ Erro na etapa de CAPTURAR DADOS DA TABELA: {e}")
                raise

    except Exception as e:
        print(f"❌ Erro geral no centro {nomeCentro}: {e}")
        raise