---
titre: Paquets Debian et documentation d'API ROS 2
---

# Paquets Debian et documentation d'API ROS 2

Produit les livrables d'une version d'un dépôt ROS 2 : paquets Debian générés par bloom, comme le buildfarm ROS, et documentation d'API générée par rosdoc2, l'outil de docs.ros.org. Les deux sortent en artefacts. Appelé par `ros-tag.yml` (entrée `assets`) pour les joindre à la release, ou seul, par exemple en `workflow_dispatch`.

Fichier : `.github/workflows/ros2-release.yml` · Déclencheur : `workflow_call` · Runner : entrée `runner` (`sonu-github-arc` par défaut)

## Utilisation

```yaml
name: "Packages"
on:
  workflow_dispatch:

jobs:
  packages:
    uses: catie-aq/ros_workflows/.github/workflows/ros2-release.yml@main
    with:
      distribution: "jazzy"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `runner` | string | Runner des jobs. | non | `sonu-github-arc` |
| `distribution` | string | Distribution ROS 2 des paquets Debian. | non | `jazzy` |
| `image` | string | Image des jobs. Vide : `ros:<distribution>-ros-base`. | non | `""` |
| `packages` | string | Paquets à empaqueter (avec leurs dépendances du workspace) et à documenter. Vide : tous. | non | `""` |
| `submodules` | string | Sous-modules : `false`, `true` ou `recursive`. | non | `false` |
| `repos-file` | string | Chemin, dans le dépôt, d'un fichier `.repos` importé avec `vcs`. | non | `""` |
| `skip-keys` | string | Clés rosdep ignorées. | non | `""` |
| `debs` | boolean | Construit les paquets Debian (artefact `debs-<distribution>`). | non | `true` |
| `docs` | boolean | Construit la documentation d'API (artefact `api-docs`). | non | `true` |
| `toolkit-ref` | string | Révision de `catie-aq/ros_workflows` dont les actions et scripts sont utilisés. | non | `main` |

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |
| `token` | Jeton pour les sous-modules et dépôts amont privés. Vide : `GITHUB_TOKEN`. | non |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |
| `debs-artifact` | Nom de l'artefact des `.deb`, vide s'il n'est pas construit. |
| `docs-artifact` | Nom de l'artefact de la documentation HTML, vide s'il n'est pas construite. |

## Fonctionnement

Job `debs` (si `debs`, conteneur `image` sinon `ros:<distribution>-ros-base`) : extraction dans `ws/src/<dépôt>`, [`ros2_setup`](ros2_setup.md) (dépendances de compilation par rosdep), puis [`ros2_debs`](ros2_debs.md) : pour chaque paquet, dans l'ordre des dépendances, `bloom-generate rosdebian` puis `fakeroot debian/rules binary`, et installation du `.deb` produit pour les paquets suivants. Artefact `debs-<distribution>`.

Job `docs` (si `docs`, même image) : `ros2_setup`, [`colcon_build`](colcon_build.md) (les pages Python importent les modules, messages générés compris), puis `scripts/build_docs.sh` : `rosdoc2 build` par paquet (Sphinx pour Python, Doxygen et Breathe pour C++). Artefact `api-docs`, un dossier HTML par paquet.

## Dépendances

- Actions de ce dépôt, à la révision `toolkit-ref` : `ros2_setup`, `ros2_debs`, `colcon_build`.
- Paquets Ubuntu installés dans le job : `python3-bloom`, `fakeroot`, `debhelper`, `dh-python`, `python3-rosdoc2`, `doxygen`, `graphviz`.
- Actions tierces : `actions/checkout@v4`, `actions/upload-artifact@v4`.

## Points d'attention

- Les paquets Debian ne sont pas publiés dans un dépôt apt : ils sont joints à la release ou téléchargés depuis l'artefact, puis installés avec `apt install ./ros-<distribution>-<paquet>_<version>.deb`. Un dépôt apt interne est une suite possible.
- La version du `.deb` est celle du `package.xml` suivie de `-0<codename>` (par exemple `0.1.0-0noble`).
- Un paquet dont une dépendance n'a pas de clé rosdep (ni du workspace, ni de la base publique) fait échouer `bloom-generate`.
- Les images Docker du workspace ne passent pas par ce workflow : elles restent construites par `generic_workflows/docker-ghcr.yml`, appelé directement par le dépôt (cas de MiniPock, `docker.yaml`).
