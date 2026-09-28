---
titre: Tag et brouillon de release ROS
---

# Tag et brouillon de release ROS

Lit la version dans le `package.xml` du paquet, crée le tag correspondant quand la version a augmenté, puis prépare un brouillon de release GitHub. À appeler sur `push` de la branche principale d'un dépôt de paquet ROS.

Fichier : `.github/workflows/ros-tag.yml` · Déclencheur : `workflow_call` · Runner : `group: default` (job `draft-release`, et job `bump-tag` via `generic_workflows`)

## Utilisation

```yaml
name: "Tag"
on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  tag:
    uses: catie-aq/ros_workflows/.github/workflows/ros-tag.yml@main
```

Les deux entrées sont facultatives ; préciser `path` si `package.xml` n'est pas à la racine du dépôt.

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `image` | string | Image Docker du conteneur dans lequel la version est lue et la release préparée. | non | `osrf/ros:humble-desktop-full` |
| `path` | string | Chemin du fichier `package.xml` dont la balise `<version>` est lue. | non | `package.xml` |

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |

Aucune. Le workflow utilise le `GITHUB_TOKEN` de l'exécution.

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Job `bump-tag` : appel de `catie-aq/generic_workflows/.github/workflows/autotag.yml@main` avec `image` = entrée `image` et `version_cmd` = `grep "<version>" <path> | sed -n 's|<version>\(.*\)</version>|\1|p' | tr -d ' '`. Le workflow appelé (runner `group: default`) compare cette version au dernier tag semver du dépôt avec l'action `semver` et pousse le tag (sans préfixe) si la version a augmenté. Il expose les sorties `bump` et `version`.

Job `draft-release` (après `bump-tag`, seulement si `bump == 'true'` ; runner `group: "default"`, conteneur = entrée `image`) :

1. `actions/checkout@v4`.
2. `softprops/action-gh-release@v1` : brouillon de release (`draft: true`) sur le tag `version`, notes générées automatiquement (`generate_release_notes: true`), jeton `GITHUB_TOKEN`.

## Dépendances

- `catie-aq/generic_workflows/.github/workflows/autotag.yml@main` (qui utilise lui-même l'action `catie-aq/generic_workflows/semver@main`).
- Actions tierces : `actions/checkout@v4`, `softprops/action-gh-release@v1`.

## Points d'attention

- Le nom du workflow parle de « pre-release » mais le code crée un brouillon (`draft: true`), pas une pré-release : il faut le publier à la main.
- Aucun bloc `permissions` dans le workflow : le dépôt appelant doit accorder `contents: write` au `GITHUB_TOKEN` pour que le tag et la release puissent être créés.
- `autotag.yml` utilise `::set-output`, déprécié par GitHub.
- `autotag.yml` saute le job `bump-tag` quand l'acteur est `dependabot[bot]` ; `draft-release` est alors sauté aussi.
- `softprops/action-gh-release@v1` est une version ancienne de l'action.
- Image par défaut Humble (`osrf/ros:humble-desktop-full`), alors que `ros2.yml` ne compile plus sur Humble ; l'image ne sert qu'à lire `package.xml` et à préparer la release.
- `version_cmd` garde toutes les lignes contenant `<version>` : un `package.xml` qui en contient plusieurs produirait une version invalide.
