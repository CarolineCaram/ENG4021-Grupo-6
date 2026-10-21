const form = document.getElementById("form-login");
const campoEmail = document.getElementById("email");
const campoSenha = document.getElementById("senha");
const mensagemErro = document.getElementById("mensagem-erro");
const botao = form.querySelector("button");

form.addEventListener("submit", async function (evento) {
  // Impede a página de recarregar quando o formulário é enviado
  evento.preventDefault();

  mensagemErro.textContent = "";
  botao.disabled = true;
  botao.textContent = "Entrando...";

  try {
    const resposta = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: campoEmail.value,
        senha: campoSenha.value
      })
    });

    const dados = await resposta.json();

    if (dados.ok) {
      window.location.href = "inicio.html";
    } else {
      mensagemErro.textContent = dados.erro;
    }
  } catch (erro) {
    mensagemErro.textContent = "Não foi possível conectar ao servidor.";
  }

  botao.disabled = false;
  botao.textContent = "Entrar";
});