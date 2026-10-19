import os
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'chave_secreta_lung_infocell'

# Configuração com a Porta 6543 (Connection Pooler do Supabase) para evitar o erro de rede no Render
db_url = 'postgresql+psycopg2://postgres:30515657Lu.%40@db.kuavbwwvjrnygegwnein.supabase.co:6543/postgres'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Função auxiliar para extrair apenas dígitos numéricos
def apenas_numeros(texto):
    if not texto:
        return ""
    return re.sub(r'\D', '', str(texto))


# --- MODELOS DO BANCO DE DADOS ---

class Tecnico(db.Model):
    __tablename__ = 'tecnicos'
    id = db.Column(db.Integer, primary_key=True)
    senha = db.Column(db.String(100), nullable=False, default="1234")


class OrdemServico(db.Model):
    __tablename__ = 'ordens_servico'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    cliente = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(30), nullable=False)
    endereco = db.Column(db.String(200), nullable=False)
    aparelho = db.Column(db.String(100), nullable=False)
    defeito = db.Column(db.String(200), nullable=False)
    relatorio = db.Column(db.Text, nullable=True)
    avarias = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Em Análise Técnica")
    valor = db.Column(db.String(50), nullable=False, default="A definir")


# Criar tabelas e registo inicial
with app.app_context():
    db.create_all()
    if not Tecnico.query.first():
        tecnico_padrao = Tecnico(senha="1234")
        db.session.add(tecnico_padrao)
        db.session.commit()


# --- ROTAS PRINCIPAIS ---

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        tecnico = Tecnico.query.first()
        senha_atual = tecnico.senha if tecnico else "1234"

        if senha_digitada == senha_atual:
            session['tecnico_logado'] = True
            return redirect(url_for('admin'))
        else:
            erro = "Senha incorreta! Tente novamente."

    return render_template('login.html', erro=erro)


@app.route('/logout')
def logout():
    session.pop('tecnico_logado', None)
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if not session.get('tecnico_logado'):
        return redirect(url_for('login'))

    ordens_bd = OrdemServico.query.order_by(OrdemServico.id.desc()).all()
    ordens_dict = {}
    for os_item in ordens_bd:
        ordens_dict[os_item.codigo] = {
            "cliente": os_item.cliente,
            "telefone": os_item.telefone,
            "endereco": os_item.endereco,
            "aparelho": os_item.aparelho,
            "defeito": os_item.defeito,
            "relatorio": os_item.relatorio,
            "avarias": os_item.avarias.split(", ") if os_item.avarias else [],
            "status": os_item.status,
            "valor": os_item.valor
        }

    return render_template('admin.html', ordens=ordens_dict)


@app.route('/api/criar-os', methods=['POST'])
def criar_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    dados = request.get_json()

    total_os = OrdemServico.query.count()
    codigo_os = f"OS-{1025 + total_os}"

    avarias_lista = dados.get('avarias', [])
    avarias_str = ", ".join(avarias_lista) if isinstance(avarias_lista, list) else str(avarias_lista)

    nova_os = OrdemServico(
        codigo=codigo_os,
        cliente=dados.get('cliente'),
        telefone=dados.get('telefone'),
        endereco=dados.get('endereco'),
        aparelho=dados.get('aparelho'),
        defeito=dados.get('defeito'),
        relatorio=dados.get('relatorio'),
        avarias=avarias_str,
        status=dados.get('status', 'Em Análise Técnica'),
        valor=dados.get('valor', 'A definir')
    )

    db.session.add(nova_os)
    db.session.commit()

    return jsonify({
        "sucesso": True,
        "mensagem": "Ordem de Serviço salva no banco de dados com sucesso!",
        "codigo_os": codigo_os
    })


@app.route('/api/atualizar-status-os', methods=['POST'])
def atualizar_status_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    dados = request.get_json()
    codigo_os = dados.get('codigo_os')
    novo_status = dados.get('novo_status')

    os_item = OrdemServico.query.filter_by(codigo=codigo_os).first()
    if os_item:
        os_item.status = novo_status
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": f"Status da {codigo_os} atualizado para: {novo_status}"})
    else:
        return jsonify({"sucesso": False, "mensagem": "OS não encontrada."}), 404


@app.route('/api/consultar-os', methods=['POST'])
def consultar_os():
    dados = request.get_json()
    numero_os = dados.get('numero_os', '').strip().upper()
    digitos_telefone = apenas_numeros(dados.get('digitos_telefone', ''))

    if not numero_os.startswith('OS-') and numero_os.isdigit():
        numero_os = f"OS-{numero_os}"

    if len(digitos_telefone) < 4:
        return jsonify({
            "sucesso": False,
            "mensagem": "Por favor, informe os 4 últimos dígitos do telefone do cliente."
        })

    os_item = OrdemServico.query.filter_by(codigo=numero_os).first()

    if os_item:
        telefone_cadastrado_limpo = apenas_numeros(os_item.telefone)
        ultimos_4_cadastrados = telefone_cadastrado_limpo[-4:] if len(telefone_cadastrado_limpo) >= 4 else ""
        ultimos_4_digitados = digitos_telefone[-4:]

        if ultimos_4_cadastrados and ultimos_4_digitados == ultimos_4_cadastrados:
            return jsonify({
                "sucesso": True,
                "mensagem": f"Aparelho: {os_item.aparelho} | Status: {os_item.status} | Valor: {os_item.valor}"
            })
        else:
            return jsonify({
                "sucesso": False,
                "mensagem": "Os 4 últimos dígitos do telefone não conferem com esta OS."
            })
    else:
        return jsonify({
            "sucesso": False,
            "mensagem": "Ordem de Serviço não encontrada. Verifique os dados digitados."
        })


@app.route('/api/alterar-senha', methods=['POST'])
def alterar_senha():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    dados = request.get_json()
    senha_atual = dados.get('senha_atual')
    nova_senha = dados.get('nova_senha')

    tecnico = Tecnico.query.first()
    if not tecnico:
        tecnico = Tecnico(senha="1234")
        db.session.add(tecnico)

    if senha_atual != tecnico.senha:
        return jsonify({"sucesso": False, "mensagem": "A senha atual está incorreta."})

    if not nova_senha or len(nova_senha.strip()) < 3:
        return jsonify({"sucesso": False, "mensagem": "A nova senha deve ter pelo menos 3 caracteres."})

    tecnico.senha = nova_senha.strip()
    db.session.commit()

    return jsonify({"sucesso": True, "mensagem": "Senha alterada com sucesso!"})


if __name__ == '__main__':
    app.run(debug=True)