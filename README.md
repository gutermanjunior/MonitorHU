# 🏥 HU-USP Monitor – Especialidades

Sistema pessoal de monitoramento das especialidades do Hospital Universitário da USP.

---

## 🎯 Objetivo

- 🔎 Detectar alterações na lista de especialidades  
- 📈 Registrar histórico estruturado das mudanças  
- 🔔 Notificar quando especialidades forem adicionadas ou removidas  
- 🛡️ Garantir funcionamento contínuo via Guardian  

---

## 🚀 Execução

### ▶ Monitor

```bash
python monitor.py
```

O monitor:

- Executa verificações periódicas com intervalo adaptativo
- Detecta diferenças entre snapshots
- Registra apenas mudanças
- Atualiza heartbeat para o Guardian
- Exibe dashboard em CLI

---

### 🛡️ Guardian (Watchdog)

```bash
python guardian.py
```

O Guardian:

- Monitora o arquivo `heartbeat.json`
- Detecta erros persistentes
- Evita spam (rate limit configurável)
- Pode enviar alertas via Telegram

---

## 🔐 Autenticação com Selenium + CAPTCHA Manual

O sistema utiliza Selenium para autenticação no site do HU.

Fluxo:

1. Primeira execução abre o navegador.
2. Usuário resolve o CAPTCHA manualmente.
3. Cookies são salvos em `data/hu_cookies.pkl`.
4. Execuções futuras tentam restaurar sessão automaticamente.
5. Se a sessão expirar, será solicitado novo login manual.

---

## ⏱️ Intervalo Adaptativo

Configurado em `config.yaml`:

```yaml
intervals:
  day:
    start: 8
    end: 18
    minutes: 15
  evening:
    start: 18
    end: 24
    minutes: 30
  night:
    start: 0
    end: 8
    minutes: 60
```

---

## 🔐 Configuração Segura (.env)

Crie um arquivo `.env` na raiz do projeto:

```
HU_USER=...
HU_DATA=...

EMAIL_CONTA=...
EMAIL_SENHA=...
EMAIL_DESTINO=...

TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
```

Instale:

```bash
pip install python-dotenv selenium webdriver-manager
```

Nunca versionar `.env`.

Adicionar ao `.gitignore`:

```
.env
data/
logs/
```

---

## 📊 Histórico de Dados

### 📁 last_snapshot.json

Armazena o estado atual da lista de especialidades.

### 📄 history.csv

Registra apenas mudanças detectadas:

```
timestamp,machine_id,action,especialidade
2026-02-17T14:03:00,windows-main,added,Cardiologia
2026-02-18T09:21:00,macbook,removed,Nefrologia
```

---

## 🖥️ Interface CLI

Exemplo de saída:

```
╔════════════════════════════════════╗
║  MONITOR HU-USP – Especialidades  ║
╠════════════════════════════════════╣
║ Última verificação: 17/02 21:03    ║
║ Status: ✅ Conectado               ║
╠════════════════════════════════════╣
║ Mudanças detectadas                ║
║ + Cardiologia                      ║
║ - Nefrologia                       ║
╚════════════════════════════════════╝
```

---

## 🛠️ Arquitetura

- `monitor.py` → Orquestrador principal  
- `guardian.py` → Watchdog externo  
- `parser.py` → Autenticação + scraping (Selenium)  
- `scheduler.py` → Intervalo adaptativo  
- `state.py` → Snapshot + heartbeat  
- `notifier.py` → Registro CSV + notificações  
- `config.yaml` → Configuração estrutural  
- `.env` → Credenciais  

Separação clara entre:

- Configuração  
- Segredos  
- Estado  
- Persistência  
- Lógica  

---

## ⚠️ Aviso Legal

Ferramenta desenvolvida para uso pessoal e educacional.

- Não utilize intervalos agressivos  
- Não sobrecarregue serviços públicos  
- Respeite as políticas de uso  

O autor não se responsabiliza por uso indevido.
