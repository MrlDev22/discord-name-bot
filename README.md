# 🤖 Discord Name Availability Bot

Bot que monitora nomes de 1 a 5 dígitos no Discord e avisa no canal quando um fica disponível.

---

## ⚡ Setup rápido

### 1. Criar o bot no Discord Developer Portal

1. Acesse [discord.com/developers/applications](https://discord.com/developers/applications)
2. Clique em **New Application** → dê um nome
3. Vá em **Bot** → clique em **Add Bot**
4. Copie o **Token** (vai no `bot.py` na variável `BOT_TOKEN`)
5. Em **Privileged Gateway Intents**, ative **Message Content Intent**
6. Vá em **OAuth2 → URL Generator**:
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Embed Links`, `Read Message History`
   - Copie a URL gerada e abra no navegador para convidar o bot ao servidor

### 2. Pegar o ID do canal

1. No Discord, vá em **Configurações → Avançado → Modo de desenvolvedor** (ativar)
2. Clique com botão direito no canal desejado → **Copiar ID**
3. Cole em `bot.py` na variável `CHANNEL_ID`

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar o bot.py

Abra `bot.py` e edite o bloco de configurações no topo:

```python
BOT_TOKEN      = "SEU_TOKEN_AQUI"         # Token do bot
CHANNEL_ID     = 123456789012345678       # ID do canal
CHECK_INTERVAL = 10                       # Minutos entre verificações
MIN_LENGTH     = 1                        # Tamanho mínimo
MAX_LENGTH     = 5                        # Tamanho máximo
CHARS          = string.digits            # Só números (0-9)
                                          # Use string.ascii_lowercase para letras
```

### 5. Rodar

```bash
python bot.py
```

---

## 📋 Comandos disponíveis

| Comando   | Descrição |
|-----------|-----------|
| `!check`  | Força uma verificação imediata |
| `!status` | Mostra estatísticas do bot |
| `!lista`  | Lista todos os nomes disponíveis detectados |

---

## ⚙️ Personalização

**Só letras (a-z):**
```python
CHARS = string.ascii_lowercase
```

**Letras + números:**
```python
CHARS = string.ascii_lowercase + string.digits
```

**Verificar só nomes de 3 dígitos:**
```python
MIN_LENGTH = 3
MAX_LENGTH = 3
```

---

## 🔢 Quantidade de nomes monitorados

| Comprimento | Só números | Só letras |
|-------------|-----------|-----------|
| 1 dígito    | 10        | 26        |
| 2 dígitos   | 100       | 676       |
| 3 dígitos   | 1.000     | 17.576    |
| 4 dígitos   | 10.000    | 456.976   |
| 5 dígitos   | 100.000   | 11.881.376|

> ⚠️ Para letras + grandes comprimentos, o bot pode demorar muito por ciclo. Recomendo usar `MIN_LENGTH = 3` e `MAX_LENGTH = 5` com só números para começar.

---

## 🛡️ Sobre rate limits

O bot tem um delay de `0.3s` entre cada verificação e respeita o header `Retry-After` da API do Discord. Mesmo assim, com muitos nomes, prefira intervalos maiores (`CHECK_INTERVAL = 30` ou mais).
