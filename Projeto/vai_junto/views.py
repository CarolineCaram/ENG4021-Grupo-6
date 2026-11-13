from functools import wraps
from datetime import date, datetime
from django.utils import timezone

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from vai_junto.models import (Usuario, Rota, Grupo, Carona, Instituicao,
                              HorarioRota, Solicitacao, Mensagem, Veiculo, Avaliacao)


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
    '''Esqueci minha senha: etapa 1 confere e-mail + matrícula;
    etapa 2 grava a nova senha e manda pro login.'''
    erro = None
    etapa = 2 if request.session.get('recuperar_usuario_id') else 1

    if request.method == 'POST':
        d = request.POST
        if d.get('etapa') == '2':
            usuario = Usuario.objects.filter(
                id_usuario=request.session.get('recuperar_usuario_id')).first()
            senha = d.get('senha', '')
            if not usuario:
                request.session.pop('recuperar_usuario_id', None)
                erro = 'Sua sessão expirou. Confirme seu e-mail e matrícula de novo.'
                etapa = 1
            elif len(senha) < 8:
                erro = 'A senha precisa ter pelo menos 8 caracteres.'
            elif senha != d.get('confirmar', ''):
                erro = 'As senhas não conferem.'
            else:
                usuario.senha = make_password(senha)
                usuario.save()
                request.session.pop('recuperar_usuario_id', None)
                return redirect('login')
        else:
            email = d.get('email', '').strip()
            matricula = d.get('matricula', '').strip()
            usuario = Usuario.objects.filter(email__iexact=email,
                                             matricula=matricula).first()
            if usuario:
                request.session['recuperar_usuario_id'] = usuario.id_usuario
                etapa = 2
            else:
                erro = 'E-mail e matrícula não conferem com nenhuma conta.'
                etapa = 1

    return render(request, 'recuperar_senha.html', {
        'erro': erro,
        'etapa': etapa,
        'dados': request.POST if request.method == 'POST' else {},
    })

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
        elif dados.get('transporte') not in {'Carro', 'Moto', 'Van'}:
            erro = 'Selecione um meio de transporte válido.'
        elif not 1 <= vagas <= {'Carro': 4, 'Moto': 1, 'Van': 8}[dados.get('transporte')]:
            limite = {'Carro': 4, 'Moto': 1, 'Van': 8}[dados.get('transporte')]
            erro = '%s permite no máximo %d vaga(s).' % (dados.get('transporte'), limite)
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
            # o veículo usado na rota entra (ou atualiza) na lista de veículos dele
            Veiculo.objects.update_or_create(
                id_usuario=usuario, tipo=dados.get('transporte'),
                defaults={'vagas': vagas})
            # passageiro que publica uma rota passa a dar carona também
            if usuario.papel == 'pegar':
                usuario.papel = 'ambos'
                usuario.save(update_fields=['papel'])
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
        elif not matricula.isdigit() or not 6 <= len(matricula) <= 10:
            erro = 'A matrícula deve ter só números (6 a 10 dígitos).'
        elif len(senha) < 8:
            erro = 'A senha precisa ter pelo menos 8 caracteres.'
        elif senha != confirmar:
            erro = 'As senhas não conferem.'
        elif Usuario.objects.filter(email__iexact=email).exists():
            erro = 'Este e-mail já está cadastrado.'
        elif Usuario.objects.filter(matricula=matricula).exists():
            erro = 'Esta matrícula já está cadastrada.'
        else:
            # a rota é pré-requisito: valida TUDO do trajeto antes de criar a conta
            inst_id = d.get('instituicao', '')
            instituicao = Instituicao.objects.filter(pk=inst_id).first() if inst_id.isdigit() else None
            origem = d.get('origem', '').strip()
            horarios = ler_horarios(d)   # um horário por dia da semana marcado
            if not instituicao:
                erro = 'Escolha sua instituição.'
            elif not origem:
                erro = 'Preencha seu ponto de origem (bairro).'
            elif not horarios:
                erro = 'Marque pelo menos um dia da semana com um horário válido.'
            else:
                papel = d.get('papel', 'ambos')
                if papel not in ('pegar', 'dar', 'ambos'):
                    papel = 'ambos'
                usuario = Usuario.objects.create(nome=nome, email=email, matricula=matricula,
                                                 senha=make_password(senha), papel=papel)

                LIMITE_VAGAS = {'Carro': 4, 'Moto': 1, 'Bicicleta': 1, 'Van': 8}

                # Preferência de veículo de quem pega carona (pode marcar vários)
                if papel in ('pegar', 'ambos'):
                    for tipo in d.getlist('pref_veiculos'):
                        if tipo in LIMITE_VAGAS:
                            Veiculo.objects.get_or_create(
                                id_usuario=usuario, tipo=tipo, defaults={'vagas': 0})

                if papel in ('dar', 'ambos'):
                    # veículos do motorista: tipo + vagas por linha (vários permitidos)
                    tipos = [t for t in d.getlist('veiculo_tipo') if t in LIMITE_VAGAS]
                    numeros = d.getlist('veiculo_vagas')
                    vistos = set()
                    veiculos = []
                    for i, tipo in enumerate(tipos):
                        if tipo in vistos:
                            continue
                        vistos.add(tipo)
                        limite = LIMITE_VAGAS[tipo]
                        txt = numeros[i] if i < len(numeros) else ''
                        n = int(txt) if txt.isdigit() else limite
                        veiculos.append((tipo, max(1, min(n, limite))))
                    if not veiculos:
                        # compatibilidade com o formulário antigo (um transporte só)
                        tipo = d.get('transporte', '') or 'Carro'
                        if tipo not in LIMITE_VAGAS:
                            tipo = 'Carro'
                        limite = LIMITE_VAGAS[tipo]
                        txt = d.get('vagas', '')
                        n = int(txt) if txt.isdigit() else limite
                        veiculos = [(tipo, max(1, min(n, limite)))]
                    for tipo, n in veiculos:
                        Veiculo.objects.create(id_usuario=usuario, tipo=tipo, vagas=n)
                    transporte, vagas = veiculos[0]
                else:
                    # passageiro: a rota guarda o trajeto dele (origem/horários),
                    # usado nas sugestões; não aparece no Descobrir
                    prefs = [t for t in d.getlist('pref_veiculos') if t in LIMITE_VAGAS]
                    transporte = prefs[0] if prefs else 'A combinar'
                    vagas = 0
                criar_rota(
                    horarios,
                    id_usuario=usuario, id_instituicao=instituicao, origem=origem,
                    referencia=d.get('referencia', '').strip() or None,
                    transporte=transporte,
                    vagas=vagas)

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
    if usuario.papel == 'dar':
        # quem é só motorista não vê a lista "Rotas disponíveis",
        # só a seção "Passageiros com trajeto parecido"
        lista = []
    else:
        lista = list(Rota.objects.select_related('id_usuario', 'id_instituicao'))
        # o usuário logado nunca vê as próprias rotas no Descobrir,
        # e só aparecem rotas de quem DÁ carona (motorista ou os dois)
        lista = [r for r in lista
                 if r.id_usuario_id != usuario.id_usuario
                 and r.id_usuario.papel in ('dar', 'ambos')]
        if q:
            lista = [r for r in lista if q.lower() in r.origem.lower()]

    # Em cada card: eu sou o dono? já pedi carona? já estou no grupo?
    minhas_solicitacoes = {s.rota_id: s.status
                           for s in Solicitacao.objects.filter(solicitante=usuario)}
    meus_grupos = {g.rota_id: g.id_grupo for g in usuario.grupos.all()}
    for r in lista:
        r.eh_dono = r.id_usuario_id == usuario.id_usuario
        r.minha_solicitacao = minhas_solicitacoes.get(r.id_rota)
        r.meu_grupo_id = meus_grupos.get(r.id_rota)

    # Sugestões pelo trajeto da pessoa (mesma instituição, horário próximo,
    # mesma origem primeiro):
    # - passageiro: caronas compatíveis, que saem da lista geral para não repetir
    # - motorista: passageiros compatíveis, para quem ele pode oferecer carona
    sugestoes = []
    sugestoes_pass = []
    minha_rota = ultima_rota(usuario)
    if minha_rota and usuario.papel == 'pegar':
        sugestoes = [m for m in buscar_matches(minha_rota)
                     if m.id_usuario.papel in ('dar', 'ambos')]
        for m in sugestoes:
            m.eh_dono = False
            m.minha_solicitacao = minhas_solicitacoes.get(m.id_rota)
            m.meu_grupo_id = meus_grupos.get(m.id_rota)
        ids = {m.id_rota for m in sugestoes}
        lista = [r for r in lista if r.id_rota not in ids]
    elif minha_rota and usuario.papel in ('dar', 'ambos'):
        ofertas = {s.destinatario_id: s.status
                   for s in Solicitacao.objects.filter(rota=minha_rota, tipo='oferta')}
        sugestoes_pass = [m for m in buscar_matches(minha_rota)
                          if m.id_usuario.papel in ('pegar', 'ambos')]
        for m in sugestoes_pass:
            m.oferta_status = ofertas.get(m.id_usuario_id)
    # Abas: usuários (menos eu), meus grupos e minhas solicitações
    outros_usuarios = (Usuario.objects.exclude(pk=usuario.pk)
                       .order_by('nome'))
    meus_grupos_lista = (usuario.grupos
                         .select_related('rota', 'rota__id_instituicao')
                         .order_by('nome'))
    minhas_sols = list(Solicitacao.objects
                       .filter(solicitante=usuario)
                       .select_related('rota', 'rota__id_usuario',
                                       'rota__id_instituicao')
                       .order_by('-criada_em'))
    # Solicitações PARA MIM: motorista recebe pedidos; passageiro recebe ofertas
    sols_recebidas = []
    if usuario.papel in ('dar', 'ambos'):
        sols_recebidas += list(Solicitacao.objects
                               .filter(rota__id_usuario=usuario, tipo='pedido')
                               .select_related('solicitante', 'rota',
                                               'rota__id_instituicao'))
    if usuario.papel in ('pegar', 'ambos'):
        sols_recebidas += list(Solicitacao.objects
                               .filter(destinatario=usuario, tipo='oferta')
                               .select_related('solicitante', 'rota',
                                               'rota__id_instituicao'))
    sols_recebidas.sort(key=lambda s: s.criada_em, reverse=True)
    pendentes = (sum(1 for s in minhas_sols if s.status == 'pendente')
                 + sum(1 for s in sols_recebidas if s.status == 'pendente'))
    return render(request, 'rotas.html', {
        'rotas': lista, 'search_query': q, 'usuario_logado': usuario,
        'sugestoes': sugestoes,
        'sugestoes_pass': sugestoes_pass,
        'minha_rota': minha_rota,
        'outros_usuarios': outros_usuarios,
        'meus_grupos_lista': meus_grupos_lista,
        'minhas_sols': minhas_sols,
        'sols_recebidas': sols_recebidas,
        'solicitacoes_pendentes': pendentes})

def rota_detalhes(request, rota_id):
    rota = get_object_or_404(Rota, id_rota=rota_id)
    return render(request, 'rota.html', {'rota': rota,
                                         'usuario_logado': usuario_logado(request)})


def usuarios(request):
    '''Lista os usuários cadastrados, sem mostrar o próprio usuário logado.'''
    lista = Usuario.objects.all()
    uid = request.session.get('usuario_id')
    if uid:
        lista = lista.exclude(pk=uid)
    return render(request, 'listar_usuarios.html',
                  {'usuarios': lista})


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
    rotas = usuario.rotas.all()
    # caronas = viagens em grupo da rota dele + caronas em que foi passageiro
    total_caronas = (Carona.objects.filter(rota__id_usuario=usuario).count()
                     + usuario.caronas_como_passageiro.count())
    recebidas = list(usuario.avaliacoes_recebidas
                     .select_related('avaliador').order_by('-criada_em'))

    def pct(avs):
        n = len(avs)
        return ('%d%%' % round(100 * sum(1 for a in avs if a.aprovou) / n)) if n else None

    av_motorista = [a for a in recebidas if a.papel == 'motorista']
    av_passageiro = [a for a in recebidas if a.papel == 'passageiro']
    aprovacao = pct(recebidas)
    veiculos = list(usuario.veiculos.all())
    # votos que o visitante logado já deu nesse perfil (pra marcar os botões)
    minhas_avaliacoes = {}
    uid = request.session.get('usuario_id')
    if uid and uid != usuario.id_usuario:
        minhas_avaliacoes = {a.papel: a.aprovou for a in
                             Avaliacao.objects.filter(avaliador_id=uid, avaliado=usuario)}
    return render(request, 'PerfilDoUsuario.html', {
        'usuario': usuario,
        'rotas': rotas,
        'primeira_rota': rotas.first(),
        'total_caronas': total_caronas,
        'total_grupos': usuario.grupos.count(),
        'aprovacao': aprovacao,
        # avaliações separadas por papel (None = nenhuma avaliação)
        'avaliacoes': recebidas[:10],
        'pct_motorista': pct(av_motorista), 'n_motorista': len(av_motorista),
        'pct_passageiro': pct(av_passageiro), 'n_passageiro': len(av_passageiro),
        'minhas_avaliacoes': minhas_avaliacoes,
        # vagas > 0: veículos do motorista · vagas = 0: preferências do passageiro
        'veiculos_motorista': [v for v in veiculos if v.vagas > 0],
        'preferencias': [v for v in veiculos if v.vagas == 0],
        # selo de matrícula verificada só aparece se o número passa na validação
        'matricula_valida': usuario.matricula.isdigit() and 6 <= len(usuario.matricula) <= 10,
    })


@login_necessario
def avaliar(request, usuario_id):
    '''Avalia um usuário como motorista ou passageiro (recomendo / não recomendo).
    Avaliar de novo no mesmo papel atualiza o voto. Ninguém se autoavalia.'''
    avaliado = get_object_or_404(Usuario, id_usuario=usuario_id)
    if request.method == 'POST' and avaliado != request.usuario:
        papel = request.POST.get('papel', '')
        voto = request.POST.get('voto', '')
        if papel in ('motorista', 'passageiro') and voto in ('1', '0'):
            Avaliacao.objects.update_or_create(
                avaliador=request.usuario, avaliado=avaliado, papel=papel,
                defaults={'aprovou': voto == '1'})
    return redirect('perfil', usuario_id=usuario_id)


@login_necessario
def editar_perfil(request):
    '''Edição do próprio perfil: nome, foto, preferências/veículos e trajeto.
    O trajeto atualiza a rota mais recente; rota nova é pelo "Publicar nova rota".'''
    usuario = request.usuario
    LIMITE_VAGAS = {'Carro': 4, 'Moto': 1, 'Bicicleta': 1, 'Van': 8}
    erro = None
    if request.method == 'POST':
        d = request.POST
        nome = d.get('nome', '').strip()
        if not nome:
            erro = 'Informe o seu nome.'
        else:
            usuario.nome = nome
            if request.FILES.get('foto'):
                usuario.foto = request.FILES['foto']
            usuario.save()

            # Preferência de veículo de quem pega carona (vagas = 0)
            if usuario.papel in ('pegar', 'ambos'):
                Veiculo.objects.filter(id_usuario=usuario, vagas=0).delete()
                for tipo in d.getlist('pref_veiculos'):
                    if tipo in LIMITE_VAGAS:
                        Veiculo.objects.get_or_create(
                            id_usuario=usuario, tipo=tipo, vagas=0)

            # Veículos de quem dá carona (vagas > 0), vários permitidos
            primeiro_veiculo = None
            if usuario.papel in ('dar', 'ambos'):
                Veiculo.objects.filter(id_usuario=usuario, vagas__gt=0).delete()
                tipos = [t for t in d.getlist('veiculo_tipo') if t in LIMITE_VAGAS]
                numeros = d.getlist('veiculo_vagas')
                vistos = set()
                for i, tipo in enumerate(tipos):
                    if tipo in vistos:
                        continue
                    vistos.add(tipo)
                    limite = LIMITE_VAGAS[tipo]
                    txt = numeros[i] if i < len(numeros) else ''
                    n = max(1, min(int(txt) if txt.isdigit() else limite, limite))
                    Veiculo.objects.create(id_usuario=usuario, tipo=tipo, vagas=n)
                    if primeiro_veiculo is None:
                        primeiro_veiculo = (tipo, n)

            # Trajeto: edita a rota mais recente no lugar
            rota = ultima_rota(usuario)
            if rota:
                origem = d.get('origem', '').strip()
                if origem:
                    rota.origem = origem
                inst_id = d.get('instituicao', '')
                if inst_id.isdigit():
                    instituicao = Instituicao.objects.filter(pk=inst_id).first()
                    if instituicao:
                        rota.id_instituicao = instituicao
                rota.referencia = d.get('referencia', '').strip() or None
                horarios = ler_horarios(d)
                if horarios:
                    rota.horario = min(h for _, h in horarios)
                    rota.horarios.all().delete()
                    HorarioRota.objects.bulk_create(
                        [HorarioRota(rota=rota, dia=dia, horario=h)
                         for dia, h in horarios])
                # mantém o campo antigo da rota em sincronia com o 1º veículo
                if primeiro_veiculo:
                    rota.transporte, rota.vagas = primeiro_veiculo
                rota.save()
            return redirect('perfil', usuario_id=usuario.id_usuario)

    rota = ultima_rota(usuario)
    horarios_rota = ({h.dia: h.horario.strftime('%H:%M')
                      for h in rota.horarios.all()} if rota else {})
    veiculos = list(usuario.veiculos.all())
    return render(request, 'conta_editar.html', {
        'usuario': usuario,
        'erro': erro,
        'rota': rota,
        'instituicoes': Instituicao.objects.all(),
        'dias': [{'n': n, 'nome': nome_dia,
                  'marcado': n in horarios_rota,
                  'horario': horarios_rota.get(n, '')}
                 for n, nome_dia in HorarioRota.DIAS],
        'veiculos_motorista': [v for v in veiculos if v.vagas > 0],
        'preferencias': [v for v in veiculos if v.vagas == 0],
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
    pode_dirigir = usuario.papel in ('dar', 'ambos')
    pode_solicitar = usuario.papel != 'dar'

    enviadas = (Solicitacao.objects.filter(solicitante=usuario)
                .select_related('rota__id_usuario', 'rota__id_instituicao')
                .order_by('-criada_em'))
    ja_solicitadas = {s.rota_id for s in enviadas}

    matches = buscar_matches(rota) if rota else []
    matches = [m for m in matches if m.id_usuario.papel in ('dar', 'ambos')]
    for m in matches:
        m.ja_solicitada = m.id_rota in ja_solicitadas

    # aceitar/recusar solicitações é só de quem dá carona (só pedidos;
    # ofertas que ele enviou aparecem nas enviadas)
    if pode_dirigir:
        recebidas = (Solicitacao.objects
                     .filter(rota__id_usuario=usuario, status='pendente',
                             tipo='pedido')
                     .select_related('solicitante', 'rota__id_instituicao'))
    else:
        recebidas = []

    pendentes = sum(1 for s in enviadas if s.status == 'pendente') + len(recebidas)

    return render(request, 'gruposrota.html', {
        'detalhe': False,
        'rota': rota,
        'matches': matches,
        'enviadas': enviadas,
        'recebidas': recebidas,
        'pendentes': pendentes,
        'meus_grupos': usuario.grupos.select_related('rota__id_instituicao'),
        'usuario_logado': usuario,
        'pode_dirigir': pode_dirigir,
        'pode_solicitar': pode_solicitar,
    })


@login_necessario
def mudar_papel(request):
    '''Troca o tipo de conta (só pego / só dou / os dois). Ao trocar, apaga as
    solicitações PENDENTES da pessoa (feitas, recebidas e ofertas) — não faria
    sentido virar motorista e continuar com pedido de carona em aberto.
    O aviso de confirmação (continuar/cancelar) fica no template do perfil.
    Se a pessoa passou a dar carona e ainda não tem rota, manda publicar a rota.'''
    usuario = request.usuario
    if request.method == 'POST':
        papel = request.POST.get('papel', '')
        if papel in ('pegar', 'dar', 'ambos') and papel != usuario.papel:
            Solicitacao.objects.filter(
                Q(solicitante=usuario) | Q(destinatario=usuario) | Q(rota__id_usuario=usuario),
                status='pendente').delete()
            usuario.papel = papel
            usuario.save(update_fields=['papel'])
    if usuario.papel in ('dar', 'ambos') and not usuario.rotas.exists():
        return redirect('oferecer_carona')
    return redirect('perfil', usuario_id=usuario.id_usuario)


@login_necessario
def contatar(request, rota_id):
    '''Botão "Solicitar carona": registra o pedido para pegar carona naquela rota.
    Ninguém pode solicitar a própria rota.'''
    rota = get_object_or_404(Rota, id_rota=rota_id)
    if rota.id_usuario_id == request.usuario.pk:
        return redirect('rotas')
    if request.usuario.papel == 'dar':
        # quem é só motorista não pede carona
        return redirect('rotas')
    if request.method == 'POST':
        sol, criada = Solicitacao.objects.get_or_create(
            rota=rota, solicitante=request.usuario, tipo='pedido')
        if not criada and sol.status == 'recusada':
            # pediu de novo depois de recusado: volta a ficar pendente
            sol.status = 'pendente'
            sol.respondida_em = None
            sol.save()
    if request.POST.get('next') == 'rotas':
        return redirect('rotas')
    return redirect('grupos_rota')


@login_necessario
def ofertar_carona(request, rota_id, usuario_id):
    '''Botão "Oferecer carona": o dono da rota oferece a carona diretamente
    para um passageiro. Espelho do contatar (que é do passageiro).'''
    rota = get_object_or_404(Rota, id_rota=rota_id)
    alvo = get_object_or_404(Usuario, id_usuario=usuario_id)
    if (rota.id_usuario_id != request.usuario.pk
            or request.usuario.papel == 'pegar'
            or alvo.pk == request.usuario.pk
            or alvo.papel == 'dar'):
        return redirect('rotas')
    if request.method == 'POST':
        sol, criada = Solicitacao.objects.get_or_create(
            rota=rota, tipo='oferta', destinatario=alvo,
            defaults={'solicitante': request.usuario})
        if not criada and sol.status == 'recusada':
            # ofereceu de novo depois de recusado: volta a ficar pendente
            sol.status = 'pendente'
            sol.respondida_em = None
            sol.save()
    return redirect('rotas')


@login_necessario
def recusar_solicitacao(request, solicitacao_id):
    '''O motorista recusa um pedido pendente.'''
    sol = get_object_or_404(Solicitacao, pk=solicitacao_id)
    autorizado = (sol.rota.id_usuario_id == request.usuario.pk
                  or (sol.tipo == 'oferta'
                      and sol.destinatario_id == request.usuario.pk))
    if request.method == 'POST' and autorizado and sol.status == 'pendente':
        sol.status = 'recusada'
        sol.respondida_em = timezone.now()
        sol.save()
    if request.POST.get('next') == 'rotas':
        return redirect('rotas')
    return redirect('grupos_rota')


@login_necessario
def grupo_chat(request, grupo_id):
    '''Chat do grupo: só quem é membro vê e manda mensagens.'''
    grupo = get_object_or_404(Grupo, id_grupo=grupo_id)
    if not grupo.usuarios.filter(pk=request.usuario.pk).exists():
        return redirect('grupos_rota')
    if request.method == 'POST':
        texto = request.POST.get('texto', '').strip()
        if texto:
            Mensagem.objects.create(grupo=grupo, usuario=request.usuario, texto=texto)
        return redirect('grupo_chat', grupo_id=grupo.id_grupo)
    return render(request, 'chat.html', {
        'grupo': grupo,
        'mensagens': grupo.mensagens.select_related('usuario'),
        'usuario_logado': request.usuario,
    })


@login_necessario
def confirmar_solicitacao(request, solicitacao_id):
    '''O motorista aceita um pedido. Cria o grupo e a carona e abre a confirmação.'''
    sol = get_object_or_404(Solicitacao, pk=solicitacao_id)
    rota = sol.rota
    # pedido: confirma o dono da rota (motorista)
    # oferta: confirma o destinatário (passageiro que recebeu a oferta)
    passageiro = sol.destinatario if sol.tipo == 'oferta' else sol.solicitante
    autorizado = (rota.id_usuario_id == request.usuario.pk
                  if sol.tipo == 'pedido'
                  else sol.destinatario_id == request.usuario.pk)

    if request.method != 'POST' or not autorizado:
        return redirect('grupos_rota')

    try:
        data = datetime.strptime(request.POST.get('data', ''), '%Y-%m-%d').date()
    except ValueError:
        data = date.today()

    grupo, _ = Grupo.objects.get_or_create(
        rota=rota,
        defaults={'nome': f'{rota.origem} → {rota.id_instituicao.sigla}'})
    grupo.usuarios.add(rota.id_usuario, passageiro)

    carona = Carona.objects.filter(rota=rota, data=data).first()
    if carona is None:
        carona = Carona.objects.create(grupo=grupo, rota=rota, data=data, status='confirmada')

    ja_esta = carona.passageiros.filter(pk=passageiro.pk).exists()
    if ja_esta or carona.passageiros.count() < rota.vagas:
        carona.passageiros.add(passageiro)
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