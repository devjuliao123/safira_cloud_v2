CREATE TABLE tbl_empresas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(150),
    apelido_fantasia VARCHAR(150),
    cnpj VARCHAR(20),
    tipo_contribuinte INT,
    inscricao_estadual VARCHAR(30),
    inscricao_municipal VARCHAR(30),
    telefone VARCHAR(20),
    email VARCHAR(150),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    data_producao DATE,
    ativo BOOLEAN,
    criado_em TIMESTAMP
);

CREATE TABLE tbl_pessoas (
    id SERIAL PRIMARY KEY,
    tipo_pessoa VARCHAR(10),
    nome_razao VARCHAR(150),
    apelido_fantasia VARCHAR(150),
    cpf_cnpj VARCHAR(20),
    tipo_contribuinte INT,
    inscricao_estadual VARCHAR(30),
    telefone VARCHAR(20),
    email VARCHAR(150),
    cidade VARCHAR(100),
    estado VARCHAR(2),
    relacao_comercial VARCHAR(30),
    cargo VARCHAR(100),
    criado_em TIMESTAMP
);

CREATE TABLE tbl_pessoas_empresas (
    id SERIAL PRIMARY KEY,
    pessoa_id INT,
    empresa_id INT,
    ativo BOOLEAN
);

CREATE TABLE tbl_veiculos (
    id SERIAL PRIMARY KEY,
    pessoa_id INT,
    placa VARCHAR(10),
    marca VARCHAR(50),
    modelo VARCHAR(50),
    ano INT,
    cor VARCHAR(30),
    km INT
);

CREATE TABLE tbl_ordens_servico (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    pessoa_id INT,
    veiculo_id INT,
    status VARCHAR(20),
    descricao TEXT,
    km INT,
    criado_em TIMESTAMP
);

CREATE TABLE tbl_os_itens (
    id SERIAL PRIMARY KEY,
    os_id INT,
    tipo VARCHAR(10),
    produto_id INT,
    servico_id INT,
    quantidade INT,
    valor NUMERIC(10,2)
);

CREATE TABLE tbl_servicos_catalogo (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(150),
    valor_padrao NUMERIC(10,2)
);

CREATE TABLE tbl_servicos (
    id SERIAL PRIMARY KEY,
    os_id INT,
    servico_id INT,
    horas NUMERIC(5,2)
);

CREATE TABLE tbl_produtos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50),
    descricao VARCHAR(150),
    custo_unitario NUMERIC(10,2),
    custo_frete NUMERIC(10,2),
    custo_impostos NUMERIC(10,2),
    valor_venda NUMERIC(10,2)
);

CREATE TABLE tbl_estoque_saldos (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    produto_id INT,
    quantidade INT
);

CREATE TABLE tbl_estoque_movimentacoes (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    produto_id INT,
    tipo VARCHAR(10),
    quantidade INT,
    criado_em TIMESTAMP
);

CREATE TABLE tbl_compras (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    fornecedor_id INT,
    valor NUMERIC(10,2)
);

CREATE TABLE tbl_compra_itens (
    id SERIAL PRIMARY KEY,
    compra_id INT,
    produto_id INT,
    quantidade INT,
    valor NUMERIC(10,2)
);

CREATE TABLE tbl_contas_receber (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    pessoa_id INT,
    valor NUMERIC(10,2),
    vencimento DATE,
    status VARCHAR(20)
);

CREATE TABLE tbl_cartoes_receber (
    id SERIAL PRIMARY KEY,
    conta_receber_id INT,
    valor NUMERIC(10,2),
    data_prevista DATE
);

CREATE TABLE tbl_contas_pagar (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    fornecedor_id INT,
    valor NUMERIC(10,2),
    vencimento DATE
);

CREATE TABLE tbl_movimentacoes_financeiras (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    tipo VARCHAR(10),
    valor NUMERIC(10,2)
);

CREATE TABLE tbl_caixa (
    id SERIAL PRIMARY KEY,
    empresa_id INT,
    saldo NUMERIC(10,2)
);

CREATE TABLE tbl_entregas (
    id SERIAL PRIMARY KEY,
    os_id INT,
    data_entrega TIMESTAMP
);

CREATE TABLE tbl_garantias (
    id SERIAL PRIMARY KEY,
    os_id INT,
    descricao TEXT
);

-- =========================
-- TABELA DE LOG DO SISTEMA
-- =========================

CREATE TABLE tbl_logs_sistema (
    id SERIAL PRIMARY KEY,
    acao VARCHAR(100),
    entidade VARCHAR(100),
    entidade_id INT,
    descricao TEXT,
    usuario VARCHAR(150),
    ip VARCHAR(45),
    criado_em TIMESTAMP DEFAULT NOW()
);