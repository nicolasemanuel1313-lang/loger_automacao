# 🚛 Loger Automação

Automação de extração de dados do sistema **Loger** (Agendamento de Carga) via web scraping com Playwright. O projeto realiza login automático, navega pelas telas do sistema, extrai os dados das grades de transporte e salva os resultados em arquivos Excel — tanto um histórico timestampado quanto um arquivo de capa sempre atualizado com o último snapshot.

---

## 📁 Estrutura do Projeto

```
loger_automacao/
├── Extração Loger 212/          # Tela 212 — Monitoramento de Agendamento de Carga
│   ├── extrair_loger_212.py     # Scraping e extração via jqGrid
│   ├── salvar_excel.py          # Persistência dos dados extraídos
│   └── main.py                  # Orquestrador — itera sobre os centros configurados
│
├── Extração Loger 29/           # Tela 29 — Fila de Transportes (Disponibilidade Imediata)
│   ├── extrair_loger_29.py      # Scraping e extração via jqGrid
│   ├── salvar_excel.py          # Persistência com filtro de Tipo Mercado
│   └── main.py                  # Orquestrador — itera sobre os centros configurados
│
├── .env.example                 # Modelo de variáveis de ambiente
└── .gitignore
```

---

## ⚙️ Funcionalidades

### Extração Loger 212 — Agendamento de Carga
- Acessa a tela **212** do Loger (Monitoramento de Atendimento de Agendamento de Carga)
- Preenche o período de consulta dinamicamente: **D-20 até D+10**
- Extrai todos os registros da grade jqGrid com campos como Transportadora, Status, Motorista, Placa, tempos previstos vs. reais, Farol, Ocorrências, Pesos etc.
- Suporta múltiplos centros em sequência (configurados via `.env`)
- Só salva o arquivo consolidado se **todos os centros** forem extraídos com sucesso

### Extração Loger 29 — Fila de Disponibilidade Imediata
- Acessa a tela **29** do Loger (Fila de Transporte — Disponibilidade Imediata)
- Extrai transportes com campos como Data Agendamento, Data Disponibilidade, Liberação Prévia/Automática, Dedicado etc.
- Aplica filtro automático por **Tipo Mercado** (`Interno` e `Interno/Transferência`)
- Lida graciosamente com centros sem registros na fila (retorna DataFrame vazio sem interromper o fluxo)

### Persistência de Dados (ambos os módulos)
Cada módulo salva os dados em dois destinos:

| Arquivo | Caminho | Propósito |
|---|---|---|
| `DD-MM-YYYY HH-MM-SS.xlsx` | `PASTA_DESTINO` | Histórico timestampado hora a hora |
| `Loger Agendamento Carga.xlsx` / `Loger Previas.xlsx` | `PASTA_CAPA` | Arquivo de capa — sempre sobrescrito com o dado mais recente |

---

## 🔧 Configuração

Copie `.env.example` para `.env` e preencha as variáveis:

```env
# Credenciais do Loger
LOGER_USER=seu_usuario
LOGER_PASSWORD=sua_senha
URL_LOGER=https://url-do-loger

# Centros a processar (JSON: {"COD": "Nome"})
LOGER_CENTROS_29={"1234": "Centro A", "5678": "Centro B"}
LOGER_CENTROS_212={"1234": "Centro A", "5678": "Centro B"}

# Pastas de destino (caminhos Windows)
PASTA_DESTINO=C:\Caminho\Para\Historico
PASTA_CAPA=C:\Caminho\Para\Capa
```

---

## 📦 Dependências

```bash
pip install playwright pandas python-dotenv openpyxl
playwright install chromium
```

---

## ▶️ Execução

Cada módulo é executado de forma independente a partir de sua própria pasta:

```bash
# Extração da tela 212
cd "Extração Loger 212"
python main.py

# Extração da tela 29
cd "Extração Loger 29"
python main.py
```

---