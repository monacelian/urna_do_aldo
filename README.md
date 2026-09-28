# 🗳️ Urna Eletrônica Escolar (Estilo TSE)

Sistema completo de **Urna Eletrônica Escolar** desenvolvido em Python/Flask, com interface inspirada nas urnas do TSE, sons característicos, controle de votação por turmas e painel administrativo em tempo real.

Ideal para eleições de **Representantes de Turma**, **Líderes de Sala**, **Grêmio Estudantil** e conselhos escolares.

---

## ✨ Funcionalidades

- 🏫 **Votação 100% por Turmas:** Permite que turmas diferentes tenham candidatos com o mesmo número (ex: Chapa 1 no 1º Ano e Chapa 1 no 2º Ano) sem conflito.
- 🔊 **Sons Reais da Urna:** Áudio de tecla, confirmação e encerramento idênticos à urna real.
- 🔒 **Controle de Sessão e Segurança:** A urna bloqueia automaticamente ao término do voto e é liberada pelo mesário/professor no painel.
- 📱 **Acesso em Rede Local:** Funciona em rede Wi-Fi/cabeada para acesso simultâneo via computador, tablet ou celular.
- 📊 **Apuração em Tempo Real:** Gráficos e tabelas automáticas com a contagem de votos e eleitos por sala.
- 📦 **100% Portátil (Zero Senha de Administrador):** Pode ser executado em qualquer pasta sem necessidade de privilégios de administrador do Windows.

---

## 🚀 Como Usar (Versão Portátil — Sem Instalação)

1. Baixe o arquivo `Urna_Escolar.zip` na aba [**Releases**](../../releases).
2. Extraia o arquivo para a sua **Área de Trabalho** ou pasta de sua preferência.
3. Dê dois cliques em **`Urna_Escolar.exe`**.
4. O navegador abrirá automaticamente no **Painel Admin** (`http://localhost:5000/admin`).

> 💡 **Dica:** Não requer instalação de Python nem permissões de administrador.

---

## 💻 Como Rodar via Código-Fonte (Desenvolvedores)

Caso queira executar ou modificar o código Python diretamente:

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/urna-eletronica-escolar.git
   cd urna-eletronica-escolar
   ```

2. **Crie e ative um ambiente virtual (opcional, mas recomendado):**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Inicie o servidor:**
   ```bash
   python app.py
   ```

5. Acesse no navegador:
   - **Painel Admin:** `http://127.0.0.1:5000/admin`
   - **Urna de Votação:** `http://127.0.0.1:5000/urna`
   - **Resultados:** `http://127.0.0.1:5000/resultados`

---

## 🛠️ Como Gerar um Novo Executável (.exe)

Para gerar um novo executável portátil utilizando o PyInstaller:

```bash
python -m PyInstaller --onefile --noconsole --add-data "templates;templates" --add-data "static;static" --name "Urna_Escolar" app.py
```

O arquivo `Urna_Escolar.exe` será gerado dentro da pasta `dist/`.

---

## 📘 Ordem de Configuração no Painel

1. **1º Cadastre as Turmas:** (Ex: *1º Ano A*, *2º Ano B*).
2. **2º Cadastre os Cargos:** (Ex: *Presidente de Turma*, *Máx. de Votos: 1*).
3. **3º Cadastre os Candidatos:** Selecione a turma correspondente de cada aluno.
4. **4º Iniciar a Eleição:** Selecione a turma que irá votar e clique em **Iniciar**.

---

## 📄 Licença
Distribuído sob a licença MIT. Livre para uso em escolas públicas e privadas.
