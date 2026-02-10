# 🏥 Monitor HU-USP

Bot de automação desenvolvido em Python para monitorar a disponibilidade de vagas de especialidades médicas no sistema do Hospital Universitário da USP (ResHU).

O sistema realiza login automático, contorna verificações de segurança básicas (com intervenção humana para CAPTCHA), monitora a lista de especialidades e notifica via Telegram e E-mail quando novas vagas de interesse surgem.

## 🚀 Funcionalidades

- **Monitoramento em Tempo Real:** Verifica a lista de especialidades a cada X segundos.
- **Notificações Inteligentes:**
  - **Telegram:** Envia mensagem com Screenshot da tela no momento da detecção.
  - **E-mail:** Envia alerta para seu e-mail USP/Pessoal.
  - **Áudio:** Emite alertas sonoros (Fala no macOS / Bip no Windows).
- **Resiliência:** Recuperação automática de sessão expirada e reinício do navegador em caso de falhas.
- **Log Histórico:** Salva todas as alterações (vagas abertas/fechadas) em um arquivo `.csv`.
- **Anti-Spam:** Não notifica repetidamente sobre a mesma vaga na mesma sessão.
- **Furtividade:** Usa User-Agent de navegador real e intervalos aleatórios (Jitter).

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Google Chrome instalado
- Conta no Telegram (para o Bot)
- Senha de App do Gmail (para envio de e-mails)

## 🔧 Instalação

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/MonitorHU.git](https://github.com/seu-usuario/MonitorHU.git)
   cd MonitorHU
