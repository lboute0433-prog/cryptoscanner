# Guide — Configuration Obsidian

Pour voir **tous les fichiers** (memory/, references/, conventions, protocoles) dans Obsidian, suivez ces étapes.

## Configuration Actuelle

Obsidian regarde probablement vers le dossier `knowledge/` seulement.

## Reconfiguration Recommandée

### Option 1 : Changer le Vault (Recommandé ✅)

1. **Ouvrir Obsidian**
2. **Cliquer** sur le logo Obsidian (en haut à gauche)
3. **Sélectionner** "Ouvrir un autre vault"
4. **Choisir** le dossier : `C:\Users\loyan\Documents\Antigravity\cryptoscanner`
5. **Confirmer**

**Résultat** : Obsidian affichera tout le contenu :
```
Antigravity--cryptoscanner/
├── memory/          (archives, contexte, notes)
├── references/      (articles, données, idées)
├── knowledge/       (existing files)
├── CONVENTION-FRANCAIS.md
├── PROTOCOLE-SESSION.md
└── GUIDE-OBSIDIAN.md
```

### Option 2 : Ajouter des Dossiers au Vault Existant

Si vous préférez garder `knowledge/` comme vault principal:

1. **Settings** → **Files & Links**
2. **Excluded Files** : vérifier que `memory/`, `references/` ne sont PAS dans la liste
3. **Reload** l'application (Ctrl+R ou Cmd+R)

---

## Structure à Explorer dans Obsidian

Une fois reconfigurée, vous verrez:

### 📁 memory/
- `contexte.md` — état courant du projet (lire en premier!)
- `archives/` — historiques immuables des sessions

### 📁 references/
- `articles/` — vos analyses, rapports
- `données/` — vos stats, métriques
- `idées/` — brainstorm, TODO, concepts

### 📄 Fichiers Racine
- `CONVENTION-FRANCAIS.md` — règles 100% français
- `PROTOCOLE-SESSION.md` — comment utiliser le système
- `GUIDE-OBSIDIAN.md` — ce fichier

---

## Utilisation dans Obsidian

### Lire le Contexte
Ouvrez `memory/contexte.md` pour comprendre où en est le projet.

### Créer une Nouvelle Fiche
1. **Créer un fichier** dans `references/articles/`, `references/donnees/`, ou `references/idées/`
2. **Nommer** en français avec `-` : `titre-description.md`
3. **Utiliser les templates** : regardez les EXEMPLE.md dans chaque dossier
4. **Sauvegarder** — Claude la trouvera automatiquement

### Naviguer avec Wikilinks
```markdown
[[memory/contexte]]     → Lien vers contexte
[[references/articles/mon-article]]  → Lien vers votre fiche
```

---

## Avantages Obsidian Configuré Correctement

- ✅ Voir tout en un seul endroit
- ✅ Naviguer avec wikilinks
- ✅ Éditer vos fiches directement
- ✅ Organiser vos notes en graphique
- ✅ Rechercher rapidement dans tout

---

## Troubleshooting

### "Je ne vois pas les dossiers"
→ Relancer Obsidian ou faire Ctrl+R (reload)

### "Les fichiers sont grisés"
→ Vérifier que les chemins ne sont pas exclus (Settings → Files & Links)

### "Les wikilinks ne fonctionnent pas"
→ S'assurer que "Strict line breaks" est OFF (Settings → Editor)

---

**Créé** : 2026-04-24
**Objective** : Configuration optimale d'Obsidian pour CryptoScanner
**Langue** : Français
