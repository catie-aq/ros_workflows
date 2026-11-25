---
titre: Tag et brouillon de release ROS
---

# Tag et brouillon de release ROS

Lit la version dans le `package.xml` du paquet, crée le tag correspondant quand la version a augmenté, puis prépare un brouillon de release GitHub. En option, le corps de la release reprend la section de la version dans `CHANGELOG.md`, et les paquets Debian et la documentation d'API sont joints à la release. À appeler sur `push` de la branche principale d'un dépôt de paquet ROS.

Fichier : `.github/workflows/ros-tag.yml` · Déclencheur : `workflow_call` · Runner : `group: default` (job `bump-tag` via `generic_workflows`, et job `draft-release` sauf entrée `runner`) ; entrée `runner` ou `sonu-github-arc` (job `assets`)

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

Toutes les entrées sont facultatives ; préciser `path` si `package.xml` n'est pas à la racine du dépôt.

Exemple avec notes de version tirées du changelog et livrables joints :

```yaml
jobs:
  tag:
    uses: catie-aq/ros_workflows/.github/workflows/ros-tag.yml@main
    with:
      path: "minipock/package.xml"
      changelog: "CHANGELOG.md"
      assets: true
      assets-distribution: "jazzy"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `image` | string | Image Docker du conteneur dans lequel la version est lue et la release préparée. | non | `osrf/ros:humble-desktop-full` |
| `path` | string | Chemin du fichier `package.xml` dont la balise `<version>` est lue. | non | `package.xml` |
| `changelog` | string | Chemin d'un `CHANGELOG.md` dont la section de la version taguée devient le corps de la release. Vide : notes générées par GitHub. | non | `""` |
| `assets` | boolean | Joint à la release les paquets Debian (bloom) et la documentation d'API (rosdoc2), produits par `ros2-release.yml`. | non | `false` |
| `assets-distribution` | string | Distribution ROS 2 des paquets Debian joints. | non | `jazzy` |
| `assets-packages` | string | Paquets à empaqueter et documenter, séparés par des espaces. Vide : tous. | non | `""` |
| `runner` | string | Runner du job `draft-release` (et du job `assets`). Vide : groupe de runners `default`, comme avant. | non | `""` |
| `toolkit-ref` | string | Révision de `catie-aq/ros_workflows` dont les scripts sont utilisés (changelog, livrables). | non | `main` |

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |

Aucune. Le workflow utilise le `GITHUB_TOKEN` de l'exécution.

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |
| `bump` | `true` si la version a augmenté et que le tag a été créé. |
| `version` | Version lue dans `package.xml`. |

## Fonctionnement

Job `bump-tag` : appel de `catie-aq/generic_workflows/.github/workflows/autotag.yml@main` avec `image` = entrée `image` et `version_cmd` = `grep "<version>" <path> | sed -n 's|<version>\(.*\)</version>|\1|p' | tr -d ' '`. Le workflow appelé (runner `group: default`) compare cette version au dernier tag semver du dépôt avec l'action `semver` et pousse le tag (sans préfixe) si la version a augmenté. Il expose les sorties `bump` et `version`.

Job `assets` (si `assets` et `bump == 'true'`) : appel de `catie-aq/ros_workflows/.github/workflows/ros2-release.yml@main` (voir [ros2-release](ros2-release.md)) avec `distribution` = `assets-distribution`, `packages` = `assets-packages`, runner `runner` sinon `sonu-github-arc`.

Job `draft-release` (après `bump-tag` et `assets`, seulement si `bump == 'true'` et que `assets` n'a pas échoué ; runner `runner`, sinon `group: "default"` ; conteneur = entrée `image`) :

1. `actions/checkout@v4`.
2. Si `changelog` : extraction de `catie-aq/ros_workflows` (révision `toolkit-ref`) et `scripts/changelog_section.py <changelog> <version>`. La section commence au titre de niveau 2 de la version (`## [2.3.0](lien) - date`, `## v2.3.0` ou `## 2.3.0`) et s'arrête au titre de niveau 2 suivant. Section absente : avertissement et notes générées par GitHub.
3. Si `assets` a réussi : téléchargement des artefacts, copie des `.deb` et archive `api-docs-<version>.tar.gz`.
4. `softprops/action-gh-release@v2` : brouillon de release (`draft: true`) sur le tag `version`, corps = section du changelog s'il y en a une, sinon notes générées (`generate_release_notes`), fichiers joints si `assets`, jeton `GITHUB_TOKEN`.

## Dépendances

- `catie-aq/generic_workflows/.github/workflows/autotag.yml@main` (qui utilise lui-même l'action `catie-aq/generic_workflows/semver@main`).
- `catie-aq/ros_workflows/.github/workflows/ros2-release.yml@main` (si `assets`) et `scripts/changelog_section.py` (si `changelog`).
- Actions tierces : `actions/checkout@v4`, `actions/download-artifact@v4`, `softprops/action-gh-release@v2`.

## Points d'attention

- Le nom du workflow parle de « pre-release » mais le code crée un brouillon (`draft: true`), pas une pré-release : il faut le publier à la main.
- Aucun bloc `permissions` dans le workflow : le dépôt appelant doit accorder `contents: write` au `GITHUB_TOKEN` pour que le tag et la release puissent être créés.
- `autotag.yml` utilise `::set-output`, déprécié par GitHub.
- `autotag.yml` saute le job `bump-tag` quand l'acteur est `dependabot[bot]` ; `draft-release` est alors sauté aussi.
- `softprops/action-gh-release` est passé de `v1` (Node 16, refusé par actionlint) à `v2` ; les entrées utilisées sont les mêmes.
- Le job `assets` appelle `ros2-release.yml@main` en dur : GitHub n'accepte pas de révision variable dans `uses`.
- Image par défaut Humble (`osrf/ros:humble-desktop-full`), alors que `ros2.yml` ne compile plus sur Humble ; l'image ne sert qu'à lire `package.xml` et à préparer la release.
- `version_cmd` garde toutes les lignes contenant `<version>` : un `package.xml` qui en contient plusieurs produirait une version invalide.
