-- UniRide - Banco de dados (SQLite)
-- Mesma modelagem do diagrama, adaptada para SQLite

DROP TABLE IF EXISTS avaliacao;
DROP TABLE IF EXISTS carona_passageiro;
DROP TABLE IF EXISTS carona;
DROP TABLE IF EXISTS mensagem;
DROP TABLE IF EXISTS grupo_usuario;
DROP TABLE IF EXISTS grupo;
DROP TABLE IF EXISTS solicitacao;
DROP TABLE IF EXISTS rota;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS instituicao;

CREATE TABLE instituicao (
    id_instituicao INTEGER PRIMARY KEY AUTOINCREMENT,
    nome           TEXT NOT NULL,
    sigla          TEXT NOT NULL UNIQUE
);

CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    matricula  TEXT NOT NULL UNIQUE,
    senha      TEXT NOT NULL  -- guarda o HASH da senha
);

CREATE TABLE rota (
    id_rota        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario     INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_instituicao INTEGER NOT NULL REFERENCES instituicao(id_instituicao),
    origem         TEXT NOT NULL,
    referencia     TEXT,
    horario        TEXT NOT NULL,
    transporte     TEXT NOT NULL
                   CHECK (transporte IN ('carro', 'moto', 'onibus', 'a_pe', 'outro')),
    vagas          INTEGER NOT NULL CHECK (vagas >= 0)
);

CREATE TABLE solicitacao (
    id_rota        INTEGER NOT NULL REFERENCES rota(id_rota) ON DELETE CASCADE,
    id_solicitante INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'pendente'
                   CHECK (status IN ('pendente', 'aceita', 'recusada', 'cancelada')),
    criada_em      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    respondida_em  TEXT,
    PRIMARY KEY (id_rota, id_solicitante)
);

CREATE TABLE grupo (
    id_grupo INTEGER PRIMARY KEY AUTOINCREMENT,
    id_rota  INTEGER NOT NULL UNIQUE REFERENCES rota(id_rota) ON DELETE CASCADE,
    nome     TEXT NOT NULL
);

CREATE TABLE grupo_usuario (
    id_grupo   INTEGER NOT NULL REFERENCES grupo(id_grupo) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    PRIMARY KEY (id_grupo, id_usuario)
);

CREATE TABLE mensagem (
    id_mensagem INTEGER PRIMARY KEY AUTOINCREMENT,
    id_grupo    INTEGER NOT NULL REFERENCES grupo(id_grupo) ON DELETE CASCADE,
    id_usuario  INTEGER NOT NULL REFERENCES usuario(id_usuario),
    texto       TEXT NOT NULL,
    enviada_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE carona (
    id_carona INTEGER PRIMARY KEY AUTOINCREMENT,
    id_grupo  INTEGER NOT NULL REFERENCES grupo(id_grupo) ON DELETE CASCADE,
    id_rota   INTEGER NOT NULL REFERENCES rota(id_rota),
    data      TEXT NOT NULL,
    status    TEXT NOT NULL DEFAULT 'agendada'
              CHECK (status IN ('agendada', 'em_andamento', 'concluida', 'cancelada'))
);

CREATE TABLE carona_passageiro (
    id_carona  INTEGER NOT NULL REFERENCES carona(id_carona) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    PRIMARY KEY (id_carona, id_usuario)
);

CREATE TABLE avaliacao (
    id_avaliacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_carona    INTEGER NOT NULL REFERENCES carona(id_carona) ON DELETE CASCADE,
    id_avaliador INTEGER NOT NULL REFERENCES usuario(id_usuario),
    id_avaliado  INTEGER NOT NULL REFERENCES usuario(id_usuario),
    aprovou      INTEGER NOT NULL CHECK (aprovou IN (0, 1)),
    criada_em    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (id_avaliador <> id_avaliado),
    UNIQUE (id_carona, id_avaliador, id_avaliado)
);

CREATE INDEX idx_rota_usuario       ON rota(id_usuario);
CREATE INDEX idx_rota_instituicao   ON rota(id_instituicao);
CREATE INDEX idx_solicitacao_user   ON solicitacao(id_solicitante);
CREATE INDEX idx_mensagem_grupo     ON mensagem(id_grupo);
CREATE INDEX idx_carona_grupo       ON carona(id_grupo);
CREATE INDEX idx_avaliacao_avaliado ON avaliacao(id_avaliado);