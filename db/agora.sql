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

-- Sugestões enviadas pelo formulário de /sugestoes/. Guardamos o texto, um contato OPCIONAL que a própria pessoa
-- escreve se quiser resposta, a página de onde veio e o id de sessão (para limitar envio em sequência).
-- Sem IP, sem user-agent, sem cookie. Não publicamos nada disso no site sem leitura humana antes.
CREATE TABLE IF NOT EXISTS sugestao (
  ts      INTEGER NOT NULL,
  texto   TEXT    NOT NULL,
  contato TEXT,
  pagina  TEXT,
  sessao  TEXT
);
CREATE INDEX IF NOT EXISTS i_sugestao_ts ON sugestao(ts);
