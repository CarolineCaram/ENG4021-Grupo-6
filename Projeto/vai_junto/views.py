from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password
from vai_junto.models import Usuario, Rota, Grupo, Carona


def home(request):
    return render(request, 'Página_Inicio.html')

def login_view(request):
    return render(request, 'Tela_Login.html')

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
    return render(request, 'OferecerCarona.html')

def cadastro(request):
    '''GET mostra o formulário. POST cria o usuário no banco.'''
    erro = None
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        matricula = request.POST.get('matricula')
        senha = request.POST.get('senha')
        if Usuario.objects.filter(email=email).exists():
            erro = 'Este e-mail já está cadastrado.'
        elif Usuario.objects.filter(matricula=matricula).exists():
            erro = 'Esta matrícula já está cadastrada.'
        else:
            Usuario.objects.create(nome=nome, email=email, matricula=matricula,
                                   senha=make_password(senha))
            return redirect('login')
    return render(request, 'cadastro.html', {'erro': erro})


def rotas(request):
    '''Lista todas as rotas, com busca opcional por origem (?q=...).'''
    q = request.GET.get('q', '')
    lista = Rota.objects.select_related('id_usuario', 'id_instituicao')
    if q:
        lista = lista.filter(origem__icontains=q)
    return render(request, 'rotas.html', {'rotas': lista, 'search_query': q})

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
        usuario.delete()
        return redirect('usuarios')
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