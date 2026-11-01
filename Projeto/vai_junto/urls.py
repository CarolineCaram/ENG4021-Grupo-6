from django.contrib import admin
from django.urls import path
from vai_junto import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('home/', views.home),
    path('login/', views.login_view, name='login'),
    path('recuperar-senha/', views.recuperar_senha, name='recuperar_senha'),
    path('verificacao/', views.verificacao, name='verificacao'),
    path('como-funciona/', views.como_funciona, name='como_funciona'),
    path('mapa/', views.mapa, name='mapa'),
    path('reportar-problema/', views.reportar_problema, name='reportar_problema'),
    path('cadastrar-veiculo/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    path('meio-transporte/', views.cadastro_meio_transporte, name='meio_transporte'),
    path('oferecer-carona/', views.oferecer_carona, name='oferecer_carona'),

    path('cadastro/', views.cadastro, name='cadastro'),
    path('rotas/', views.rotas, name='rotas'),
    path('rotas/<int:rota_id>/', views.rota_detalhes, name='rota_detalhes'),
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/<int:usuario_id>/remover/', views.usuario_remover, name='usuario_remover'),
    path('perfil/<int:usuario_id>/', views.perfil, name='perfil'),
    path('grupos/<int:grupo_id>/', views.grupo_detalhes, name='grupo_detalhes'),
    path('caronas/<int:carona_id>/', views.carona_detalhes, name='carona_detalhes'),
]