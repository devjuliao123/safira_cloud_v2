from flask import Flask, request, jsonify, render_template, render_template_string
import psycopg2
import uuid
import re

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
            schema TEXT NOT NULL,
            qtd_usuarios_limite INT DEFAULT 1,
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
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Quantidade de Usuários</label>
                            <input type="number" id="qtd_usuarios" value="1" min="1"
                                class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all outline-none">
                        </div>
    """

    # Substituir campo original Nome da Unidade
    html = re.sub(r'<div>\s*<label[^>]*>Nome da Unidade</label>\s*<input[^>]*id="nome"[^>]*>\s*</div>', novos_campos, html, flags=re.DOTALL)

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

        // Sobrescrever listarOrgs para atualizar o próximo ID
        window.listarOrgs = async function() {
            const grid = document.getElementById("gridBody");
            grid.innerHTML = `<tr><td colspan="3" class="p-6 text-center text-slate-400 italic">Sincronizando...</td></tr>`;

            try {
                const res = await fetch("/organizacoes");
                const data = await res.json();

                grid.innerHTML = "";
                data.forEach(org => {
                    grid.innerHTML += `
                        <tr class="hover:bg-blue-50/50 transition-colors">
                            <td class="px-6 py-4 font-mono text-xs text-blue-600 font-semibold">${org.schema}</td>
                            <td class="px-6 py-4 text-sm font-medium text-slate-700">${org.nome}</td>
                            <td class="px-6 py-4">
                                <span class="flex items-center gap-1.5 text-emerald-600 text-xs font-bold">
                                    <span class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                                    ATIVO
                                </span>
                            </td>
                        </tr>
                    `;
                });
                document.getElementById("totalOrgs").innerText = `${data.length} Organizações`;
            } catch (e) {
                grid.innerHTML = `<tr><td colspan="3" class="p-8 text-center text-slate-400">Nenhum registro encontrado.</td></tr>`;
            }

            try {
                const r = await fetch("/proximo-id");
                const d = await r.json();
                if (d.sucesso) {
                    document.getElementById("numero_display").value = d.proximo;
                }
            } catch (e) {}
            lucide.createIcons();
        };

        // Sobrescrever função criar original
        window.criar = async function() {
            const btn = document.getElementById("btnCriar");
            const nome_org = document.getElementById("nome_org").value;
            const qtd_usuarios = document.getElementById("qtd_usuarios").value;
            const container = document.getElementById("statusContainer");

            if (!nome_org) {
                alert("Nome da organização é obrigatório.");
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
                        qtd_usuarios: parseInt(qtd_usuarios)
                    })
                });

                const data = await res.json();

                if (data.status === "ok") {
                    container.className = "mt-4 p-4 rounded-lg border bg-emerald-50 border-emerald-200 text-emerald-700 block";
                    document.getElementById("msgHeader").innerText = "Sucesso!";
                    document.getElementById("msgBody").innerText = `Organização ${data.schema} criada com sucesso.`;

                    document.getElementById("nome_org").value = "";
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
    qtd_usuarios = data.get("qtd_usuarios", 1)

    if not nome:
        return jsonify({"status": "erro", "mensagem": "Nome da organização é obrigatório"}), 400

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
            INSERT INTO public.tbl_organizacoes (numero, nome, schema, qtd_usuarios_limite)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (numero, nome, schema, qtd_usuarios))
        org_id = cur.fetchone()[0]

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
