from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Banco de dados simulado de Ordens de Serviço (OS)
ORDENS_DE_SERVICO = {
    "OS-1024": {"cliente": "João Silva", "aparelho": "iPhone 11", "status": "Aguardando Peça", "valor": "R$ 350,00"},
    "OS-1025": {"cliente": "Maria Souza", "aparelho": "Samsung A52", "status": "Pronto para Retirada", "valor": "R$ 180,00"},
    "OS-1026": {"cliente": "Carlos Oliveira", "aparelho": "Motorola G30", "status": "Em Análise Técnica", "valor": "R$ 120,00"},
}

# Rota principal - Carrega a página inicial do site
@app.route('/')
def home():
    return render_template('index.html')

# Rota de API para consultar a Ordem de Serviço via Python
@app.route('/api/consultar-os', methods=['POST'])
def consultar_os():
    dados = request.get_json()
    numero_os = dados.get('numero_os', '').strip().upper()

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

if __name__ == '__main__':
    app.run(debug=True)