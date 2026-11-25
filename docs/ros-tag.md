---
titre: Tag et brouillon de release ROS
---

# Tag et brouillon de release ROS

Lit la version dans le `package.xml` du paquet, crée le tag correspondant quand la version a augmenté, puis prépare un brouillon de release GitHub. En option, le corps de la release reprend la section de la version dans `CHANGELOG.md`. À appeler sur `push` de la branche principale d'un dépôt de paquet ROS.

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

Toutes les entrées sont facultatives ; préciser `path` si `package.xml` n'est pas à la racine du dépôt.

Exemple avec notes de version tirées du changelog :

```yaml
jobs:
  tag:
    uses: catie-aq/ros_workflows/.github/workflows/ros-tag.yml@main
    with:
      path: "minipock/package.xml"
      changelog: "CHANGELOG.md"
```

Les paquets Debian et la documentation d'API ne passent pas par ce workflow : le dépôt appelle [`ros2-release.yml`](ros2-release.md) à part (exemple dans sa doc).

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `image` | string | Image Docker du conteneur dans lequel la version est lue et la release préparée. | non | `osrf/ros:humble-desktop-full` |
| `path` | string | Chemin du fichier `package.xml` dont la balise `<version>` est lue. | non | `package.xml` |
| `changelog` | string | Chemin d'un `CHANGELOG.md` dont la section de la version taguée devient le corps de la release. Vide : notes générées par GitHub. | non | `""` |
| `toolkit-ref` | string | Révision de `catie-aq/ros_workflows` dont le script de changelog est utilisé, si `changelog` est renseigné. | non | `main` |

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

Job `draft-release` (après `bump-tag`, seulement si `bump-tag` a réussi et que `bump == 'true'` ; runner `group: "default"`, conteneur = entrée `image`) :

1. `actions/checkout@v4`.
2. Si `changelog` : extraction de `catie-aq/ros_workflows` (révision `toolkit-ref`) et `scripts/changelog_section.py <changelog> <version>`. La section commence au titre de niveau 2 de la version (`## [2.3.0](lien) - date`, `## v2.3.0` ou `## 2.3.0`) et s'arrête au titre de niveau 2 suivant. Section absente : avertissement et notes générées par GitHub.
3. `softprops/action-gh-release@v2.6.2` : brouillon de release (`draft: true`) sur le tag `version`, corps = section du changelog s'il y en a une, sinon notes générées (`generate_release_notes`), jeton `GITHUB_TOKEN`.

## Dépendances

- `catie-aq/generic_workflows/.github/workflows/autotag.yml@main` (qui utilise lui-même l'action `catie-aq/generic_workflows/semver@main`).
- `scripts/changelog_section.py` de `catie-aq/ros_workflows` (si `changelog`).
- Actions tierces : `actions/checkout@v4`, `softprops/action-gh-release@v2.6.2`.

## Points d'attention

- Le nom du workflow parle de « pre-release » mais le code crée un brouillon (`draft: true`), pas une pré-release : il faut le publier à la main.
- Aucun bloc `permissions` dans le workflow : le dépôt appelant doit accorder `contents: write` au `GITHUB_TOKEN` pour que le tag et la release puissent être créés. Rien d'autre n'est nécessaire, `changelog` compris.
- `autotag.yml` utilise `::set-output`, déprécié par GitHub.
- `autotag.yml` saute le job `bump-tag` quand l'acteur est `dependabot[bot]` ; `draft-release` est alors sauté aussi.
- `softprops/action-gh-release` est passé de `v1` (Node 16, refusé par actionlint) à `v2.6.2` ; les entrées utilisées sont les mêmes. Sans `changelog`, les jobs sont ceux d'avant.
- Les tags poussés par `autotag.yml` avec le `GITHUB_TOKEN` ne déclenchent pas d'autre workflow (`on: push: tags`) : c'est la publication du brouillon, faite à la main, qui peut lancer `ros2-release.yml` (`on: release: types: [published]`).
- Image par défaut Humble (`osrf/ros:humble-desktop-full`), alors que `ros2.yml` ne compile plus sur Humble ; l'image ne sert qu'à lire `package.xml` et à préparer la release.
- `version_cmd` garde toutes les lignes contenant `<version>` : un `package.xml` qui en contient plusieurs produirait une version invalide.
