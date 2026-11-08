# Nuvem de palavras ao vivo

O público lê o QR code, responde uma pergunta no celular e a resposta entra na
nuvem projetada. Quanto mais vezes um termo aparece, maior ele fica. A nuvem se
atualiza sozinha a cada 3 segundos.

| Endereço | Para quê |
|---|---|
| `/` | a nuvem: projetar em tela cheia (F11); `?tema=escuro` para fundo escuro |
| `/r` | página de resposta, para onde o QR leva |
| `/admin` | trocar a pergunta, remover um termo, limpar as respostas, baixar o QR |
| `/qr.png?baixar=1` | QR em alta resolução para slide ou impressão |

Na tela da nuvem o QR fica no canto inferior direito; clique nele para ampliar.
`qr-nuvem.png` e `qr-nuvem.svg`, na raiz, já apontam para
`https://nuvem.agilematuritymodel.com/r` e servem para montar slide antes do deploy.

## Como a resposta vira termo

- A resposta inteira é um termo: "falta de clareza" conta como uma coisa só.
- Caixa e acento não separam: "Organizada", "organizada" e "ORGANIZADA" somam
  juntas, e a nuvem mostra a grafia mais usada.
- Pontuação nas pontas é descartada. Limite de 40 caracteres.

## Uma resposta por pessoa

Na primeira resposta o navegador da pessoa recebe um cookie. Se ela abrir o QR
de novo, vê "Você já respondeu" e a resposta que deu. O controle é por
navegador, não é à prova de fraude: uma janela anônima ou outro navegador
respondem outra vez. Bloquear por IP não serviria, porque na rede do escritório
todo mundo sai pelo mesmo IP.

**Limpar todas** no `/admin` começa uma rodada nova: todos podem responder de
novo. **Remover** um termo libera quem o escreveu.

## Rodar local

`run.bat` cria o `.venv` na primeira vez e sobe em http://127.0.0.1:8010
(admin: qualquer usuário, senha `admin`).

## Variáveis

| Variável | O que faz | Padrão |
|---|---|---|
| `DATA_DIR` | pasta do SQLite (`/data` no Railway) | `./data` |
| `ADMIN_PASSWORD` | senha do `/admin`; sem ela o `/admin` fica desligado | — |
| `URL_PUBLICA` | domínio que vai no QR | host da requisição |
| `PERGUNTA` | pergunta inicial; só vale no primeiro boot, depois quem manda é o `/admin` | "Me conta em uma palavra, qual a sua percepção em relação à gestão dos nossos projetos atualmente?" |

Publicação: [DEPLOY.md](DEPLOY.md).
