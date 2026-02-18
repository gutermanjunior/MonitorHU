# 🏥 Monitor HU-USP (v2) – Especialidades

Status: ✅ Estável (Modular & Resiliente)  
Sistema de automação e monitoramento para detectar disponibilidade de vagas de especialidades médicas no Hospital Universitário da USP.  
Esta versão (v2) foi reescrita para ser modular, resiliente a falhas e rodar como um serviço contínuo.

---

## 🎯 Objetivo

- 🔎 Detectar disponibilidade/alterações nas especialidades
- 📈 Registrar histórico estruturado das mudanças
- 🔔 Notificar quando novas vagas surgirem (ex.: Telegram)
- 🛡️ Garantir funcionamento contínuo via Guardian (watchdog)

---

## ✨ Funcionalidades

### 🧠 Inteligência & Automação

- Arquitetura modular: código separado em serviços (`parser`, `notifier`, `state`, etc.) para fácil manutenção.
- 🛡️ Guardian (Watchdog): processo sentinela que monitora o bot principal; se o monitor travar ou cair, o Guardian reinicia automaticamente.
- Persistência de sessão: salva cookies para evitar logins manuais repetitivos.
- ⏱️ Intervalos adaptativos: configuração via `config.yaml` para definir frequências diferentes (dia, noite, madrugada).

---

### 📱 Interface & Notificações

- Dashboard CLI: painel visual no terminal com status, últimas vagas e histórico recente.
- Telegram formatado: envia alertas com negrito e ícones quando novas vagas surgem.
- Histórico local: mantém registro de alterações na pasta `data/`.

---

## 📂 Estrutura do Projeto

```bash
MonitorHU/
│
├── monitor_hu/           # Código Fonte (Pacote)
│   ├── monitor.py        # Lógica principal e Dashboard
│   ├── parser.py         # Automação do Browser (Selenium)
│   ├── guardian.py       # Sentinela (Reinicia em caso de crash)
│   ├── notifier.py       # Envio de mensagens (Telegram)
│   ├── scheduler.py      # Gerenciador de intervalos de tempo
│   └── state.py          # Gestão de estado e snapshots
│
├── data/                 # Dados gerados (Cookies, Logs, JSONs)
├── config.yaml           # Configuração de horários
├── .env                  # Credenciais (Não versionado)
└── requirements.txt      # Dependências
```

---

## 🛠️ Instalação

Clone o repositório e entre na pasta:

```bash
git clone https://github.com/seu-usuario/MonitorHU.git
cd MonitorHU
```

Crie e ative o ambiente virtual:

- Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

- Linux/Mac:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração

### 1) Credenciais (`.env`)

Crie um arquivo `.env` na raiz do projeto com seus dados:

```bash
# Acesso HU
HU_USER=seu_numero_usp
HU_DATA=dd/mm/aaaa

# Telegram (Opcional, mas recomendado)
TELEGRAM_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id

# Identificação da Máquina (Opcional)
MACHINE_ID=meu_pc_casa
```

Nunca versionar `.env`. Adicione ao `.gitignore`:

```bash
.env
data/
logs/
```

---

### 2) Intervalos (`config.yaml`)

O arquivo `config.yaml` define a frequência de verificação (em minutos) por período do dia:

```yaml
intervals:
  day:
    start: 8
    end: 18
    minutes: 15   # Verifica a cada 15 min durante o dia
  evening:
    start: 18
    end: 24
    minutes: 30   # A cada 30 min à noite
  night:
    start: 0
    end: 8
    minutes: 60   # A cada 1h na madrugada
```

---

## 🚀 Execução

Existem duas formas de rodar o sistema, sempre a partir da raiz `MonitorHU/`.

### 🛡️ Opção 1: Modo Blindado (Recomendado)

Roda o Guardian, que gerencia o monitor. Se der erro, ele reinicia o processo.

```bash
python -m monitor_hu.guardian
```

---

### ▶️ Opção 2: Modo Direto (Para Testes)

Roda apenas o monitor. Se der erro, o programa fecha.

```bash
python -m monitor_hu.monitor
```

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

## 🖥️ Dashboard CLI

Ao rodar, você verá uma interface como esta no terminal:

```text
╔════════════════════════════════════════════════════╗
║  MONITOR HU-USP – Especialidades                   ║
╠════════════════════════════════════════════════════╣
║ Última verificação: 18/02 14:30:05                 ║
║ Status: ✅ Conectado                               ║
╠════════════════════════════════════════════════════╣
║ NOVAS VAGAS (1)                                    ║
║ • CARDIOLOGIA                                      ║
╠════════════════════════════════════════════════════╣
║ Histórico recente                                  ║
║ 🟢 18/02 14:30: Cardiologia abriu                  ║
║ 🔴 18/02 09:15: Dermatologia fechou                ║
╚════════════════════════════════════════════════════╝

💤 Próxima verificação em 15 minutos...
```

---

## 🛠️ Arquitetura

- `monitor_hu/monitor.py` → Orquestrador principal + Dashboard
- `monitor_hu/guardian.py` → Watchdog externo (sentinela)
- `monitor_hu/parser.py` → Autenticação + scraping (Selenium)
- `monitor_hu/scheduler.py` → Intervalo adaptativo
- `monitor_hu/state.py` → Estado local, snapshots e heartbeat
- `monitor_hu/notifier.py` → Notificações (Telegram) + histórico
- `config.yaml` → Configuração de horários e intervalos
- `.env` → Credenciais e identificação da máquina
- `data/` → Cookies, logs e registros

Separação clara entre:

- Configuração
- Segredos
- Estado
- Persistência
- Lógica

---

## ⚠️ Aviso Legal

Este software é para uso pessoal e educacional.

- Utilize intervalos de tempo razoáveis (como o padrão sugerido)
- Não sobrecarregue os serviços do Hospital Universitário
- Respeite as políticas de uso

O autor não se responsabiliza por qualquer uso indevido desta ferramenta.