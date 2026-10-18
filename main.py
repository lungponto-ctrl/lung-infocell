from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'chave_secreta_lung_infocell'

# Senha inicial do técnico (pode ser alterada direto pelo painel admin)
SENHA_TECNICO = "1234"

# Banco de dados simulado de Ordens de Serviço (OS)
ORDENS_DE_SERVICO = {
    "OS-1024": {
        "cliente": "João Silva",
        "telefone": "(31) 99999-1111",
        "endereco": "Rua das Flores, 123 - Betim",
        "aparelho": "iPhone 11",
        "defeito": "Tela quebrada",
        "relatorio": "Necessária troca de frontal display completa.",
        "avarias": ["Tela trincada / arranhada", "Marcas na carcaça"],
        "status": "Aguardando Peça",
        "valor": "R$ 350,00"
    }
}

contador_os = 1025


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        senha_digitada = request.form.get('senha')
        if senha_digitada == SENHA_TECNICO:
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
    return render_template('admin.html', ordens=ORDENS_DE_SERVICO)


@app.route('/api/criar-os', methods=['POST'])
def criar_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    global contador_os
    dados = request.get_json()

    codigo_os = f"OS-{contador_os}"

    ORDENS_DE_SERVICO[codigo_os] = {
        "cliente": dados.get('cliente'),
        "telefone": dados.get('telefone'),
        "endereco": dados.get('endereco'),
        "aparelho": dados.get('aparelho'),
        "defeito": dados.get('defeito'),
        "relatorio": dados.get('relatorio'),
        "avarias": dados.get('avarias', []),
        "status": dados.get('status', 'Em Análise Técnica'),
        "valor": dados.get('valor', 'A definir')
    }

    contador_os += 1

    return jsonify({
        "sucesso": True,
        "mensagem": "Ordem de Serviço criada com sucesso!",
        "codigo_os": codigo_os
    })


@app.route('/api/atualizar-status-os', methods=['POST'])
def atualizar_status_os():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    dados = request.get_json()
    codigo_os = dados.get('codigo_os')
    novo_status = dados.get('novo_status')

    if codigo_os in ORDENS_DE_SERVICO:
        ORDENS_DE_SERVICO[codigo_os]['status'] = novo_status
        return jsonify({"sucesso": True, "mensagem": f"Status da {codigo_os} atualizado para: {novo_status}"})
    else:
        return jsonify({"sucesso": False, "mensagem": "OS não encontrada."}), 404


@app.route('/api/consultar-os', methods=['POST'])
def consultar_os():
    dados = request.get_json()
    numero_os = dados.get('numero_os', '').strip().upper()

    if not numero_os.startswith('OS-') and numero_os.isdigit():
        numero_os = f"OS-{numero_os}"

    if numero_os in ORDENS_DE_SERVICO:
        info = ORDENS_DE_SERVICO[numero_os]
        return jsonify({
            "sucesso": True,
            "mensagem": f"Aparelho: {info['aparelho']} | Status: {info['status']} | Valor: {info['valor']}"
        })
    else:
        return jsonify({
            "sucesso": False,
            "mensagem": "Ordem de Serviço não encontrada. Verifique o número digitado."
        })


@app.route('/api/alterar-senha', methods=['POST'])
def alterar_senha():
    if not session.get('tecnico_logado'):
        return jsonify({"sucesso": False, "mensagem": "Acesso não autorizado."}), 403

    global SENHA_TECNICO
    dados = request.get_json()
    senha_atual = dados.get('senha_atual')
    nova_senha = dados.get('nova_senha')

    if senha_atual != SENHA_TECNICO:
        return jsonify({"sucesso": False, "mensagem": "A senha atual está incorreta."})

    if not nova_senha or len(nova_senha.strip()) < 3:
        return jsonify({"sucesso": False, "mensagem": "A nova senha deve ter pelo menos 3 caracteres."})

    SENHA_TECNICO = nova_senha.strip()
    return jsonify({"sucesso": True, "mensagem": "Senha alterada com sucesso!"})


if __name__ == '__main__':
    app.run(debug=True)