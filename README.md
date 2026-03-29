# 🏥 Monitor HU-USP (v3.1) – Ultimate Edition

**Status:** 🚀 Estável & Inteligente  
**Autor:** Guterman ([guterman.com.br](http://guterman.com.br))

Sistema avançado de monitoramento e automação para detecção de vagas em especialidades médicas no Hospital Universitário da USP. Esta versão 3.1 traz uma interface rica (TUI), resiliência extrema via Guardian e filtros inteligentes de busca.

---

## ✨ Novidades da Versão 3.1

- **🖥️ Rich TUI Dashboard:** Interface visual moderna e estática no terminal que se atualiza em tempo real sem "picar" a tela.
- **🎯 Sniper Mode:** Permite focar em especialidades específicas via comandos no Telegram, ignorando o resto.
- **🔇 Silent Baseline:** O bot memoriza o estado inicial do site sem disparar alertas falsos na primeira execução.
- **💉 JS Injection:** Bypassa máscaras de entrada de data no site do HU via injeção direta de JavaScript no Selenium.
- **📊 Analytics On-Demand:** Gere gráficos de horários de pico de abertura de vagas diretamente pelo Telegram.

---

## 🛡️ Arquitetura Resiliente

O sistema opera em duas camadas para garantir que você nunca perca uma vaga:

1.  **Monitor (`monitor.py`):** O cérebro que navega, analisa mudanças e desenha a interface.
2.  **Guardian (`guardian.py`):** O sentinela. Ele vigia o Monitor; se houver queda de internet ou crash do browser, o Guardian aplica um *backoff* exponencial e reinicia o sistema automaticamente.

---

## 🚀 Como Rodar

### 1. Instalação
```bash
# Clone e entre na pasta
git clone https://github.com/seu-usuario/MonitorHU.git
cd MonitorHU

# Configure o ambiente
python -m venv venv
source venv/Scripts/activate  # No Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuração (`.env`)
Crie um arquivo `.env` na raiz do projeto com suas credenciais:
```env
# Acesso HU
HU_USER=1234567          # Seu número USP
HU_DATA=01/01/1990       # Data de nascimento (DD/MM/AAAA)

# Telegram
TELEGRAM_TOKEN=...       # Token obtido com o @BotFather
TELEGRAM_CHAT_ID=...     # Seu Chat ID (obtido com @userinfobot)

# Notificações Adicionais
EMAIL_CONTA=...          # Gmail para alertas
EMAIL_SENHA=...          # Senha de App do Google
EMAIL_DESTINO=...        # Para onde enviar o e-mail
```

### 3. Execução Protegida (Recomendado)
```bash
python -m monitor_hu.guardian
```

---

## 🤖 Comandos do Telegram

O Monitor é totalmente interativo. Envie estes comandos para o seu bot:

| Comando | Descrição |
| :--- | :--- |
| `/status` | Tempo de atividade e vagas visíveis agora. |
| `/list` | Lista completa das especialidades abertas em texto. |
| `/add [NOME]` | Adiciona uma especialidade ao **Modo Sniper**. |
| `/remove [NOME]` | Remove uma especialidade dos alvos. |
| `/relatorio` | Gera e envia o gráfico de histórico de horários. |
| `/print` | Tira um print da tela do navegador agora. |
| `/pause` / `/resume` | Pausa ou retoma o monitoramento remotamente. |

---

## ⚠️ Problemas Conhecidos (Known Issues)

- **PowerShell Artifacts:** Devido a limitações de buffer do Windows Terminal/PowerShell 7, ao encerrar o programa via `Ctrl+C`, pequenos resíduos visuais da interface podem permanecer na tela. Isso não afeta a funcionalidade do código e é um comportamento estético do terminal sob interrupção de subprocessos.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **Selenium** (Automação Web)
- **Rich** (Interface TUI no Terminal)
- **Pandas & Matplotlib** (Análise de Dados e Gráficos)
- **SMTP/Requests** (Notificações e API do Telegram)

---

## ⚠️ Aviso Legal

Este software é para uso pessoal e educacional.

- Utilize intervalos de tempo razoáveis (como o padrão sugerido)
- Não sobrecarregue os serviços do Hospital Universitário
- Respeite as políticas de uso

O autor não se responsabiliza por qualquer uso indevido desta ferramenta.

*Este software é para uso pessoal e educacional. Utilize com responsabilidade e respeite os intervalos de acesso ao servidor do HU-USP.*
