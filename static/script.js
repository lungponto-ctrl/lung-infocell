function enviarMensagem(event) {
    event.preventDefault();

    // Captura os valores dos campos e remove espaços extras nas pontas
    const nome = document.getElementById('nome').value.trim();
    const telefone = document.getElementById('telefone').value.trim();
    const aparelho = document.getElementById('aparelho').value.trim();
    const defeito = document.getElementById('defeito').value.trim();

    // Número real da Lung InfoCell (com código do país 55 + DDD 31)
    const numeroWhatsApp = "5531972148479";

    // Monta a mensagem formatada para o WhatsApp
    const mensagem = `Olá! Gostaria de um orçamento na *Lung InfoCell*:\n\n` +
                     `👤 *Nome:* ${nome}\n` +
                     `📞 *Telefone:* ${telefone}\n` +
                     `📱 *Aparelho:* ${aparelho}\n` +
                     `🛠️ *Defeito/Serviço:* ${defeito}`;

    // Cria a URL oficial do WhatsApp
    const url = `https://wa.me/${numeroWhatsApp}?text=${encodeURIComponent(mensagem)}`;

    // Abre o WhatsApp numa nova aba/separador
    window.open(url, '_blank');
}