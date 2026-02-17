🏥 Monitor de Vagas HU-USP
> Status: ✅ Funcional e Estável (v16.0)
> 
Um robô de automação inteligente desenvolvido em Python para monitorar a disponibilidade de vagas de especialidades médicas no sistema do Hospital Universitário da USP (ResHU).
O objetivo deste projeto é ajudar pacientes e alunos a encontrar vagas de especialidades concorridas (como Dermatologia, Cardiologia, etc.) sem precisar atualizar a página manualmente o dia inteiro.
✨ Funcionalidades Detalhadas
🤖 Automação e Inteligência
 * Monitoramento Contínuo: Verifica a lista de especialidades automaticamente em intervalos inteligentes.
 * Agendamento Inteligente (Smart Scheduling):
   * Horário Comercial: Verificações frequentes e aleatórias (para evitar detecção).
   * Madrugada (22h-06h): Reduz drasticamente a frequência para economizar recursos e evitar bloqueios.
 * Persistência de Sessão (Cookies): Salva sua sessão de login. Se o robô reiniciar, ele tenta entrar direto sem pedir CAPTCHA novamente.
 * Recuperação de Falhas: Se a internet cair ou o navegador travar, o sistema reinicia o processo automaticamente.
 * Modo Fantasma (Headless): Opção de rodar o navegador em segundo plano, sem abrir janelas.
🎯 Modos de Operação
 * Modo Geral (Padrão): Monitora todas as vagas, exceto as que estiverem na "Lista Negra" (ex: Pediatria, Odontologia).
 * Modo Sniper (Alvos): Você define uma lista específica (ex: "Cardio", "Dermato"). O robô ignora tudo o que não for seu alvo.
📱 Notificações e Controle
 * Telegram Bidirecional (Controle Remoto):
   * Receba prints da tela e alertas em tempo real.
   * Envie comandos para o robô direto pelo chat (Pausar, Retomar, Pedir Status).
 * E-mail: Envia alertas formais para seu e-mail USP ou Pessoal.
 * Alertas Sonoros:
   * Windows: Bip sonoro.
   * macOS: O computador fala em voz alta qual vaga abriu.
📊 Dados e Relatórios
 * Log Histórico: Salva todas as movimentações em historico_especialidades.csv.
 * Gráficos Automáticos: Gera gráficos de horários de pico sob demanda via comando do Telegram.
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

3. Instalar Dependências
Com o ambiente ativado, instale as bibliotecas necessárias:
pip install -r requirements.txt

⚙️ Configuração (Crucial)
O sistema precisa das suas senhas para funcionar, mas nunca colocamos senhas direto no código. Usamos um arquivo secreto chamado .env.
 * Na pasta do projeto, crie um arquivo novo chamado .env.
 * Cole o modelo abaixo, preenchendo com seus dados:
<!-- end list -->
# --- DADOS DE ACESSO AO HU ---
HU_USER=seu_numero_usp
HU_DATA=DD/MM/AAAA

# --- NOTIFICAÇÃO POR E-MAIL (GMAIL) ---
# Necessário ativar "Verificação em 2 etapas" e criar uma "Senha de App" no Google.
EMAIL_CONTA=seu_email@gmail.com
EMAIL_SENHA=senha_de_app_gerada_pelo_google
EMAIL_DESTINO=email_onde_quer_receber@usp.br

# --- NOTIFICAÇÃO POR TELEGRAM ---
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_id_aqui

🤖 Como conseguir as chaves do Telegram?
 * Busque por @BotFather no Telegram e envie /newbot.
 * Dê um nome e username para receber seu TOKEN.
 * Busque por @userinfobot para descobrir seu CHAT ID (número).
 * Importante: Envie um "Oi" para o seu novo bot antes de rodar o programa.
▶️ Como Usar
Execução Básica
Abre o navegador e inicia o monitoramento padrão (Intervalo ~120s).
python MonitorHU.py

Argumentos de Linha de Comando (CLI)
Você pode personalizar a execução sem mexer no código:
 * Modo Sniper (Só avisa o que você quer):
   python MonitorHU.py --alvos "cardiologia,dermatologia"

 * Alterar velocidade (Cuidado com bloqueios):
   python MonitorHU.py --intervalo 60

 * Modo Invisível (Headless):
   python MonitorHU.py --headless

🎮 Comandos do Telegram
Uma vez que o robô esteja rodando, você pode controlá-lo enviando mensagens no chat do Telegram:
| Comando | Descrição |
|---|---|
| /status | Mostra tempo de execução, modo atual e quantas vagas estão visíveis. |
| /list | Envia uma lista em texto de todas as especialidades disponíveis agora. |
| /print | Tira um Screenshot da tela do navegador e te envia. |
| /pause | Pausa o monitoramento temporariamente (útil para manutenção). |
| /resume | Retoma o monitoramento. |
| /relatorio | Gera e envia um Gráfico mostrando os horários que mais abrem vagas. |
| /alvos | Lista quais especialidades estão na sua mira (Modo Sniper). |
| /add [nome] | Adiciona uma nova especialidade aos alvos. Ex: /add Otorrino |
| /remove [nome] | Remove uma especialidade dos alvos. |
| /ping | Teste de conexão (Pong!). |
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
