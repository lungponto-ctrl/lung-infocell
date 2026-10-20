import os
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'chave_secreta_bancadapro_saas'

# Configuração da Base de Dados
database_url = os.environ.get("DATABASE_URL")

if database_url:
    database_url = database_url.strip().strip('"').strip("'")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lung_infocell.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


def apenas_numeros(texto):
    if not texto:
        return ""
    return re.sub(r'\D', '', str(texto))


def validar_senha_forte(senha):
    """
    Exige:
    - Mínimo de 8 caracteres
    - Pelo menos uma letra maiúscula
    - Pelo menos uma letra minúscula
    - Pelo menos um número
    - Pelo menos um caractere especial (ex: @, #, $, !, etc.)
    """
    if not senha or len(senha) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    if not re.search(r'[A-Z]', senha):
        return False, "A senha deve conter pelo menos uma letra maiúscula."
    if not re.search(r'[a-z]', senha):
        return False, "A senha deve conter pelo menos uma letra minúscula."
    if not re.search(r'[0-9]', senha):
        return False, "A senha deve conter pelo menos um número."
    if not re.search(r'[^A-Za-z0-9]', senha):
        return False, "A senha deve conter pelo menos um caractere especial (ex: @, #, $, !, etc.)."
    return True, ""


# --- MODELOS DO BANCO DE DADOS ---

class Empresa(db.Model):
    __tablename__ = 'empresas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    telefone_whatsapp = db.Column(db.String(30), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    horario = db.Column(db.String(100), nullable=True)
    cor_primaria = db.Column(db.String(20), nullable=False, default="#ff3b30")
    servicos = db.Column(db.Text, nullable=True, default="tela_bateria,conector,computadores,acessorios")
    ativo = db.Column(db.Boolean, nullable=False, default=False)

    tecnicos = db.relationship('Tecnico', backref='empresa', lazy=True)
    ordens = db.relationship('OrdemServico', backref='empresa', lazy=True)
    clientes = db.relationship('Cliente', backref='empresa', lazy=True)


class Tecnico(db.Model):
    __tablename__ = 'tecnicos'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, default=1)
    usuario = db.Column(db.String(50), nullable=True, default="admin")
    senha = db.Column(db.String(100), nullable=False, default="Admin@2026")


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    endereco = db.Column(db.String(200), nullable=True)


class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'
    id = db.Column(db.Integer, primary_key=True)
    empresa_id = db.Column(db.Integer, db.ForeignKey('empresas.id'), nullable=False, default=1)
    codigo = db.Column(db.String(20), nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    aparelho = db.Column(db.String(100), nullable=False)
    defeito = db.Column(db.String(200), nullable=False)
    relatorio = db.Column(db.Text, nullable=True)
    avarias = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Em Análise Técnica")
    valor = db.Column(db.String(50), nullable=False, default="A definir")


# --- MIGRAÇÃO AUTOMÁTICA E INICIALIZAÇÃO ---
with app.app_context():
    db.create_all()

    colunas_migrar = [
        ("empresas", "ativo", "BOOLEAN DEFAULT 0"),
        ("tecnicos", "empresa_id", "INTEGER DEFAULT 1"),
        ("tecnicos", "usuario", "VARCHAR(50) DEFAULT 'admin'"),
        ("ordens_servico", "empresa_id", "INTEGER DEFAULT 1"),
        ("ordens_servico", "relatorio", "TEXT"),
        ("ordens_servico", "avarias", "TEXT"),
        ("ordens_servico", "status", "VARCHAR(50) DEFAULT 'Em Análise Técnica'"),
        ("ordens_servico", "valor", "VARCHAR(50) DEFAULT 'A definir'"),
        ("clientes", "empresa_id", "INTEGER DEFAULT 1"),
        ("clientes", "endereco", "VARCHAR(200)")
    ]

    for tabela, coluna, tipo in colunas_migrar:
        try:
            db.session.execute(db.text(f"ALTER TABLE {tabela} ADD COLUMN IF NOT EXISTS {coluna} {tipo}"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    empresa_padrao = Empresa.query.filter_by(id=1).first()
    if not empresa_padrao:
        empresa_padrao = Empresa(
            id=1,
            nome="Lung InfoCell",
            slug="lung-infocell",
            telefone_whatsapp="5531972148479",
            endereco="Rua Olga Assunção, 1212 - Novo Horizonte, Betim - MG",
            horario="Seg a Sex: 08:00 - 18:00 | Sáb: 08:00 - 12:00",
            cor_primaria="#ff3b30",
            servicos="tela_bateria,conector,computadores,acessorios",
            ativo=True
        )
        db.session.add(empresa_padrao)
        db.session.commit()
    else:
        if not empresa_padrao.ativo:
            empresa_padrao.ativo = True
            db.session.commit()

    tecnico = Tecnico.query.filter_by(empresa_id=1).first()
    if not tecnico:
        db.session.add(Tecnico(empresa_id=1, usuario="admin", senha="Admin@2026"))
        db.session.commit()
    else:
        tecnico.senha = "Admin@2026"
        db.session.commit()


def get_empresa_atual():
    empresa_id = session.get('empresa_id', 1)
    return Empresa.query.get(empresa_id)


# --- ROTAS PRINCIPAIS & AUTOATENDIMENTO ---

@app.route('/')
def home():
    empresa = get_empresa_atual()
    if not empresa or not empresa.ativo:
        return redirect(url_for('cadastro_loja'))
    return render_template('index.html', empresa=empresa)


@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro_loja():
    if request.method == 'POST':
        dados = request.get_json() or {}
        nome = dados.get('nome')

        slug_raw = dados.get('slug', '')
        slug = re.sub(r'[^a-zA-Z0-9]', '-', slug_raw.lower()).strip('-')

        telefone = dados.get('telefone')
        endereco = dados.get('endereco')
        cor_primaria = dados.get('cor_primaria', '#ff3b30')

        servicos_lista = dados.get('servicos', [])
        servicos_str = ",".join(servicos_lista) if isinstance(servicos_lista, list) else str(servicos_lista)

        senha_tecnico = dados.get('senha_tecnico', '')

        valida, mensagem_erro = validar_senha_forte(senha_tecnico)
        if not valida:
            return jsonify({"sucesso": False, "mensagem": f"Senha fraca: {mensagem_erro}"})

        if not slug:
            return jsonify({"sucesso": False, "mensagem": "O identificador (slug) é inválido!"})

        if Empresa.query.filter_by(slug=slug).first():
            return jsonify(
                {"sucesso": False, "mensagem": "Já existe uma loja com esse identificador (slug). Escolha outro."})

        nova_empresa = Empresa(
            nome=nome,
            slug=slug,
            telefone_whatsapp=telefone,
            endereco=endereco,
            cor_primaria=cor_primaria,
            servicos=servicos_str,
            ativo=False
        )
        db.session.add(nova_empresa)
        db.session.commit()

        novo_tecnico = Tecnico(
            empresa_id=nova_empresa.id,
            senha=senha_tecnico
        )
        db.session.add(novo_tecnico)
        db.session.commit()

        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso! Sua loja está aguardando liberação do pagamento para ser ativada.",
            "slug": slug
        })

    return render_template('cadastro.html')


@app.route('/loja/<slug>')
def home_loja(slug):
    empresa = Empresa.query.filter(db.func.lower(Empresa.slug) == slug.lower()).first_or_404()

    if not empresa.ativo:
        return render_template('aguardando_ativacao.html', empresa=empresa)

    session['empresa_id'] = empresa.id
    return render_template('index.html', empresa=empresa)


@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    empresa_id_sessao = session.get('empresa_id', 1)
    empresa = Empresa.query.get(empresa_id_sessao)

    if empresa and not empresa.ativo:
        return render_template('aguardando_ativacao.html', empresa=empresa)

    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        tecnico = Tecnico.query.filter_by(empresa_id=empresa_id_sessao, senha=senha_digitada).first()

        if not tecnico:
            tecnico = Tecnico.query.filter_by(senha=senha_digitada).first()

        if tecnico:
            empresa_tec = Empresa.query.get(tecnico.empresa_id)
            if not empresa_tec.ativo:
                erro = "Esta loja está pendente de ativação/pagamento. Entre em contato com o suporte."
            else:
                session['tecnico_logado'] = True
                session['empresa_id'] = tecnico.empresa_id
                return redirect(url_for('admin'))
        else:
            erro = "Senha incorreta! Tente novamente."

    return render_template('login.html', erro=erro, empresa=empresa)


@app.route('/logout')
def logout():
    session.pop('tecnico_logado', None)
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if not session.get('tecnico_logado'):
        return redirect(url_for('login'))

    empresa_id = session.get('empresa_id', 1)
    empresa = Empresa.query.get(empresa_id)

    if not empresa.ativo:
        return render_template('aguardando_ativacao.html', empresa=empresa)

    ordens_bd = OrdemServico.query.filter_by(empresa_id=empresa_id).order_by(OrdemServico.id.desc()).all()

    faturamento_total = 0.0
    os_abertas = 0
    os_concluidas = 0

    ordens_dict = {}
    for os_item in ordens_bd:
        if os_item.status in ["Pronto para Retirada", "Entregue"]:
            os_concluidas += 1
        else:
            os_abertas += 1

        val_str = str(os_item.valor or "").lower()
        if "definir" not in val_str and val_str.strip():
            limpo = val_str.replace("r$", "").replace(" ", "").replace(".", "").replace(",", ".")
            limpo_num = re.sub(r'[^0-9.]', '', limpo)
            try:
                faturamento_total += float(limpo_num)
            except ValueError:
                pass

        if os_item.avarias:
            avarias_lista = [a.strip() for a in os_item.avarias.split(",") if a.strip()] if isinstance(os_item.avarias,
                                                                                                       str) else os_item.avarias
        else:
            avarias_lista = []

        ordens_dict[os_item.codigo] = {
            "cliente": os_item.cliente,
            "telefone": os_item.telefone,
            "endereco": os_item.endereco,
            "aparelho": os_item.aparelho,
            "defeito": os_item.defeito,
            "relatorio": os_item.relatorio or "",
            "avarias": avarias_lista,
            "status": os_item.status,
            "valor": os_item.valor
        }

    ticket_medio = (faturamento_total / os_concluidas) if os_concluidas > 0 else 0.0

    metricas = {
        "faturamento": f"R$ {faturamento_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "ticket_medio": f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        "os_abertas": os_abertas,
        "os_concluidas": os_concluidas,
        "total_os": len(ordens_bd)
    }

    return render_template('admin.html', ordens=ordens_dict, empresa=empresa, metricas=metricas)


# --- ROTAS DE API DA OS E CLIENTES ---

@app.route('/api/buscar-cliente', methods=['POST'])
def buscar_cliente():
    if not session.get('tecnico_logado'):
        return jsonify({"encontrado": False}), 403
    empresa_id = session.get('empresa_id', 1)
    dados = request.get_json() or {}
    telefone = apenas_numeros(dados.get('telefone', ''))
    if len(telefone) < 4:
        return jsonify({"encontrado": False})

    clientes = Cliente.query.filter_by(empresa_id=empresa_id).all()
    for c in clientes:
        if apenas_numeros(c.telefone) == telefone or telefone in apenas_numeros(c.telefone):
            return jsonify({
                "encontrado": True,
                "nome": c.nome,
                "telefone": c.telefone,
                "endereco": c.endereco or ""
            })
    return jsonify({"encontrado": False})


def salvar_ou_atualizar_cliente(empresa_id, nome, telefone, endereco):
    cli = Cliente.query.filter_by(empresa_id=empresa_id, telefone=telefone).first()
    if not cli:
        novo = Cliente(empresa_id=empresa_id, nome=nome, telefone=telefone, endereco=endereco)
        db.session.add(novo)
    else:
        cli.nome = nome
        cli.endereco = endereco or cli.endereco
    db.session.commit()


@app.route('/api/criar-os', methods=['POST'])
def criar_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    empresa_id = session.get('empresa_id', 1)
    dados = request.get_json() or {}

    nome_cliente = dados.get('cliente')
    tel_cliente = dados.get('telefone')
    aparelho = dados.get('aparelho')
    defeito = dados.get('defeito')

    if not nome_cliente or not tel_cliente or not aparelho or not defeito:
        return jsonify({"sucesso": False,
                        "mensagem": "Preencha todos os campos obrigatórios (Cliente, Telefone, Aparelho e Defeito)."}), 400

    # Busca a última OS cadastrada DESSA EMPRESA específica para pegar o número mais alto com segurança
    ultima_os_empresa = OrdemServico.query.filter_by(empresa_id=empresa_id).order_by(OrdemServico.id.desc()).first()

    if ultima_os_empresa and ultima_os_empresa.codigo.startswith('OS-'):
        try:
            num_atual = int(ultima_os_empresa.codigo.replace('OS-', ''))
            proximo_num = num_atual + 1
        except ValueError:
            proximo_num = 1026
    else:
        proximo_num = 1026

    codigo_os = f"OS-{proximo_num}"

    # Loop de segurança extrema caso o número já exista por algum motivo na base
    while OrdemServico.query.filter_by(empresa_id=empresa_id, codigo=codigo_os).first():
        proximo_num += 1
        codigo_os = f"OS-{proximo_num}"

    avarias_lista = dados.get('avarias', [])
    avarias_str = ", ".join(avarias_lista) if isinstance(avarias_lista, list) else str(avarias_lista)
    end_cliente = dados.get('endereco', '')

    try:
        nova_os = OrdemServico(
            empresa_id=empresa_id,
            codigo=codigo_os,
            cliente=nome_cliente,
            telefone=tel_cliente,
            endereco=end_cliente,
            aparelho=aparelho,
            defeito=defeito,
            relatorio=dados.get('relatorio', ''),
            avarias=avarias_str,
            status=dados.get('status', 'Em Análise Técnica'),
            valor=dados.get('valor', 'A definir')
        )
        db.session.add(nova_os)
        db.session.commit()

        salvar_ou_atualizar_cliente(empresa_id, nome_cliente, tel_cliente, end_cliente)

        return jsonify({"sucesso": True, "mensagem": "Ordem de Serviço salva com sucesso!", "codigo_os": codigo_os})
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "mensagem": f"Erro ao criar OS no banco de dados: {str(e)}"}), 500


@app.route('/api/consultar-os', methods=['POST'])
def consultar_os():
    dados = request.get_json() or {}
    empresa_id = session.get('empresa_id', 1)
    numero_os = str(dados.get('numero_os') or dados.get('codigo_os') or '').strip().upper()
    digitos_telefone = apenas_numeros(dados.get('digitos_telefone') or dados.get('telefone') or '')

    if not numero_os:
        return jsonify({"sucesso": False, "mensagem": "Informe o número da OS."})

    if not numero_os.startswith('OS-') and numero_os.isdigit():
        numero_os_formatado = f"OS-{numero_os}"
    else:
        numero_os_formatado = numero_os

    os_item = OrdemServico.query.filter(
        OrdemServico.empresa_id == empresa_id,
        (OrdemServico.codigo == numero_os_formatado) | (OrdemServico.codigo == numero_os)
    ).first()

    if not os_item:
        return jsonify({"sucesso": False, "mensagem": "Ordem de Serviço não encontrada."})

    telefone_cadastrado_limpo = apenas_numeros(os_item.telefone)
    ultimos_4_cadastrados = telefone_cadastrado_limpo[-4:] if len(telefone_cadastrado_limpo) >= 4 else ""

    if ultimos_4_cadastrados and digitos_telefone[-4:] == ultimos_4_cadastrados:
        return jsonify({
            "sucesso": True, "codigo": os_item.codigo, "cliente": os_item.cliente,
            "aparelho": os_item.aparelho, "defeito": os_item.defeito, "status": os_item.status,
            "valor": os_item.valor, "relatorio": os_item.relatorio or "Em avaliação",
            "mensagem": f"Aparelho: {os_item.aparelho} | Status: {os_item.status}"
        })
    else:
        return jsonify({"sucesso": False, "mensagem": "Os 4 últimos dígitos do telefone não conferem."})


@app.route('/api/editar-os', methods=['POST'])
def editar_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado."}), 403
    empresa_id = session.get('empresa_id', 1)
    dados = request.get_json()
    os_item = OrdemServico.query.filter_by(codigo=dados.get('codigo_os'), empresa_id=empresa_id).first()
    if not os_item:
        return jsonify({"sucesso": False, "mensagem": "OS não encontrada."}), 404

    avarias_lista = dados.get('avarias', [])
    os_item.cliente = dados.get('cliente', os_item.cliente)
    os_item.telefone = dados.get('telefone', os_item.telefone)
    os_item.endereco = dados.get('endereco', os_item.endereco)
    os_item.aparelho = dados.get('aparelho', os_item.aparelho)
    os_item.defeito = dados.get('defeito', os_item.defeito)
    os_item.relatorio = dados.get('relatorio', os_item.relatorio)
    os_item.avarias = ", ".join(avarias_lista) if isinstance(avarias_lista, list) else str(avarias_lista)
    os_item.status = dados.get('status', os_item.status)
    os_item.valor = dados.get('valor', os_item.valor)
    db.session.commit()

    salvar_ou_atualizar_cliente(empresa_id, os_item.cliente, os_item.telefone, os_item.endereco)

    return jsonify({"sucesso": True, "mensagem": "Ordem atualizada com sucesso!"})


@app.route('/api/excluir-os', methods=['POST'])
def excluir_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado."}), 403
    empresa_id = session.get('empresa_id', 1)
    os_item = OrdemServico.query.filter_by(codigo=request.get_json().get('codigo_os'), empresa_id=empresa_id).first()
    if not os_item:
        return jsonify({"sucesso": False, "mensagem": "OS não encontrada."}), 404
    db.session.delete(os_item)
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "OS excluída com sucesso!"})


@app.route('/api/mudar-senha', methods=['POST'])
def mudar_senha():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado."}), 403

    empresa_id = session.get('empresa_id', 1)
    dados = request.get_json() or {}
    senha_atual = dados.get('senha_atual')
    nova_senha = dados.get('nova_senha')

    if not senha_atual or not nova_senha:
        return jsonify({"sucesso": False, "mensagem": "Preencha todos os campos de senha."})

    valida, mensagem_erro = validar_senha_forte(nova_senha)
    if not valida:
        return jsonify({"sucesso": False, "mensagem": f"Nova senha inválida: {mensagem_erro}"})

    tecnico = Tecnico.query.filter_by(empresa_id=empresa_id, senha=senha_atual).first()
    if not tecnico:
        tecnico = Tecnico.query.filter_by(senha=senha_atual).first()

    if tecnico:
        tecnico.senha = nova_senha
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Senha alterada com sucesso!"})
    else:
        return jsonify({"sucesso": False, "mensagem": "A senha atual está incorreta."})


# --- SUPER ADMIN (SENHA MESTRE VIA VARIÁVEL DE AMBIENTE) ---

@app.route('/super-admin', methods=['GET', 'POST'])
def super_admin():
    SUPER_SENHA_MESTRE = os.environ.get("SUPER_ADMIN_SENHA", "Pro@2026Master!")
    if request.method == 'POST':
        if request.form.get('senha_mestre') == SUPER_SENHA_MESTRE:
            session['super_logado'] = True
            return redirect(url_for('super_painel'))
        else:
            return render_template('super_login.html', erro="Senha Mestre incorreta!")
    return render_template('super_login.html')


@app.route('/super/painel')
def super_painel():
    if not session.get('super_logado'):
        return redirect(url_for('super_admin'))
    empresas = Empresa.query.all()
    return render_template('super_painel.html', empresas=empresas)


@app.route('/super/criar-loja', methods=['POST'])
def super_criar_loja():
    if not session.get('super_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado"}), 403
    dados = request.get_json() or {}
    slug = re.sub(r'[^a-zA-Z0-9]', '-', dados.get('slug', '').lower()).strip('-')

    senha_tec = dados.get('senha_tecnico', '')
    valida, msg = validar_senha_forte(senha_tec)
    if not valida:
        return jsonify({"sucesso": False, "mensagem": f"Senha do técnico fraca: {msg}"})

    if Empresa.query.filter_by(slug=slug).first():
        return jsonify({"sucesso": False, "mensagem": "Já existe uma loja com este slug."})

    servicos_lista = dados.get('servicos', [])
    servicos_str = ",".join(servicos_lista) if isinstance(servicos_lista, list) else str(servicos_lista)

    nova = Empresa(
        nome=dados.get('nome'),
        slug=slug,
        telefone_whatsapp=dados.get('telefone'),
        endereco=dados.get('endereco'),
        cor_primaria=dados.get('cor_primaria', '#ff3b30'),
        servicos=servicos_str,
        ativo=True
    )
    db.session.add(nova)
    db.session.commit()

    db.session.add(Tecnico(empresa_id=nova.id, senha=senha_tec))
    db.session.commit()

    return jsonify({"sucesso": True, "mensagem": "Loja criada e ativada com sucesso!"})


@app.route('/super/editar-loja', methods=['POST'])
def super_editar_loja():
    if not session.get('super_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado"}), 403
    dados = request.get_json() or {}
    empresa = Empresa.query.get(dados.get('id'))
    if not empresa:
        return jsonify({"sucesso": False, "mensagem": "Loja não encontrada."}), 404

    nova_senha = dados.get('senha_tecnico')
    if nova_senha:
        valida, msg = validar_senha_forte(nova_senha)
        if not valida:
            return jsonify({"sucesso": False, "mensagem": f"Nova senha fraca: {msg}"})

        tec = Tecnico.query.filter_by(empresa_id=empresa.id).first()
        if tec:
            tec.senha = nova_senha
            db.session.commit()

    servicos_lista = dados.get('servicos', [])
    empresa.nome = dados.get('nome', empresa.nome)
    empresa.telefone_whatsapp = dados.get('telefone', empresa.telefone_whatsapp)
    empresa.endereco = dados.get('endereco', empresa.endereco)
    empresa.cor_primaria = dados.get('cor_primaria', empresa.cor_primaria)
    empresa.servicos = ",".join(servicos_lista) if isinstance(servicos_lista, list) else str(servicos_lista)
    db.session.commit()

    return jsonify({"sucesso": True, "mensagem": "Loja atualizada com sucesso!"})


@app.route('/super/ativar-loja', methods=['POST'])
def super_ativar_loja():
    if not session.get('super_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado"}), 403

    dados = request.get_json() or {}
    loja_id = dados.get('id')

    if not loja_id:
        return jsonify({"sucesso": False, "mensagem": "ID da loja não fornecido."}), 400

    empresa = Empresa.query.get(int(loja_id))
    if empresa:
        empresa.ativo = not empresa.ativo
        db.session.commit()
        status_txt = "ativada com sucesso" if empresa.ativo else "suspensa com sucesso"
        return jsonify({"sucesso": True, "mensagem": f"Loja '{empresa.nome}' foi {status_txt}!"})

    return jsonify({"sucesso": False, "mensagem": "Loja não encontrada."}), 404


@app.route('/super/excluir-loja', methods=['POST'])
def super_excluir_loja():
    if not session.get('super_logado'):
        return jsonify({"sucesso": False, "mensagem": "Não autorizado"}), 403
    loja_id = request.get_json().get('id')
    if loja_id == 1:
        return jsonify({"sucesso": False, "mensagem": "Não é permitido excluir a matriz."}), 400
    empresa = Empresa.query.get(loja_id)
    if empresa:
        Tecnico.query.filter_by(empresa_id=loja_id).delete()
        OrdemServico.query.filter_by(empresa_id=loja_id).delete()
        Cliente.query.filter_by(empresa_id=loja_id).delete()
        db.session.delete(empresa)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Loja excluída com sucesso!"})
    return jsonify({"sucesso": False, "mensagem": "Loja não encontrada."}), 404


@app.route('/super/logout')
def super_logout():
    session.pop('super_logado', None)
    return redirect(url_for('super_admin'))


if __name__ == '__main__':
    app.run(debug=True)