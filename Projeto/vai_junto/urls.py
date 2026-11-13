from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from vai_junto import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('home/', views.home),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar-senha/', views.recuperar_senha, name='recuperar_senha'),
    path('verificacao/', views.verificacao, name='verificacao'),
    path('como-funciona/', views.como_funciona, name='como_funciona'),
    path('mapa/', views.mapa, name='mapa'),
    path('reportar-problema/', views.reportar_problema, name='reportar_problema'),
    path('cadastrar-veiculo/', views.cadastrar_veiculo, name='cadastrar_veiculo'),
    path('meio-transporte/', views.cadastro_meio_transporte, name='meio_transporte'),
    path('oferecer-carona/', views.oferecer_carona, name='oferecer_carona'),

    path('cadastro/', views.cadastro, name='cadastro'),
    path('cadastro/verificar-email/', views.verificar_email, name='verificar_email'),
    path('rotas/', views.rotas, name='rotas'),
    path('rotas/<int:rota_id>/', views.rota_detalhes, name='rota_detalhes'),
    path('rotas/<int:rota_id>/contatar/', views.contatar, name='contatar'),          # NOVA
    path('usuarios/', views.usuarios, name='usuarios'),
    path('usuarios/<int:usuario_id>/remover/', views.usuario_remover, name='usuario_remover'),
    path('perfil/<int:usuario_id>/', views.perfil, name='perfil'),
    path('grupos/', views.grupos_rota, name='grupos_rota'),                          # NOVA
    path('conta/papel/', views.mudar_papel, name='mudar_papel'),
    path('grupos/<int:grupo_id>/', views.grupo_detalhes, name='grupo_detalhes'),
    path('caronas/<int:carona_id>/', views.carona_detalhes, name='carona_detalhes'),
    path('rotas/<int:rota_id>/ofertar/<int:usuario_id>/', views.ofertar_carona, name='ofertar_carona'),
    path('solicitacoes/<int:solicitacao_id>/confirmar/', views.confirmar_solicitacao, name='confirmar_solicitacao'),
    path('solicitacoes/<int:solicitacao_id>/recusar/', views.recusar_solicitacao, name='recusar_solicitacao'),
    path('grupos/<int:grupo_id>/chat/', views.grupo_chat, name='grupo_chat'),
    path('caronas/<int:carona_id>/confirmada/', views.confirmacao_carona, name='confirmacao_carona'),
    path('conta/editar/', views.editar_perfil, name='editar_perfil'),
    path('perfil/<int:usuario_id>/avaliar/', views.avaliar, name='avaliar'),
]

# Serve as fotos de perfil em desenvolvimento (python manage.py runserver)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)