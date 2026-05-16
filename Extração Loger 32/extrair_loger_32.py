from playwright.sync_api import sync_playwright
import pandas as pd
import os
import io
import tempfile
from datetime import datetime
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

def extrair_base_loger(nomeCentro):
    url = os.getenv("URL_LOGER")
    user = os.getenv("LOGER_USER")
    password = os.getenv("LOGER_PASSWORD")

    # Período: do dia 1 do mês atual até hoje
    hoje = datetime.today()
    data_ini = hoje.replace(day=1).strftime("%d/%m/%Y")
    data_fim = hoje.strftime("%d/%m/%Y")

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
            page.get_by_role("button", name="Agendamento De Carga").wait_for(timeout=30000)
            page.get_by_role("button", name="Agendamento De Carga").click()
            page.get_by_role("textbox", name="Acesso rápido").fill('32')
            page.get_by_role("button", name="search").click()
            page.wait_for_selector("iframe", timeout=30000)
            print(f"✅ Centro {nomeCentro} selecionado com sucesso.")
        except Exception as e:
            print(f"❌ Erro na etapa de SELEÇÃO DO CENTRO {nomeCentro}: {e}")
            raise

        # ======================
        # PREENCHIMENTO DOS FILTROS
        # ======================
        try:
            # Polling: aguarda o frame correto carregar com o elemento #filtroDataIni
            frame_tela = None
            for _ in range(30):  # tenta por até 15 segundos (30x 500ms)
                for f in page.frames:
                    if "relatorioDadosTransporte" in f.url and "centro=" in f.url:
                        try:
                            el = f.query_selector("#filtroDataIni")
                            if el:
                                frame_tela = f
                                break
                        except:
                            pass
                if frame_tela:
                    break
                page.wait_for_timeout(500)

            if not frame_tela:
                raise Exception("Frame com #filtroDataIni não encontrado após 15 segundos.")

            print(f"✅ Frame encontrado: {frame_tela.url}")

            # Preencher Data Inicial via JS (jQuery UI Datepicker)
            frame_tela.evaluate(f"""
                var el = document.getElementById('filtroDataIni');
                el.value = '{data_ini}';
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            """)

            # Preencher Data Final via JS
            frame_tela.evaluate(f"""
                var el = document.getElementById('filtroDataFim');
                el.value = '{data_fim}';
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
            """)

            print(f"✅ Datas preenchidas: {data_ini} a {data_fim}")

            # Marcar todos os grupos de checkboxes via JS
            for checkbox_id in ['dadosGerais', 'previsto', 'real', 'indicadores']:
                frame_tela.evaluate(f"""
                    var el = document.getElementById('{checkbox_id}');
                    if (!el.checked) {{
                        el.click();
                    }}
                """)

            print("✅ Checkboxes selecionadas.")

        except Exception as e:
            print(f"❌ Erro na etapa de PREENCHIMENTO DOS FILTROS: {e}")
            raise

        # ======================
        # DOWNLOAD E PROCESSAMENTO
        # ======================
        try:
            with page.expect_download(timeout=60000) as download_info:
                frame_tela.evaluate("""
                    document.getElementById('btnExcel').click();
                """)

            download = download_info.value

            # Salva em arquivo temporário, lê com pandas e remove em seguida
            tmp_path = os.path.join(tempfile.gettempdir(), f"loger_32_{nomeCentro}.xlsx")
            download.save_as(tmp_path)

            df = pd.read_excel(tmp_path,engine='xlrd')
            os.remove(tmp_path)

            print(f"✅ Dados carregados: {len(df)} linhas, {len(df.columns)} colunas")
            return df

        except Exception as e:
            print(f"❌ Erro na etapa de DOWNLOAD/PROCESSAMENTO: {e}")
            raise