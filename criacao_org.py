from flask import Flask, request, jsonify, render_template, render_template_string
import psycopg2
import uuid
import re
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Configurações do Banco de Dados
DB_NAME = "db_safira_softwares"
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "user": "postgres",
    "password": "xbala"
}

def conectar(db=DB_NAME):
    try:
        conn = psycopg2.connect(
            database=db,
            **DB_CONFIG
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Erro conexão: {e}")
        return None

def criar_database():
    conn = psycopg2.connect(
        database="postgres",
        **DB_CONFIG
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    existe = cur.fetchone()

    if not existe:
        cur.execute(f"CREATE DATABASE {DB_NAME}")

    cur.close()
    conn.close()

def inicializar():
    criar_database()
    conn = conectar()
    if not conn: return

    cur = conn.cursor()
    # Tabela mestre para controle de tenants
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.tbl_organizacoes (
            id SERIAL PRIMARY KEY,
            numero INT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            nome_unidade TEXT,
            schema TEXT NOT NULL,
            qtd_usuarios_limite INT DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.tbl_usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            organizacao_id INT REFERENCES public.tbl_organizacoes(id),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.tbl_convites_usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            organizacao_id INT REFERENCES public.tbl_organizacoes(id),
            usado BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def proximo_numero():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM public.tbl_organizacoes")
    numero = cur.fetchone()[0]
    cur.close()
    conn.close()
    return numero

def carregar_sql():
    # Certifique-se que o caminho do arquivo está correto em relação ao app.py
    try:
        with open("schema/schema_base.sql", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def executar_schema(conn, schema):
    cur = conn.cursor()
    sql = carregar_sql()
    if sql:
        cur.execute(f"SET search_path TO {schema}")
        cur.execute(sql)
    conn.commit()
    cur.close()

# --- ROTAS API ---

@app.route("/")
def index():
    # Carrega o template original
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        return "Template não encontrado", 404

    # 1. Alteração de Branding: Safira SaaS Control -> Safira Cloud
    html = html.replace(
        'Safira <span class="text-slate-400 font-light">SaaS Control</span>',
        'Safira <span class="text-blue-400 font-light">Cloud</span>'
    )

    # 2. Remover texto: Gerenciamento de instâncias e schemas isolados
    html = html.replace(
        '<p class="text-slate-500 text-sm">Gerenciamento de instâncias e schemas isolados</p>',
        ''
    )

    # 3. Logo será uma nuvem (lucide: cloud)
    html = html.replace('data-lucide="layers"', 'data-lucide="cloud" id="cloud-logo"')

    # 4. Próximo Schema dinâmico ao carregar
    prox = proximo_numero()
    schema_formatado = f"org_{str(prox).zfill(4)}"
    html = html.replace('value="AUTO-SEQUENCE"', f'value="{schema_formatado}"')

    # 6. Injeção de novos campos no formulário
    novos_campos = """
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Nome da Organização</label>
                            <input type="text" id="nome_org" placeholder="Ex: Safira Corp"
                                class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none">
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Nome da Unidade</label>
                            <input type="text" id="nome_unidade" placeholder="Ex: Matriz São Paulo"
                                class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none">
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Email do Primeiro Usuário</label>
                            <input type="email" id="email" placeholder="usuario@email.com"
                                class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none">
                        </div>

                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Quantidade de Usuários</label>
                            <input type="number" id="qtd_usuarios" value="1" min="1"
                                class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none">
                        </div>
    """

    # Localizar o bloco original do Nome da Unidade e substituir
    ponto_insercao = re.compile(r'<div>\s*<label[^>]*>Nome da Unidade</label>\s*<input[^>]*id="nome"[^>]*>\s*</div>', re.DOTALL)
    html = ponto_insercao.sub(novos_campos, html)

    # 5. JS para animação da nuvem e atualização do próximo schema
    script_js = """
    <script>
        // Animação da Nuvem (Floating)
        const animaNuvem = () => {
            const logo = document.getElementById('cloud-logo');
            if (logo) {
                let pos = 0;
                let subindo = true;
                setInterval(() => {
                    if (subindo) pos += 0.2; else pos -= 0.2;
                    if (pos >= 5) subindo = false; if (pos <= -5) subindo = true;
                    logo.style.transform = `translateY(${pos}px)`;
                }, 30);
            }
        };

        // Sobrescrever listarOrgs para atualizar o próximo ID após criação/refresh
        const originalListarOrgs = window.listarOrgs;
        window.listarOrgs = async function() {
            await originalListarOrgs();
            try {
                const r = await fetch("/proximo-id");
                const d = await r.json();
                if (d.sucesso) {
                    document.getElementById("numero_display").value = d.proximo;
                }
            } catch (e) {}
        };

        // Sobrescrever função criar original
        window.criar = async function() {
            const btn = document.getElementById("btnCriar");
            const nome_org = document.getElementById("nome_org").value;
            const nome_unidade = document.getElementById("nome_unidade").value;
            const email = document.getElementById("email").value;
            const qtd_usuarios = document.getElementById("qtd_usuarios").value;
            const container = document.getElementById("statusContainer");

            if (!nome_org || !email || !nome_unidade) {
                alert("Por favor preencha todos os campos obrigatórios.");
                return;
            }

            btn.disabled = true;
            btn.innerHTML = `<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i> Criando...`;
            lucide.createIcons();

            try {
                const res = await fetch("/criar-organizacao", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        nome: nome_org,
                        unidade: nome_unidade,
                        email: email,
                        qtd_usuarios: parseInt(qtd_usuarios)
                    })
                });

                const data = await res.json();

                if (data.status === "ok") {
                    container.className = "mt-4 p-4 rounded-lg border bg-emerald-50 border-emerald-200 text-emerald-700 block";
                    document.getElementById("msgHeader").innerText = "Sucesso!";
                    document.getElementById("msgBody").innerText = `Convite enviado para ${email}. Link: ${data.link_convite || ''}`;

                    document.getElementById("nome_org").value = "";
                    document.getElementById("nome_unidade").value = "";
                    document.getElementById("email").value = "";
                    document.getElementById("qtd_usuarios").value = "1";

                    listarOrgs();
                } else {
                    throw new Error(data.mensagem);
                }
            } catch (err) {
                container.className = "mt-4 p-4 rounded-lg border bg-red-50 border-red-200 text-red-700 block";
                document.getElementById("msgHeader").innerText = "Erro";
                document.getElementById("msgBody").innerText = err.message;
            } finally {
                btn.disabled = false;
                btn.innerHTML = `<i data-lucide="zap" class="w-4 h-4"></i> Provisionar`;
                lucide.createIcons();
            }
        };

        // Iniciar animação
        setTimeout(animaNuvem, 500);
    </script>
    """
    # Usando render_template_string para garantir que o Jinja2 renderize o conteúdo original se houver
    return render_template_string(html.replace('</body>', f"{script_js}</body>"))

@app.route("/proximo-id")
def get_proximo_id():
    """Retorna o próximo ID formatado como org_000X para o front-end"""
    prox = proximo_numero()
    schema_formatado = f"org_{str(prox).zfill(4)}"
    return jsonify({"sucesso": True, "proximo": schema_formatado})

@app.route("/organizacoes")
def listar_orgs():
    """Retorna a lista de organizações para o Grid View"""
    conn = conectar()
    if not conn: return jsonify([])

    cur = conn.cursor()
    cur.execute("SELECT numero, nome, schema FROM public.tbl_organizacoes ORDER BY numero DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    lista = [{"numero": r[0], "nome": r[1], "schema": r[2]} for r in rows]
    return jsonify(lista)

@app.route("/criar-organizacao", methods=["POST"])
def criar_org():
    data = request.json
    nome = data.get("nome")
    unidade = data.get("unidade")
    email = data.get("email")
    qtd_usuarios = data.get("qtd_usuarios", 1)

    if not nome or not email or not unidade:
        return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios"}), 400

    if int(qtd_usuarios) < 1:
        return jsonify({"status": "erro", "mensagem": "Quantidade de usuários deve ser pelo menos 1"}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"status": "erro", "mensagem": "Email inválido"}), 400

    conn = conectar()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco"}), 500

    try:
        numero = proximo_numero()
        schema = f"org_{str(numero).zfill(4)}"

        cur = conn.cursor()
        cur.execute("""
            INSERT INTO public.tbl_organizacoes (numero, nome, nome_unidade, schema, qtd_usuarios_limite)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (numero, nome, unidade, schema, qtd_usuarios))
        org_id = cur.fetchone()[0]

        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        executar_schema(conn, schema)

        token = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO public.tbl_convites_usuarios (email, token, organizacao_id)
            VALUES (%s, %s, %s)
        """, (email, token, org_id))

        conn.commit()
        cur.close()
        conn.close()

        link_convite = f"/primeiro-acesso?token={token}"
        print(f"SIMULAÇÃO ENVIO EMAIL PARA {email}: Bem-vindo! Crie sua conta aqui: {link_convite}")

        return jsonify({"status": "ok", "schema": schema, "link_convite": link_convite})

    except Exception as e:
        if conn: conn.close()
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route("/primeiro-acesso")
def primeiro_acesso():
    token = request.args.get("token")
    if not token:
        return "Token não fornecido", 400

    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT email, organizacao_id FROM public.tbl_convites_usuarios WHERE token = %s AND usado = FALSE", (token,))
    convite = cur.fetchone()
    cur.close()
    conn.close()

    if not convite:
        return "Convite inválido ou já utilizado", 400

    email = convite[0]

    # Usando render_template_string com placeholders para evitar XSS
    template_primeiro_acesso = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>Primeiro Acesso | Safira Cloud</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-50 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200 w-full max-w-md">
            <h1 class="text-2xl font-bold text-blue-600 mb-6">Definir Senha</h1>
            <p class="text-slate-500 mb-4">Olá <strong>{{ email }}</strong>, crie sua senha para acessar o sistema.</p>
            <form action="/finalizar-cadastro" method="POST" class="space-y-4">
                <input type="hidden" name="token" value="{{ token }}">
                <div>
                    <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Nova Senha</label>
                    <input type="password" name="senha" required class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all">
                    Confirmar e Acessar
                </button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(template_primeiro_acesso, email=email, token=token)

@app.route("/finalizar-cadastro", methods=["POST"])
def finalizar_cadastro():
    token = request.form.get("token")
    senha = request.form.get("senha")

    if not token or not senha:
        return "Dados incompletos", 400

    conn = conectar()
    try:
        cur = conn.cursor()
        cur.execute("SELECT email, organizacao_id FROM public.tbl_convites_usuarios WHERE token = %s AND usado = FALSE", (token,))
        convite = cur.fetchone()

        if not convite:
            return "Convite inválido", 400

        email, org_id = convite
        senha_hash = generate_password_hash(senha)

        cur.execute("""
            INSERT INTO public.tbl_usuarios (email, senha, organizacao_id)
            VALUES (%s, %s, %s)
        """, (email, senha_hash, org_id))

        cur.execute("UPDATE public.tbl_convites_usuarios SET usado = TRUE WHERE token = %s", (token,))

        conn.commit()
        cur.close()
        conn.close()

        return """
        <div style="text-align:center; padding:50px; font-family:sans-serif;">
            <h1 style="color:#2563eb;">Cadastro Finalizado!</h1>
            <p>Seu usuário foi criado com sucesso. Agora você pode fazer login na Safira Cloud.</p>
        </div>
        """
    except Exception as e:
        if conn: conn.close()
        return str(e), 500

if __name__ == "__main__":
    inicializar()
    app.run(debug=True)
