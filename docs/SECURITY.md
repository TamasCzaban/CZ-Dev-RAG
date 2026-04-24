# CZ-Dev-RAG - Security Model

## Trust boundary

**Tailscale is the perimeter.** There is no application-layer authentication in front of LightRAG, Langfuse, or the MCP server. Access control is enforced entirely by the WireGuard tunnel: only devices authenticated in the `czaban.dev` tailnet can reach ports 9621 and 3000.

Tailscale ACL rules in the admin console (login.tailscale.com/admin/acls) restrict which tailnet devices can reach which ports. The host firewall does not expose these ports to the public internet.

## Data handling

- **Client data never leaves the host.** `data/` (raw input + graph storage) is gitignored and stays on Tamas's 3090.
- **Embeddings and the knowledge graph** are stored in `data/rag_storage/` on the host filesystem and in Backblaze B2 (encrypted at rest via restic - AES-256 with the `RESTIC_PASSWORD` key).
- **Langfuse traces** contain query text and retrieved passages. The Langfuse instance is self-hosted (Docker container on the same host). Traces do not reach Langfuse Cloud.
- **Ollama inference** runs locally on the 3090. No query text, no document content, and no embeddings are sent to external AI APIs.

## Credentials

| Secret                    | Where it lives             | Never committed? |
|---------------------------|---------------------------|-----------------|
| `.env`                    | Host filesystem only       | Yes - gitignored |
| `RESTIC_PASSWORD`         | Windows Machine env var    | Yes |
| `B2_ACCOUNT_KEY`          | Windows Machine env var    | Yes |
| `LANGFUSE_NEXTAUTH_SECRET`| `.env`                     | Yes |
| Tailscale auth key        | One-time use, expires      | Yes |

Rotate `LANGFUSE_NEXTAUTH_SECRET` and `LANGFUSE_SALT` if the host is ever compromised. Rotate the B2 application key if `backup.sh` logs appear in a public location.

## Client disclosure language

For client engagements where documents are ingested into the knowledge base:

> "Your documents are processed locally on CZ Dev infrastructure (an RTX 3090 workstation in Budapest). They are never uploaded to external AI services. Embeddings, graph data, and query traces remain on premises. Remote access by CZ Dev team members is secured via Tailscale (WireGuard). Backups are encrypted with AES-256 before being stored in Backblaze B2."

If a client requires NDA-level guarantees: confirm that `data/input/<client-slug>/` is deleted and `restic forget` + `restic prune` have run before engagement ends, then provide the snapshot ID as evidence.