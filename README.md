🏥 Monitor de Vagas HU-USP
> Status: ✅ Funcional e Estável (v11.0)
> 
Um robô de automação inteligente desenvolvido em Python para monitorar a disponibilidade de vagas de especialidades médicas no sistema do Hospital Universitário da USP (ResHU).
O objetivo deste projeto é ajudar pacientes e alunos a encontrar vagas de especialidades concorridas (como Dermatologia, Cardiologia, etc.) sem precisar atualizar a página manualmente o dia inteiro.
✨ Funcionalidades
 * 🔍 Monitoramento Contínuo: Verifica a lista de especialidades a cada X segundos automaticamente.
 * 📱 Notificações via Telegram: Receba um alerta no celular com print da tela assim que uma vaga abrir.
 * 📧 Notificações via E-mail: Envia um aviso para seu e-mail (USP ou Pessoal).
 * 🔊 Alertas Sonoros:
   * Windows: Emite um Bip sonoro.
   * macOS: O computador fala qual vaga abriu (Voz: Luciana).
 * 🛡️ Resiliência: Se a internet cair ou o navegador travar, o robô reinicia sozinho.
 * 📊 Histórico de Dados: Salva todas as vagas que abriram e fecharam em um arquivo .csv para análise futura.
 * 👻 Modo Fantasma: Opção de rodar sem abrir a janela do navegador (headless).
🛠️ Pré-requisitos
Antes de começar, certifique-se de ter instalado:
 * Python 3.8+: Baixar aqui
   * No Windows, marque a opção "Add Python to PATH" na instalação.
 * Google Chrome: O navegador precisa estar atualizado.
🚀 Instalação (Passo a Passo)
1. Clonar ou Baixar
Baixe este projeto no seu computador e extraia a pasta.
2. Criar Ambiente Virtual
Abra o terminal na pasta do projeto e rode:
Windows:
python -m venv venv
venv\Scripts\activate

macOS / Linux:
python3 -m venv venv
source venv/bin/activate

(Você saberá que funcionou se aparecer um (venv) no início da linha do terminal).
3. Instalar Dependências
Com o ambiente ativado, instale as bibliotecas necessárias:
pip install -r requirements.txt

⚙️ Configuração (Crucial)
O sistema precisa das suas senhas para funcionar, mas nunca colocamos senhas direto no código. Usamos um arquivo secreto chamado .env.
 * Na pasta do projeto, crie um arquivo novo chamado .env (sem nome antes do ponto).
 * Abra esse arquivo com o Bloco de Notas e cole o modelo abaixo, preenchendo com seus dados:
<!-- end list -->
# --- DADOS DE ACESSO AO HU ---
HU_USER=seu_numero_usp
HU_DATA=10/03/1993

# --- NOTIFICAÇÃO POR E-MAIL (GMAIL) ---
# Necessário ativar "Verificação em 2 etapas" e criar uma "Senha de App" no Google.
EMAIL_CONTA=seu_email@gmail.com
EMAIL_SENHA=senha_de_app_gerada_pelo_google
EMAIL_DESTINO=email_onde_quer_receber@usp.br

# --- NOTIFICAÇÃO POR TELEGRAM ---
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_id_aqui

🤖 Como conseguir as chaves do Telegram?
Se você nunca criou um bot, siga este guia rápido:
 * Crie o Bot:
   * Abra o Telegram e busque por @BotFather.
   * Envie /newbot.
   * Dê um nome (ex: Monitor HU) e um username (ex: monitor_hu_bot).
   * Ele vai te dar um TOKEN (algo como 123456:ABC-DEF...). Copie e cole no .env.
 * Pegue seu ID:
   * Busque por @userinfobot no Telegram e clique em Iniciar.
   * Ele vai te responder com um número (ex: 811632084). Esse é o seu TELEGRAM_CHAT_ID.
 * Ative o Bot:
   * Busque pelo nome do seu bot recém-criado e envie um "Oi" para ele. Isso permite que ele te mande mensagens.
▶️ Como Usar
Com tudo configurado, basta rodar o comando no terminal:
Modo Padrão (Recomendado)
Abre o navegador, você faz o login manual (resolve o CAPTCHA) e o robô assume a partir daí. Verifica a cada 2 minutos.
python MonitorHU.py

Comandos Avançados
Você pode personalizar o comportamento sem mexer no código:
 * Alterar tempo de verificação (ex: a cada 30 segundos):
   python MonitorHU.py --intervalo 30

   (Cuidado: Intervalos muito curtos podem bloquear seu IP).
 * Modo Invisível (Headless):
   Roda o navegador em segundo plano, sem abrir janela.
   python MonitorHU.py --headless

📊 Analisando os Dados
O robô cria automaticamente um arquivo chamado historico_especialidades.csv.
Você pode abrir este arquivo no Excel para ver:
 * Quais especialidades abriram.
 * Em qual horário exato elas costumam aparecer.
Exemplo de conteúdo:
Data_Hora,Evento,Especialidade
2024-02-09 14:30:01,ADICIONADA,CARDIOLOGIA
2024-02-09 14:45:12,REMOVIDA,CARDIOLOGIA

⚠️ Aviso Legal
Este software foi desenvolvido para fins estritamente pessoais e de aprendizado. O uso de bots automatizados pode ir contra os termos de serviço de algumas instituições. Utilize com responsabilidade, respeitando intervalos de tempo razoáveis para não sobrecarregar o servidor do Hospital Universitário.
