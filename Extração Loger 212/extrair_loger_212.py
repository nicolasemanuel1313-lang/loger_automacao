from playwright.sync_api import sync_playwright
import pandas as pd
import time
from datetime import datetime, timedelta
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
                page.get_by_role("textbox", name="Acesso rápido").fill('212')
                page.get_by_role("button", name="search").click()
                # Aguarda o iframe da tela 212 carregar
                page.wait_for_selector("iframe", timeout=30000)
                print(f"✅ Centro {nomeCentro} selecionado com sucesso.")
            except Exception as e:
                print(f"❌ Erro na etapa de SELEÇÃO DO CENTRO {nomeCentro}: {e}")
                raise

            # ======================
            # SELEÇÃO DAS DATAS E CONSULTAR
            # ======================
            try:
                # Calcula as datas dinamicamente
                hoje = datetime.today()
                data_de = (hoje - timedelta(days=20)).strftime('%d/%m/%Y')
                data_ate = (hoje + timedelta(days=10)).strftime('%d/%m/%Y')

                # Localiza o iframe legacy e espera o campo de data
                frame = page.frame_locator("iframe").first
                frame.locator("#periodoDe").wait_for(timeout=30000)

                # Seta as datas via JavaScript dentro do iframe
                page.evaluate(f"""
                    var iframe = document.querySelector('iframe');
                    var doc = iframe.contentDocument || iframe.contentWindow.document;

                    var de = doc.getElementById('periodoDe');
                    var ate = doc.getElementById('periodoAte');

                    de.value = '{data_de}';
                    de.dispatchEvent(new Event('change', {{bubbles: true}}));
                    de.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    de.dispatchEvent(new Event('input', {{bubbles: true}}));

                    ate.value = '{data_ate}';
                    ate.dispatchEvent(new Event('change', {{bubbles: true}}));
                    ate.dispatchEvent(new Event('blur', {{bubbles: true}}));
                    ate.dispatchEvent(new Event('input', {{bubbles: true}}));
                """)

                # Aguarda os valores serem aplicados antes de clicar em Consultar
                frame.locator("#periodoDe").evaluate("el => el.value !== ''")

                # Clica no Consultar
                page.evaluate("""
                    var iframe = document.querySelector('iframe');
                    var doc = iframe.contentDocument || iframe.contentWindow.document;
                    doc.getElementById('btnConsultar').click();
                """)

                # Aguarda a tabela de resultados carregar com dados
                frame.locator("#monitoramentoAtendimentoAgendamentoCargaGrid tr.jqgrow").first.wait_for(timeout=60000)

                # Aguarda o loader sumir indicando processamento completo
                frame.locator('.loader-container').wait_for(state='hidden', timeout=60000)
                print(f"✅ Datas preenchidas ({data_de} até {data_ate}) e consulta iniciada.")

                # ======================
                # EXTRAÇÃO DA TABELA
                # ======================

                # Extrai todos os dados via API do jqGrid
                dados = page.evaluate("""
                    (function() {
                        var iframe = document.querySelector('iframe');
                        var win = iframe.contentWindow;

                        var grid = win.jQuery('#monitoramentoAtendimentoAgendamentoCargaGrid');
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
                    'centro':                    'Centro',
                    'transporte':                'Transporte',
                    'transportadora':            'Transportadora',
                    'placa':                     'Placa',
                    'motorista':                 'Motorista',
                    'status':                    'Status',
                    'tipoMaterial':              'Tipo Material',
                    'entradaprevista':           'Entrada Prevista',
                    'iniciocargaprevista':       'Início Carregamento Previsto',
                    'fimcargaprevista':          'Fim Carregamento Previsto',
                    'saidaprevista':             'Saída Prevista',
                    'tempocarregamentoprevisto': 'Carregamento Previsto',
                    'tempoprevisto':             'Permanência Prevista',
                    'metatpv':                   'Meta TPV',
                    'sequenciaagendada':         'Sequência Agendada',
                    'chegada':                   'Chegada',
                    'entradareal':               'Entrada Real',
                    'pesageminicial':            'Pesagem Inicial',
                    'iniciocargareal':           'Início Carregamento Real',
                    'fimcargareal':              'Fim Carregamento Real',
                    'saidareal':                 'Saída Real',
                    'tempocarregamento':         'Carregamento Real',
                    'tempoAmarracao':            'Amarração',
                    'temporeal':                 'Permanência Real',
                    'calcpermanencia':           'Perm. Prev X Real',
                    'farol':                     'Farol',
                    'tempodisponibilidade':      'Disponibilidade',
                    'aderenciaDisponibilidade':  'Aderência Disp.',
                    'qtdeAmarracao':             'Qnt Amarração',
                    'ocorrencias':               'Ocorrência',
                    'sequenciareal':             'Sequência Real',
                    'pesoprogramado':            'Peso Programado',
                    'pesoreal':                  'Peso Real',
                    'dedicado':                  'Dedicado',
                })

                # Dropar colunas adjacentes do jqGrid
                colunas_remover = [
                    'minutocarregamento', 'minutocarregamentoprevisto', 'minutoprevisto',
                    'minutoreal', 'minutocalcpermanencia', 'minutodisponibilidade',
                    'minutoAmarracao', 'valorpesoprogramado', 'valorpesoreal', 'Nome Centro'
                ]
                df = df.drop(columns=[c for c in colunas_remover if c in df.columns])

                print(f"✅ {len(df)} registros extraídos do centro {nomeCentro}.")
                print(df.head())

                return df

            except Exception as e:
                print(f"❌ Erro na etapa de SELEÇÃO DAS DATAS E CONSULTAR {nomeCentro}: {e}")
                raise

    except Exception as e:
        print(f"❌ Erro geral no centro {nomeCentro}: {e}")
        raise