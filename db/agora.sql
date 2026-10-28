-- Painel "Agora": uma linha por página aberta. Nada aqui identifica ninguém.
-- `sessao` é um identificador aleatório que vive só enquanto a aba está aberta (sessionStorage) e serve
-- apenas para não contar a mesma pessoa duas vezes no "quantas pessoas estão no site agora".
-- Não gravamos IP, nem user-agent, nem cookie. A origem é só o domínio de onde a pessoa veio.
-- Retenção: 48 horas (a limpeza roda junto com a gravação).
CREATE TABLE IF NOT EXISTS evento (
  ts      INTEGER NOT NULL,
  sessao  TEXT    NOT NULL,
  tipo    TEXT    NOT NULL,
  slug    TEXT    NOT NULL,
  titulo  TEXT,
  uf      TEXT,
  partido TEXT,
  origem  TEXT
);
CREATE INDEX IF NOT EXISTS i_evento_ts   ON evento(ts);
CREATE INDEX IF NOT EXISTS i_evento_slug ON evento(slug, ts);
