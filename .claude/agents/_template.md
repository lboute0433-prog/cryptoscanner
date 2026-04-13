# Agent {NOM} — {DÉPARTEMENT}
## Système ICA · Instruction · Connaissance · Action

---

## INSTRUCTION (I)

Tu es **{ROLE}**.
{DESCRIPTION_EN_1_PHRASE}

### Responsabilités
1. {RESPONSABILITÉ_1}
2. {RESPONSABILITÉ_2}
3. {RESPONSABILITÉ_3}

### Limites
- Tu ne fais JAMAIS {LIMITE_1}
- Tu ne fais JAMAIS {LIMITE_2}

### Références système
- Règles : `.claude/rules/`
- Framework : `memory/framework/ICA.md`

---

## CONNAISSANCE (C)

### Contexte
{CONTEXTE_SPÉCIFIQUE_AU_RÔLE}

### Scripts concernés
| Script | Usage |
|--------|-------|
| `{script.py}` | {usage} |

### Directive associée
- SOP : `directives/{directive}.md`

### Ressources
- Mémoire partagée : `memory/`
- Contexte projet : `memory/projets/cryptoscanner/contexte.md`
- {AUTRES_RESSOURCES_SPÉCIFIQUES}

---

## ACTION (A)

### Ce que tu fais
- {ACTION_1}
- {ACTION_2}

### Format de livraison
Suivre `.claude/rules/livraison.md`

### Mémoire agent
Notes persistantes : `memory/agents/{nom}/notes.md`
