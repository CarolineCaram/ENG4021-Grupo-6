from django.shortcuts import render
from .models import Rota

def lista_rotas(request):
    rotas = Rota.objects.all()
    return render(request, 'rotas.html', {'rotas': rotas})