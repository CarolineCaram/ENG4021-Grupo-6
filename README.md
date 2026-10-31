# 🚗 VaiJunto - Caronas Universitárias

Aplicação web desenvolvida em **Django** para caronas universitárias (Disciplina ENG4021 - Grupo 6).

O VaiJunto conecta estudantes que fazem o mesmo trajeto até a faculdade, para que possam oferecer e combinar caronas de forma organizada e segura.

## Funcionalidades

- Cadastro e login de usuários
- Cadastro de veículo e meio de transporte
- Oferta de rotas (origem, horário, transporte e vagas) 
- Busca de rotas por origem
- Grupos por rota, com mensagens entre os participantes
- Caronas agendadas, com lista de passageiros
- Perfil de usuário e remoção de usuário
- Interface administrativa para consultar e editar todos os dados

## Tecnologias

- Python 3.12
- Django 6.1
- SQLite
- HTML e CSS

## Como executar

Todos os comandos são executados no terminal, a partir da raiz do repositório.

1. Entre na pasta do projeto:
   ```bash
   cd Projeto
   ```
2. Crie e ative o ambiente virtual (se ainda não existir):
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   O texto `(venv)` deve aparecer no início do terminal.
3. Instale o Django:
   ```bash
   pip install django
   ```
4. Crie as tabelas do banco de dados:
   ```bash
   python manage.py migrate
   ```
5. Popule o banco com os dados de exemplo:
   ```bash
   python PopulaBanco.py
   ```
6. Crie um superusuário para acessar a área administrativa:
   ```bash
   python manage.py createsuperuser
   ```
7. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```
8. Acesse: `http://localhost:8000/`

No GitHub Codespaces, abra a aba **Portas**, deixe a porta 8000 como **Pública** e clique no endereço gerado.

## Páginas do site

| Caminho | Descrição |
|---|---|
| `/` | Página inicial |
| `/login/` | Login |
| `/cadastro/` | Cadastro de usuário |
| `/recuperar-senha/` | Recuperação de senha |
| `/como-funciona/` | Como funciona |
| `/mapa/` | Mapa |
| `/rotas/` | Lista de rotas (aceita `?q=` para buscar por origem) |
| `/rotas/<id>/` | Detalhes de uma rota |
| `/usuarios/` | Lista de usuários |
| `/perfil/<id>/` | Perfil de um usuário |
| `/grupos/<id>/` | Grupo de uma rota, com membros e mensagens |
| `/caronas/<id>/` | Detalhes de uma carona |
| `/oferecer-carona/` | Oferecer carona |
| `/cadastrar-veiculo/` | Cadastro de veículo |
| `/reportar-problema/` | Reportar problema |
| `/admin/` | Interface administrativa |

## Banco de dados

O banco (`db.sqlite3`) segue a modelagem de dados do projeto, com 8 tabelas principais mais 2 tabelas de ligação:

| Tabela | Descrição |
|---|---|
| `instituicao` | Instituições de ensino |
| `usuario` | Usuários do sistema |
| `rota` | Rotas oferecidas pelos motoristas |
| `solicitacao` | Pedidos de participação em uma rota |
| `grupo` | Grupo de conversa de cada rota |
| `mensagem` | Mensagens enviadas nos grupos |
| `carona` | Caronas agendadas |
| `avaliacao` | Avaliações entre usuários após a carona |
| `grupo_usuario` | Ligação entre grupos e usuários |
| `carona_passageiro` | Ligação entre caronas e passageiros |

Os dados de exemplo são inseridos pelo script `PopulaBanco.py`. Ele pode ser executado mais de uma vez sem duplicar registros. As senhas de teste dos usuários de exemplo são `senha123`, armazenadas como hash.

## Estrutura do projeto

```
ENG4021-Grupo-6/
├── README.md
├── Protótipos/              # protótipos das telas
└── Projeto/
    ├── manage.py
    ├── PopulaBanco.py       # popula o banco com dados de exemplo
    ├── db.sqlite3
    └── vai_junto/
        ├── models.py        # tabelas do banco
        ├── views.py         # lógica das páginas
        ├── urls.py          # rotas do site
        ├── admin.py         # interface administrativa
        ├── settings.py      # configurações
        ├── migrations/
        ├── templates/       # páginas HTML
        └── static/          # CSS, imagens e JS
```

## Equipe

Grupo 6 - ENG4021

- Caroline Caram
- Giovanna Monteiro
- Ana Clara Regal
- Joana Arrais
- Isabela Jaegger