from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import psycopg2
from functools import wraps

app = Flask(__name__)
app.secret_key = "safira_secret_key"

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
            schema TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabela de usuários globais (para login no painel de controle)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.tbl_usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(150),
            email VARCHAR(150) UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT NOW()
        )
    """)

    # Usuário padrão
    cur.execute("SELECT 1 FROM public.tbl_usuarios WHERE email = %s", ('suporte@safirasoftwares.inf.br',))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO public.tbl_usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
        """, ('Suporte Safira', 'suporte@safirasoftwares.inf.br', 'safira'))

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

        # Insere o usuário padrão no novo schema
        cur.execute("""
            INSERT INTO tbl_usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
            ON CONFLICT (email) DO NOTHING
        """, ('Suporte Safira', 'suporte@safirasoftwares.inf.br', 'safira'))

    conn.commit()
    cur.close()

# --- AUTH DECORATOR ---

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS API ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.form
        email = data.get("email")
        senha = data.get("password")

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT email, nome FROM public.tbl_usuarios WHERE email = %s AND senha = %s", (email, senha))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['usuario'] = user[0]
            session['nome'] = user[1]
            return redirect(url_for('index'))
        else:
            return render_template("login.html", erro="Credenciais inválidas")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/proximo-id")
@login_required
def get_proximo_id():
    """Retorna o próximo ID formatado como org_000X para o front-end"""
    prox = proximo_numero()
    schema_formatado = f"org_{str(prox).zfill(4)}"
    return jsonify({"sucesso": True, "proximo": schema_formatado})

@app.route("/organizacoes")
@login_required
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
@login_required
def criar_org():
    data = request.json
    nome = data.get("nome")

    if not nome:
        return jsonify({"status": "erro", "mensagem": "Nome é obrigatório"}), 400

    conn = conectar()
    if not conn:
        return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco"}), 500

    try:
        # 1. Define o número sequencial de forma atômica
        numero = proximo_numero()
        schema = f"org_{str(numero).zfill(4)}"

        cur = conn.cursor()

        # 2. Registra na tabela pública
        cur.execute("""
            INSERT INTO public.tbl_organizacoes (numero, nome, schema)
            VALUES (%s, %s, %s)
        """, (numero, nome, schema))

        # 3. Cria o Schema físico
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

        # 4. Popula o schema com as tabelas do schema_base.sql
        executar_schema(conn, schema)

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "ok", "schema": schema})

    except Exception as e:
        if conn: conn.close()
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    inicializar()
    app.run(debug=True)