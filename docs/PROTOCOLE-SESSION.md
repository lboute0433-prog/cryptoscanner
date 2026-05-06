# Protocole de Session — Memory System

Comment utiliser le système de mémoire de CryptoScanner pour apprendre et s'améliorer.

## Début de Session

```
/recall cryptoscanner
```

Claude charge:
1. Contexte courant (`memory/projets/cryptoscanner/contexte.md`)
2. Dernières archives (`memory/archives/`)
3. Vos fiches personnelles (`references/{articles,donnees,idees}/`)

**Résultat** : Claude comprend où on en est et votre contexte.

## Pendant la Session

### Créer des Fiches

À tout moment, créez des fiches dans `references/`:

**Article** (analyse, rapport):
```
references/articles/titre-description.md
```

**Donnée** (stats, métriques):
```
references/donnees/metriques-contexte.md
```

**Idée** (brainstorm, TODO):
```
references/idees/categorie-idee.md
```

### Claude Lit Vos Fiches

Claude utilise vos fiches pour:
- Contextualiser ses réponses
- Adapter ses suggestions à votre contexte réel
- Mémoriser vos priorités et idées

**Plus vous remplissez `references/`, mieux Claude vous comprend.**

## Fin de Session

```
/archive
```

Claude crée une archive immuable:
- Date/heure de la session
- Travail effectué
- Résultats/décisions
- Prochaines étapes

Puis met à jour `memory/projets/cryptoscanner/contexte.md` avec l'état courant.

**Important** : `/archive` AVANT `/clear` !

Sans archive, le contexte est **perdu définitivement**.

## Flux Complet

```
Début Session
    ↓
/recall cryptoscanner
    ↓
Claude charge contexte + fiches
    ↓
Travail / Création de fiches / Discussions
    ↓
Fin Session
    ↓
/archive
    ↓
Claude sauvegarde archive + met à jour contexte
    ↓
Session terminée ✅
```

## Exemple de Session Complète

### 1. Démarrage
```
claude> /recall cryptoscanner
✅ Contexte chargé: Production live, API Mix Phase 3 complète
✅ Dernière archive: 2026-04-24-api-mix-phase3-production.md
✅ Fiches trouvées: 0 (aucune fiches dans references/ encore)
```

### 2. Travail
```
Vous créez: references/idees/features-phase4.md
Vous créez: references/donnees/metriques-hetzner.md

Claude adapte ses suggestions basées sur ces fiches.
```

### 3. Fin de Session
```
claude> /archive

✅ Archive créée: 2026-04-25-brainstorm-features.md
✅ Contexte mis à jour: phase, dernière-session, status
✅ Prêt pour prochaine session
```

## Bonnes Pratiques

### ✅ DO
- Créer une fiche quand c'est important pour toi
- Mettre à jour fiches si contexte change
- Utiliser noms descriptifs et français
- Archiver à la fin de chaque session

### ❌ DON'T
- Oublier `/archive` (= perte de contexte)
- Créer fiches en anglais (convention: français)
- Garder fiches obsolètes sans les nettoyer
- Créer trop de fiches non-essentielles (qualité > quantité)

## Structure pour 100% Français

**Tous les fichiers** dans les dossiers suivants doivent être **100% français**:

```
memory/
├── projets/
│   └── cryptoscanner/
│       └── contexte.md          (français)
├── archives/
│   └── *.md                     (français)
└── agents/
    └── notes.md                 (français)

references/
├── articles/                    (français)
├── donnees/                     (français)
└── idees/                       (français)

CONVENTION-FRANCAIS.md           (français)
PROTOCOLE-SESSION.md             (français)
```

Code Python/JS peut rester multilingue (conventions standards).

---

**Protocole établi** : 2026-04-24
**Valide à partir de** : Session 2026-04-25+
**Langue** : Français
