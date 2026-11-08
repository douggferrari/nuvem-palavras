# Publicar em nuvem.agilematuritymodel.com

Mesmo caminho do KMM: GitHub → Railway → DNS na Hostinger.

## 1. GitHub

Criar um repositório **vazio** (sem README) em github.com, por exemplo
`douggferrari/nuvem-palavras`. Depois, nesta pasta:

```bash
git init -b main
git add .
git commit -m "Nuvem de palavras ao vivo (v1.0)"
git remote add origin https://github.com/douggferrari/nuvem-palavras.git
git push -u origin main
```

## 2. Railway

1. **New → GitHub Repo → nuvem-palavras**, como serviço novo no projeto do KMM
   (`just-delight`) ou num projeto próprio. O `railway.json` já define o start.
   Não confundir com `meticulous-wholeness`, que é o site.
2. No serviço: **+ New Volume** montado em `/data`. Sem volume, cada deploy
   apaga as respostas.
3. **Variables**:

   | Variável | Valor |
   |---|---|
   | `DATA_DIR` | `/data` |
   | `ADMIN_PASSWORD` | uma senha forte para o `/admin` |
   | `URL_PUBLICA` | `https://nuvem.agilematuritymodel.com` |
   | `PERGUNTA` | opcional: a pergunta inicial |

4. **Settings → Networking → Custom Domain** → `nuvem.agilematuritymodel.com`.
   O Railway mostra dois registros DNS; anote os valores.

## 3. Hostinger (hPanel → Domínios → agilematuritymodel.com → DNS)

| Tipo | Nome | Valor |
|---|---|---|
| CNAME | `nuvem` | o `xxxx.up.railway.app` mostrado pelo Railway |
| TXT | `_railway-verify.nuvem` | o valor mostrado pelo Railway |

Só o CNAME não basta: sem o TXT o Railway não valida o domínio (aconteceu no KMM).
O certificado HTTPS sai sozinho depois da validação.

## 4. Conferir

- No celular, **com dados móveis**: ler `qr-nuvem.png`, responder, ver o termo
  aparecer em `https://nuvem.agilematuritymodel.com`. No PC, o Avast pode
  marcar o site como "não seguro" mesmo com tudo certo.
- Versão no ar, sem logar:

  ```bash
  curl -s https://nuvem.agilematuritymodel.com/ | grep -o 'estilo.css?v=[0-9.]*'
  ```

  O número é o `VERSAO` de `app/main.py`; suba esse número a cada mudança.

Se o push entra e o site continua na versão antiga, olhar o billing do Railway
primeiro: ele pausa build e mantém o container velho no ar.

## Antes de cada sessão

`/admin` → ajustar a pergunta → **Limpar todas**, que também libera todo mundo
para responder de novo. Durante a sessão, um termo inadequado sai com
**Remover**, e quem o escreveu pode responder outra vez.

Para testar no celular sem gastar a sua resposta da sessão, use uma janela
anônima e apague o teste com **Remover** ou **Limpar todas**.
