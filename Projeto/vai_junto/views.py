from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from vai_junto.models import Usuario, Rota, Grupo, Carona, Instituicao


# ---------------------------------------------------------------
# Ajuda: descobre quem está logado (guardamos o id na sessão)
# ---------------------------------------------------------------
def usuario_logado(request):
    uid = request.session.get('usuario_id')
    if uid:
        return Usuario.objects.filter(id_usuario=uid).first()
    return None


def home(request):
    # Tela inicial = landing page do Vaijunto
    return render(request, 'Tela_Login.html',
                  {'usuario_logado': usuario_logado(request)})


def login_view(request):
    '''GET mostra a tela. POST confere e-mail e senha e abre a sessão.'''
    if usuario_logado(request):
        return redirect('rotas')

    erro = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '')
        usuario = Usuario.objects.filter(email__iexact=email).first()
        if usuario and check_password(senha, usuario.senha):
            request.session['usuario_id'] = usuario.id_usuario
            return redirect('rotas')
        erro = 'E-mail ou senha incorretos.'
    # tela de login de verdade
    return render(request, 'Pagina_Inicio.html', {'erro': erro})


def logout_view(request):
    if request.method == 'POST':
        request.session.flush()
    return redirect('home')


def recuperar_senha(request):
    return render(request, 'recuperar_senha.html')

def verificacao(request):
    return render(request, 'verificacao.html')

def como_funciona(request):
    return render(request, 'como_funciona.html')

def mapa(request):
    return render(request, 'mapa.html')

def reportar_problema(request):
    return render(request, 'reportar_problema.html')

def cadastrar_veiculo(request):
    return render(request, 'cadastrar_veiculo.html')

def cadastro_meio_transporte(request):
    return render(request, 'cadastromeiotransporte.html')

def oferecer_carona(request):
    usuario = usuario_logado(request)
    if not usuario:
        return redirect('login')

    erro = None
    if request.method == 'POST':
        dados = request.POST
        origem = dados.get('origem', '').strip()
        instituicao_id = dados.get('instituicao', '')
        horario_texto = dados.get('horario', '')
        vagas_texto = dados.get('vagas', '')
        instituicao = (
            Instituicao.objects.filter(pk=instituicao_id).first()
            if instituicao_id.isdigit() else None
        )

        try:
            horario = datetime.strptime(horario_texto, '%H:%M').time()
        except ValueError:
            horario = None

        try:
            vagas = int(vagas_texto)
        except (TypeError, ValueError):
            vagas = 0

        if not origem:
            erro = 'Informe o ponto de origem.'
        elif not instituicao:
            erro = 'Selecione uma instituição válida.'
        elif not horario:
            erro = 'Informe um horário válido.'
        elif not 1 <= vagas <= 8:
            erro = 'Informe entre 1 e 8 vagas.'
        elif dados.get('transporte') not in {'Carro', 'Moto', 'Van'}:
            erro = 'Selecione um meio de transporte válido.'
        else:
            Rota.objects.create(
                id_usuario=usuario,
                id_instituicao=instituicao,
                origem=origem,
                referencia=dados.get('referencia', '').strip() or None,
                horario=horario,
                transporte=dados.get('transporte', 'Carro'),
                vagas=vagas,
            )
            return redirect('rotas')

    return render(request, 'OferecerCarona.html', {
        'erro': erro,
        'dados': request.POST,
        'instituicoes': Instituicao.objects.all(),
    })


def cadastro(request):
    '''GET mostra o formulário. POST cria o usuário (e a rota, se vier preenchida)
    e já deixa o usuário logado.'''
    erro = None
    if request.method == 'POST':
        d = request.POST
        nome = d.get('nome', '').strip()
        email = d.get('email', '').strip().lower()
        matricula = d.get('matricula', '').strip()
        senha = d.get('senha', '')
        confirmar = d.get('confirmar', senha)   # se o seu HTML não tiver "confirmar", ignora

        if not nome or not email or not matricula:
            erro = 'Preencha nome, e-mail e matrícula.'
        elif len(senha) < 8:
            erro = 'A senha precisa ter pelo menos 8 caracteres.'
        elif senha != confirmar:
            erro = 'As senhas não conferem.'
        elif Usuario.objects.filter(email__iexact=email).exists():
            erro = 'Este e-mail já está cadastrado.'
        elif Usuario.objects.filter(matricula=matricula).exists():
            erro = 'Esta matrícula já está cadastrada.'
        else:
            usuario = Usuario.objects.create(nome=nome, email=email, matricula=matricula,
                                             senha=make_password(senha))

            # Etapas "Minha rota" e "Meio de transporte": só cria a Rota se vierem preenchidas
            inst_id = d.get('instituicao', '')
            instituicao = Instituicao.objects.filter(pk=inst_id).first() if inst_id.isdigit() else None
            origem = d.get('origem', '').strip()
            try:
                horario = datetime.strptime(d.get('horario', ''), '%H:%M').time()
            except ValueError:
                horario = None
            if instituicao and origem and horario:
                vagas = d.get('vagas', '')
                extra = {}
                if any(f.name == 'dias' for f in Rota._meta.get_fields()):   # só se você criou o campo "dias"
                    extra['dias'] = ','.join(d.getlist('dias'))
                Rota.objects.create(
                    id_usuario=usuario, id_instituicao=instituicao, origem=origem,
                    referencia=d.get('referencia', '').strip() or None,
                    horario=horario, transporte=d.get('transporte', '') or 'passageiro',
                    vagas=int(vagas) if vagas.isdigit() else 0, **extra)

            request.session['usuario_id'] = usuario.id_usuario
            return redirect('rotas')

    return render(request, 'cadastro.html', {
        'erro': erro,
        'dados': request.POST,
        'instituicoes': Instituicao.objects.all(),
    })


def rotas(request):
    '''Lista todas as rotas, com busca opcional por origem (?q=...). Exige login.'''
    usuario = usuario_logado(request)
    if not usuario:
        return redirect('login')
    q = request.GET.get('q', '')
    lista = Rota.objects.select_related('id_usuario', 'id_instituicao')
    if q:
        lista = lista.filter(origem__icontains=q)
    return render(request, 'rotas.html', {'rotas': lista, 'search_query': q,
                                          'usuario_logado': usuario})

def rota_detalhes(request, rota_id):
    rota = get_object_or_404(Rota, id_rota=rota_id)
    return render(request, 'rota.html', {'rota': rota})


def usuarios(request):
    return render(request, 'listar_usuarios.html',
                  {'usuarios': Usuario.objects.all()})


def usuario_remover(request, usuario_id):
    '''GET mostra a confirmação. POST apaga o usuário.'''
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    if request.method == 'POST':
        if request.POST.get('confirmacao', '').strip() == 'REMOVER':
            usuario.delete()
            return redirect('usuarios')
        return render(request, 'remocao.html', {
            'usuario': usuario,
            'erro': 'Digite REMOVER para confirmar a exclusão.',
        })
    return render(request, 'remocao.html', {'usuario': usuario})


def perfil(request, usuario_id):
    usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
    return render(request, 'PerfilDoUsuario.html', {
        'usuario': usuario,
        'rotas': usuario.rotas.all(),
    })


def grupo_detalhes(request, grupo_id):
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    return render(request, 'gruposrota.html', {
        'grupo': grupo,
        'membros': grupo.usuarios.all(),
        'mensagens': grupo.mensagens.select_related('usuario'),
    })


def carona_detalhes(request, carona_id):
    carona = get_object_or_404(Carona, id_carona=carona_id)
    return render(request, 'Detalhescarona.html', {
        'carona': carona,
        'passageiros': carona.passageiros.all(),
    })
