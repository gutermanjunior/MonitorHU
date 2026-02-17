## 🛡️ Como Usar (Guardian)

Recomenda-se executar o projeto através do **Guardian**. Ele funciona como uma camada de segurança que mantêm o Monitor rodando mesmo se houver erros de rede ou travamentos do Chrome.

**Comando Principal:**
```bash
python Guardian.py

Inicia o monitoramento com intervalo padrão e interface visual.  

### Modo "Fantasma" (Headless)

```bash
python Guardian.py --headless
```

Roda o navegador em segundo plano (invisível).  

### Modo "Sniper" (Alvos Específicos)

```bash
python Guardian.py --alvos "DERMATO, CARDIO"
```

O bot ignorará todas as outras vagas e avisará apenas se encontrar Dermatologia ou Cardiologia.  

### Ajuste de Intervalo

```bash
python MonitorHU.py --intervalo 60
```

---

## Comandos do Telegram

Uma vez rodando, você pode controlar o bot enviando mensagens privadas para ele:

| Comando      | Descrição                                                                 |
|-------------|---------------------------------------------------------------------------|
| `/status`   | Exibe tempo de atividade, modo atual, alvos e estatísticas.              |
| `/print`    | Tira um screenshot da tela atual do navegador e envia para você.         |
| `/pause`    | Pausa temporariamente as verificações.                                   |
| `/resume`   | Retoma o monitoramento.                                                  |
| `/list` | Lista as especialidades disponíveis no momento em formato de texto. |
| `/relatorio` | Gera um gráfico visual baseada no histórico (CSV) e envia no chat. |
| `/add [NOME]`    | Adiciona uma nova especialidade à lista de alvos em tempo real.        |
| `/remove [NOME]` | Remove uma especialidade da lista de alvos.                           |
| `/alvos`    | Lista quais especialidades estão sendo buscadas no momento.              |
| `/ping`     | Teste de conexão.                                                        |

---

## Funcionalidades
- **🛡️ Sistema Guardian (Anti-Crash):** Um script "vigia" dedicado que monitora o processo principal e o reinicia automaticamente em caso de falhas ou travamentos.
- **🍪 Persistência de Sessão (Cookies):** Salva os dados de sessão localmente. Se você reiniciar o computador, o bot tenta restaurar o login sem pedir CAPTCHA novamente.
- **📊 Relatórios Gráficos:** Novo comando `/relatorio` envia um gráfico de barras no Telegram mostrando os horários de pico das vagas encontradas.
- **🌙 Modo Não Perturbe:** O sistema de áudio é silenciado automaticamente entre **22h e 08h**, mantendo apenas as notificações silenciosas (Telegram/E-mail).
- **📸 Print Expandido:** O comando `/print` e os alertas de vaga agora expandem o menu de especialidades antes de tirar a foto, facilitando a leitura.

---

## Arquitetura do Projeto

O sistema utiliza uma arquitetura modular para facilitar a manutenção:

- **BrowserService**: Gerencia o Selenium e interações com o site.  
- **TelegramService**: Gerencia comunicação bidirecional com a API do Telegram.  
- **DataService**: Gerencia persistência de dados (logs CSV).  
- **MonitorController**: Orquestra os serviços e aplica a lógica de negócio.  
- **Guardian Process:** Processo pai (`Guardian.py`) que gerencia o ciclo de vida do bot, captura erros críticos e realiza reinicializações automáticas.

---

🤖 Como configurar o Telegram (Passo a Passo)
Para receber notificações no seu celular, você precisa criar um "robô" pessoal no Telegram. É gratuito, rápido e não exige conhecimentos de programação.
Passo 1: Criar o seu Robô (Token)
 * Abra o Telegram e procure pelo usuário @BotFather (ele tem um selo azul de verificado).
 * Clique em Começar (ou envie a mensagem /start).
 * Envie o comando: /newbot
 * O BotFather vai pedir um Nome para o seu robô (pode ser qualquer coisa).
   * Exemplo: Monitor HU do Guterman
 * Agora ele vai pedir um Username (deve ser único no mundo e terminar obrigatoriamente em bot).
   * Exemplo: monitor_hu_vagas_2024_bot
 * Se o nome estiver disponível, o BotFather enviará uma mensagem de parabéns. Procure pela frase "Use this token to access the HTTP API:".
 * O código logo abaixo é o seu TOKEN. Copie esse código (ele se parece com: 123456789:ABCdefGHIjkl...).
Passo 2: Descobrir o seu ID (Chat ID)
O robô precisa saber o "endereço" do seu chat para enviar mensagens só para você.
 * No Telegram, procure pelo usuário @userinfobot (ou qualquer bot de ID).
 * Clique em Começar (ou envie /start).
 * Ele responderá imediatamente com seus dados. Procure pelo número ao lado de Id.
   * Exemplo: 811632084
 * Copie esse número.
Passo 3: Ativar e Configurar
 * Muito Importante: Antes de rodar o programa, procure pelo nome de usuário do seu robô (aquele que você criou no Passo 1) e envie um "Oi" para ele. Isso autoriza o robô a te mandar mensagens.
 * Abra o arquivo .env na pasta do programa (se não tiver, crie um baseado no .env.example).
 * Cole os dados que você obteve:
<!-- end list -->
TELEGRAM_TOKEN=cole_o_token_aqui
TELEGRAM_CHAT_ID=cole_o_seu_id_aqui



---

## Aviso Legal

Este software é uma ferramenta de automação pessoal desenvolvida para fins educacionais e de auxílio próprio.  O uso de bots deve ser feito de maneira responsável para não sobrecarregar os serviços públicos.  O autor não se responsabiliza pelo uso indevido da ferramenta.
