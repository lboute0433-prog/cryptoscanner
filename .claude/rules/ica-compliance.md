# Règle — Conformité ICA

Toute création dans ce système suit le Framework ICA (Instruction · Connaissance · Action).

## Obligations

- Tout agent, command, skill ou prompt est structuré en I puis C puis A, dans cet ordre.
- I définit l'identité : rôle, responsabilités, limites, ton.
- C définit les connaissances : contexte, données, références, skills.
- A définit les actions : ce que l'entité fait, son format de livraison, ses outils.

## Validation

Avant de valider toute création, vérifier :
- [ ] I est défini (rôle + limites claires)
- [ ] C est défini (contexte + références)
- [ ] A est défini (actions + format de sortie)
- [ ] L'entité est autonome : I + C + A = agent capable d'agir

## Source de vérité

- Framework complet : `memory/framework/ICA.md`
- Pilier Instruction : `memory/framework/I.md`
- Pilier Connaissance : `memory/framework/C.md`
- Pilier Action : `memory/framework/A.md`

## Règle d'Or

```
I sans C  = Agent aveugle (il sait qui il est mais manque de contexte)
C sans I  = Agent perdu (il a les infos mais ne sait pas les filtrer)
I+C sans A = Agent paralysé (il comprend mais ne peut pas agir)
I + C + A = Agent autonome
```
