from functools import wraps
from datetime import date, datetime
from django.utils import timezone

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from vai_junto.models import (Usuario, Rota, Grupo, Carona, Instituicao,
                              HorarioRota, Solicitacao)


# ---------------------------------------------------------------
# Ajuda: descobre quem está logado (guardamos o id na sessão)
# ---------------------------------------------------------------
def usuario_logado(request):
    uid = request.session.get('usuario_id')
    if uid:
        return Usuario.objects.filter(id_usuario=uid).first()
    return None

def login_necessario(view):
    '''Sem login, manda para /login/. Dentro da view, o usuário fica em request.usuario.'''
    @wraps(view)
    def interna(request, *args, **kwargs):
        usuario = usuario_logado(request)
        if not usuario:
            return redirect('login')
        request.usuario = usuario
        return view(request, *args, **kwargs)
    return interna


def ultima_rota(usuario):
    return usuario.rotas.order_by('-id_rota').first()


def buscar_matches(rota, janela=60):
    '''Estudantes compatíveis: mesma instituição e horário até `janela` minutos
    de diferença. Quem tem a mesma origem aparece primeiro.'''
    def minutos(h):
        return h.hour * 60 + h.minute

    candidatas = (Rota.objects
                  .filter(id_instituicao=rota.id_instituicao)
                  .exclude(id_usuario=rota.id_usuario)
                  .select_related('id_usuario', 'id_instituicao'))
    matches = []
    for c in candidatas:
        dif = abs(minutos(c.horario) - minutos(rota.horario))
        if dif <= janela:
            c.dif_min = dif
            c.mesma_origem = c.origem.strip().lower() == rota.origem.strip().lower()
            matches.append(c)
    matches.sort(key=lambda c: (not c.mesma_origem, c.dif_min))
    return matches

# ---------------------------------------------------------------
# Horários por dia da semana (formulário: checkbox "dias" + campo "horario_<n>")
# ---------------------------------------------------------------
def dias_do_formulario(post=None):
    """Lista de dias pro template: número, nome, se está marcado e o horário digitado."""
    marcados = post.getlist('dias') if post else []
    return [{'n': n, 'nome': nome, 'marcado': str(n) in marcados,
             'horario': post.get('horario_%d' % n, '') if post else ''}
            for n, nome in HorarioRota.DIAS]


def ler_horarios(post):
    """Devolve [(dia, hora), ...] dos dias marcados, ou None se algum horário for inválido."""
    horarios = []
    for n, _ in HorarioRota.DIAS:
        if str(n) in post.getlist('dias'):
            try:
                horarios.append((n, datetime.strptime(post.get('horario_%d' % n, ''), '%H:%M').time()))
            except ValueError:
                return None
    return horarios


def criar_rota(horarios, **campos):
    """Cria a Rota (horario = o mais cedo da semana) e um HorarioRota por dia marcado."""
    rota = Rota.objects.create(horario=min(h for _, h in horarios), **campos)
    HorarioRota.objects.bulk_create(
        [HorarioRota(rota=rota, dia=dia, horario=h) for dia, h in horarios])
    return rota


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
        horarios = ler_horarios(dados)
        vagas_texto = dados.get('vagas', '')
        instituicao = (
            Instituicao.objects.filter(pk=instituicao_id).first()
            if instituicao_id.isdigit() else None
        )

        try:
            vagas = int(vagas_texto)
        except (TypeError, ValueError):
            vagas = 0

        if not origem:
            erro = 'Informe o ponto de origem.'
        elif not instituicao:
            erro = 'Selecione uma instituição válida.'
        elif not horarios:
            erro = 'Escolha pelo menos um dia e informe o horário de saída de cada dia marcado.'
        elif not 1 <= vagas <= 8:
            erro = 'Informe entre 1 e 8 vagas.'
        elif dados.get('transporte') not in {'Carro', 'Moto', 'Van'}:
            erro = 'Selecione um meio de transporte válido.'
        else:
            criar_rota(
                horarios,
                id_usuario=usuario,
                id_instituicao=instituicao,
                origem=origem,
                referencia=dados.get('referencia', '').strip() or None,
                transporte=dados.get('transporte', 'Carro'),
                vagas=vagas,
            )
            return redirect('rotas')

    return render(request, 'OferecerCarona.html', {
        'erro': erro,
        'dados': request.POST,
        'dias': dias_do_formulario(request.POST if request.method == 'POST' else None),
        'instituicoes': Instituicao.objects.all(),
    })


def verificar_email(request):
    '''Usado pela etapa 1 do cadastro: diz se o e-mail ainda está livre.'''
    email = request.GET.get('email', '').strip().lower()
    livre = bool(email) and not Usuario.objects.filter(email__iexact=email).exists()
    return JsonResponse({'disponivel': livre})


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
            horarios = ler_horarios(d)   # um horário por dia da semana marcado
            if instituicao and origem and horarios:
                vagas = d.get('vagas', '')
                criar_rota(
                    horarios,
                    id_usuario=usuario, id_instituicao=instituicao, origem=origem,
                    referencia=d.get('referencia', '').strip() or None,
                    transporte=d.get('transporte', '') or 'passageiro',
                    vagas=int(vagas) if vagas.isdigit() else 0)

            request.session['usuario_id'] = usuario.id_usuario
            return redirect('rotas')

    return render(request, 'cadastro.html', {
        'erro': erro,
        'dados': request.POST,
        'dias': dias_do_formulario(request.POST if request.method == 'POST' else None),
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
    return render(request, 'rota.html', {'rota': rota,
                                         'usuario_logado': usuario_logado(request)})


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


@login_necessario
def grupo_detalhes(request, grupo_id):
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    return render(request, 'gruposrota.html', {
        'detalhe': True,
        'grupo': grupo,
        'membros': grupo.usuarios.all(),
        'mensagens': grupo.mensagens.select_related('usuario'),
        'usuario_logado': request.usuario,
    })


def carona_detalhes(request, carona_id):
    carona = get_object_or_404(Carona, id_carona=carona_id)
    return render(request, 'Detalhescarona.html', {
        'carona': carona,
        'passageiros': carona.passageiros.all(),
    })

@login_necessario
def grupos_rota(request):
    '''Etapa 7: estudantes compatíveis (Descobrir) e contatos (Meu grupo).'''
    usuario = request.usuario
    rota = ultima_rota(usuario)
    if not rota:
        return redirect('oferecer_carona')

    enviadas = (Solicitacao.objects.filter(solicitante=usuario)
                .select_related('rota__id_usuario', 'rota__id_instituicao')
                .order_by('-criada_em'))
    ja_solicitadas = {s.rota_id for s in enviadas}

    matches = buscar_matches(rota)
    for m in matches:
        m.ja_solicitada = m.id_rota in ja_solicitadas

    recebidas = (Solicitacao.objects
                 .filter(rota__id_usuario=usuario, status='pendente')
                 .select_related('solicitante', 'rota__id_instituicao'))

    pendentes = sum(1 for s in enviadas if s.status == 'pendente') + recebidas.count()

    return render(request, 'gruposrota.html', {
        'detalhe': False,
        'rota': rota,
        'matches': matches,
        'enviadas': enviadas,
        'recebidas': recebidas,
        'pendentes': pendentes,
        'meus_grupos': usuario.grupos.select_related('rota__id_instituicao'),
        'usuario_logado': usuario,
    })


@login_necessario
def contatar(request, rota_id):
    '''Botão "Contatar": registra o pedido para pegar carona naquela rota.'''
    rota = get_object_or_404(Rota, id_rota=rota_id)
    if request.method == 'POST' and rota.id_usuario_id != request.usuario.pk:
        Solicitacao.objects.get_or_create(rota=rota, solicitante=request.usuario)
    return redirect('grupos_rota')


@login_necessario
def confirmar_solicitacao(request, solicitacao_id):
    '''O motorista aceita um pedido. Cria o grupo e a carona e abre a confirmação.'''
    sol = get_object_or_404(Solicitacao, pk=solicitacao_id)
    rota = sol.rota

    if request.method != 'POST' or rota.id_usuario_id != request.usuario.pk:
        return redirect('grupos_rota')

    try:
        data = datetime.strptime(request.POST.get('data', ''), '%Y-%m-%d').date()
    except ValueError:
        data = date.today()

    grupo, _ = Grupo.objects.get_or_create(
        rota=rota,
        defaults={'nome': f'{rota.origem} → {rota.id_instituicao.sigla}'})
    grupo.usuarios.add(rota.id_usuario, sol.solicitante)

    carona = Carona.objects.filter(rota=rota, data=data).first()
    if carona is None:
        carona = Carona.objects.create(grupo=grupo, rota=rota, data=data, status='confirmada')

    ja_esta = carona.passageiros.filter(pk=sol.solicitante.pk).exists()
    if ja_esta or carona.passageiros.count() < rota.vagas:
        carona.passageiros.add(sol.solicitante)
        sol.status = 'aceita'
        sol.respondida_em = timezone.now()
        sol.save()
        return redirect('confirmacao_carona', carona_id=carona.id_carona)

    sol.status = 'recusada'   # carona cheia
    sol.respondida_em = timezone.now()
    sol.save()
    return redirect('grupos_rota')


@login_necessario
def confirmacao_carona(request, carona_id):
    '''Tela "Carona confirmada!" (RF12). Só quem participa vê.'''
    carona = get_object_or_404(Carona, id_carona=carona_id)
    rota = carona.rota
    motorista = rota.id_usuario
    passageiros = carona.passageiros.all()

    eh_motorista = motorista.pk == request.usuario.pk
    if not eh_motorista and not passageiros.filter(pk=request.usuario.pk).exists():
        return redirect('grupos_rota')

    return render(request, 'confirmacao_carona.html', {
        'carona': carona,
        'rota': rota,
        'motorista': motorista,
        'passageiros': passageiros,
        'grupo': carona.grupo,
        'eh_motorista': eh_motorista,
        'vagas_restantes': max(rota.vagas - passageiros.count(), 0),
        'usuario_logado': request.usuario,
    })