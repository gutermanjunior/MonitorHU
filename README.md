## Como Usar (CLI)

Execute o bot através do terminal. Você pode personalizar o comportamento usando argumentos.  

### Uso Básico

```bash
python MonitorHU.py
```

Inicia o monitoramento com intervalo padrão e interface visual.  

### Modo "Fantasma" (Headless)

```bash
python MonitorHU.py --headless
```

Roda o navegador em segundo plano (invisível).  

### Modo "Sniper" (Alvos Específicos)

```bash
python MonitorHU.py --alvos "DERMATO, CARDIO"
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
| `/add [NOME]`    | Adiciona uma nova especialidade à lista de alvos em tempo real.        |
| `/remove [NOME]` | Remove uma especialidade da lista de alvos.                           |
| `/alvos`    | Lista quais especialidades estão sendo buscadas no momento.              |
| `/ping`     | Teste de conexão.                                                        |

---

## Arquitetura do Projeto

O sistema utiliza uma arquitetura modular para facilitar a manutenção:

- **BrowserService**: Gerencia o Selenium e interações com o site.  
- **TelegramService**: Gerencia comunicação bidirecional com a API do Telegram.  
- **DataService**: Gerencia persistência de dados (logs CSV).  
- **MonitorController**: Orquestra os serviços e aplica a lógica de negócio.  

---

## Aviso Legal

Este software é uma ferramenta de automação pessoal desenvolvida para fins educacionais e de auxílio próprio.  O uso de bots deve ser feito de maneira responsável para não sobrecarregar os serviços públicos.  O autor não se responsabiliza pelo uso indevido da ferramenta.
