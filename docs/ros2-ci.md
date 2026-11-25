---
titre: CI ROS 2
---

# CI ROS 2

CI complète d'un dépôt ROS 2 (un paquet ou un workspace) : pre-commit, lint des paquets, compilation et tests par distribution et type de build, couverture Python et C++, résumé Markdown du job, test d'intégration optionnel sur un runner CPU ou GPU. À utiliser pour tout nouveau dépôt ROS 2 ; `ros2.yml` reste pour les appelants existants.

Fichier : `.github/workflows/ros2-ci.yml` · Déclencheur : `workflow_call` · Runner : entrée `runner` (`sonu-github-arc` par défaut, `sonu-github-arc-gpu` possible) ; `sonu-github-arc` pour le job `pre-commit` (via `generic_workflows`)

## Utilisation

```yaml
name: "ROS 2 CI"
on:
  pull_request:
  push:
    branches: [main]

jobs:
  ros2:
    uses: catie-aq/ros_workflows/.github/workflows/ros2-ci.yml@main
```

Sans entrée, le workflow compile et teste tous les paquets du dépôt sur Jazzy, dans `ros:jazzy-ros-base`, avec rosdep, couverture et ccache.

Exemple d'un workspace avec sous-module, tests d'intégration Gazebo et runner GPU (cas de MiniPock) :

```yaml
jobs:
  ros2:
    uses: catie-aq/ros_workflows/.github/workflows/ros2-ci.yml@main
    with:
      submodules: "recursive"
      merge-install: true
      packages: "minipock minipock_bringup minipock_description minipock_gz minipock_navigation2 minipock_cartographer"
      pytest-args: '["-m", "not integration"]'
      integration: true
      integration-runner: "sonu-github-arc-gpu"
      integration-packages: "minipock_bringup"
      container-env: '{"ROS_AUTOMATIC_DISCOVERY_RANGE": "LOCALHOST"}'
    secrets:
      token: ${{ secrets.PAT }}
```

Le dépôt appelant doit contenir un `.pre-commit-config.yaml` (job `pre-commit`), sinon passer `pre-commit: false`.

Migration depuis `ros2.yml` : beaucoup de dépôts appellent déjà `generic_workflows/pre-commit.yaml` dans leur propre workflow (c'est le cas de MiniPock et de C-Rob). Avec `ros2-ci.yml`, retirer ce job du dépôt, ou passer `pre-commit: false`, sinon pre-commit tourne deux fois.

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `runner` | string | Runner de tous les jobs : `sonu-github-arc` ou `sonu-github-arc-gpu`. | non | `sonu-github-arc` |
| `distributions` | string | Tableau JSON des distributions ROS 2, un job `build-test` chacune. | non | `'["jazzy"]'` |
| `image` | string | Image des jobs `lint` et `build-test`. Vide : `ros:<distribution>-ros-base`. | non | `""` |
| `build-types` | string | Tableau JSON de `CMAKE_BUILD_TYPE`, un job `build-test` chacun. | non | `'["RelWithDebInfo"]'` |
| `packages` | string | Paquets à compiler (avec leurs dépendances) et tester, séparés par des espaces. Vide : tous. | non | `""` |
| `pytest-args` | string | Tableau JSON d'arguments pytest du job `build-test`. | non | `'[]'` |
| `container-env` | string | Objet JSON de variables d'environnement des jobs `build-test` et `integration`. | non | `'{}'` |
| `timeout-minutes` | number | Délai de chaque job `build-test`, en minutes. | non | `60` |
| `submodules` | string | Sous-modules : `false`, `true` ou `recursive`. | non | `false` |
| `repos-file` | string | Chemin, dans le dépôt, d'un fichier `.repos` importé avec `vcs`. Vide : aucun. | non | `""` |
| `skip-keys` | string | Clés rosdep ignorées, séparées par des espaces. | non | `""` |
| `rosdep-check` | boolean | Échec si `rosdep check` trouve une dépendance système manquante après l'installation. | non | `true` |
| `merge-install` | boolean | Compilation avec `--merge-install`. | non | `false` |
| `cmake-args` | string | Arguments CMake supplémentaires. | non | `""` |
| `coverage` | boolean | Couverture : pytest-cov pour Python, gcovr pour C et C++. | non | `true` |
| `sanitizer` | string | `none` ou `asan` (AddressSanitizer sur le code C et C++). | non | `none` |
| `ccache` | boolean | Compilation via ccache, cache conservé entre les exécutions (`actions/cache`). | non | `true` |
| `retries` | number | Relance des tests en échec jusqu'à N fois. `0` : aucune relance. | non | `0` |
| `pre-commit` | boolean | Lance le job `pre-commit` de `generic_workflows`. | non | `true` |
| `lint` | boolean | Lance le job `lint` (`ament_xmllint`, `ament_lint_cmake`). | non | `true` |
| `lint-ruff` | boolean | Ajoute `ruff check` au job `lint`, avec la configuration du dépôt. | non | `false` |
| `integration` | boolean | Lance le job `integration` après `build-test`. | non | `false` |
| `integration-runner` | string | Runner du job `integration`. Vide : entrée `runner`. | non | `""` |
| `integration-image` | string | Image du job `integration` sur runner CPU. Vide : `osrf/ros:<première distribution>-desktop-full`. | non | `""` |
| `integration-packages` | string | Paquets du job `integration`. Vide : entrée `packages`. | non | `""` |
| `integration-pytest-args` | string | Tableau JSON d'arguments pytest du job `integration`. | non | `'["-m", "integration"]'` |
| `integration-rendering` | string | Rendu OpenGL : `auto`, `hardware` ou `software`. | non | `auto` |
| `integration-timeout-minutes` | number | Délai du job `integration`, en minutes. | non | `45` |
| `concurrency-group` | string | Suffixe du groupe de concurrence, pour appeler le workflow plusieurs fois depuis un même workflow. | non | `""` |
| `toolkit-ref` | string | Révision de `catie-aq/ros_workflows` dont les actions et scripts sont utilisés. | non | `main` |

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |
| `token` | Jeton pour les sous-modules et dépôts amont privés. Vide : `GITHUB_TOKEN`. | non |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune. Les résultats sont dans le résumé du job et les artefacts `test-reports-*`.

## Fonctionnement

Concurrence : groupe `ros2-ci-<workflow appelant>-<numéro de PR ou ref>-<concurrency-group>` ; un nouveau push sur une PR annule l'exécution en cours, un push sur une branche n'annule rien.

Chaque job (hors `pre-commit`) extrait le dépôt appelant dans `ws/src/<dépôt>` et `catie-aq/ros_workflows` à la révision `toolkit-ref` dans `.ros_workflows`, hors du workspace.

Job `pre-commit` (si `pre-commit`) : appel de `catie-aq/generic_workflows/.github/workflows/pre-commit.yaml@main`.

Job `lint` (si `lint` ; conteneur `image`, sinon `ros:<première distribution>-ros-base`) : action [`ros2_lint`](ros2_lint.md) sur `ws/src`.

Job `build-test` (matrice `distributions` × `build-types`, `fail-fast: false`, conteneur `image` sinon `ros:<distribution>-ros-base`, variables `container-env`) :

1. [`ros2_setup`](ros2_setup.md) : import de `repos-file`, `rosdep install` limité aux `packages` et à leurs dépendances, `rosdep check`.
2. [`colcon_build`](colcon_build.md) : `--packages-up-to <packages>`, type de build de la matrice, `--coverage` si `coverage`, sanitizer, ccache avec une clé par dépôt, distribution, type de build, sanitizer et couverture.
3. [`colcon_test`](colcon_test.md) : `--packages-select <packages>`, `pytest-args`, couverture, résumé Markdown, artefact `test-reports-<distribution>-<type>`.
4. En cas d'échec : [`ros2_logs`](ros2_logs.md), artefact `ros2-logs-<distribution>-<type>`.

Job `integration` (si `integration`, après `build-test`, première distribution) :

- runner dont le nom contient `gpu` : pas de conteneur. Sur `sonu-github-arc-gpu`, la carte n'est visible que du conteneur du runner, pas des conteneurs de job (`catie-aq/helm_github-arc`, `value_gpu.yaml`). `ros2_setup` installe alors ROS 2 (`ros-<distribution>-ros-base`) sur le runner, puis rosdep le reste ;
- autre runner : conteneur `integration-image`, sinon `osrf/ros:<distribution>-desktop-full`.

Étapes : variables `container-env` exportées (`scripts/export_env.py`), choix du rendu (`scripts/detect_rendering.sh` : matériel si `nvidia-smi` voit une carte ou si un nœud `/dev/dri/renderD*` est accessible, logiciel sinon avec `LIBGL_ALWAYS_SOFTWARE=1` ; variable `ROS2_CI_RENDERING` exportée), puis `ros2_setup`, `colcon_build`, `colcon_test` avec `integration-pytest-args`, artefacts `test-reports-integration` et, en cas d'échec, `ros2-logs-integration`.

## Dépendances

- `catie-aq/generic_workflows/.github/workflows/pre-commit.yaml@main`
- Actions de ce dépôt, à la révision `toolkit-ref` : `ros2_setup`, `colcon_build`, `colcon_test`, `ros2_lint`, `ros2_logs`.
- Actions tierces : `actions/checkout@v4`, `actions/cache@v4`, `actions/upload-artifact@v4`.

## Points d'attention

- `toolkit-ref` doit désigner la même révision que celle du workflow appelé : un appel à `ros2-ci.yml@v2` garde des actions de `main` tant que `toolkit-ref` n'est pas aussi `v2`. GitHub ne donne pas à un workflow réutilisable sa propre révision.
- Le job `pre-commit` tourne toujours sur `sonu-github-arc` : `generic_workflows/pre-commit.yaml` n'a pas d'entrée de runner.
- Les tests d'intégration sont à exclure du job `build-test` par `pytest-args` (par exemple `'["-m", "not integration"]'`) : le workflow n'ajoute aucun filtre.
- Sur le runner GPU, le job installe ROS 2 et toutes les dépendances à chaque exécution, faute de conteneur : compter plusieurs minutes de plus que sur le runner CPU. Le runner GPU n'accepte qu'un job à la fois (`maxRunners: 1`) et peut être suspendu pendant des mesures (README de `helm_github-arc`).
- Le rendu matériel n'a pas été validé sur `sonu-github-arc-gpu` lui-même ; il l'a été dans l'image du runner (`ghcr.io/actions/actions-runner`) avec une carte NVIDIA locale : `eglinfo` y montre le moteur de rendu NVIDIA et `ROS2_CI_RENDERING=hardware`.
- `permissions: contents: read` : l'appelant doit accorder au moins cela à son `GITHUB_TOKEN` (c'est le défaut des dépôts `catie-aq`).
- Deux appels de ce workflow dans un même workflow appelant doivent avoir des `concurrency-group` différents, sinon le second annule le premier sur une PR, et les noms d'artefacts entrent en collision.
- `sanitizer: asan` instrumente le C et le C++ : un test Python qui charge une bibliothèque instrumentée du workspace (messages générés, extensions) échoue au chargement. Réserver ce mode aux paquets C++ (`packages`).
- Le résumé ne compte pas les fichiers XML de CTest lui-même : son total peut différer d'une unité par paquet CMake de celui de `colcon test-result`.
