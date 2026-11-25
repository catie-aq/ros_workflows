---
titre: Compilation de paquets ROS 2
---

# Compilation de paquets ROS 2

Compile le paquet ROS 2 porté par le dépôt appelant, par défaut sur les distributions Jazzy et Rolling, avec `ros-tooling/action-ros-ci`. Sans entrée, les tests ne sont pas lancés et rosdep n'installe rien ; les entrées ci-dessous les activent et règlent distributions, image, paquets, délai et runner.

Pour un nouveau dépôt, préférer [`ros2-ci.yml`](ros2-ci.md) : lint, couverture, résumé des tests, test d'intégration, runner GPU. `ros2.yml` reste en place, avec les mêmes défauts, pour ses appelants actuels (dépôts C-Rob, MiniPock, `stelia_aoa-ros-driver`).

Fichier : `.github/workflows/ros2.yml` · Déclencheur : `workflow_call` · Runner : entrée `runner` (`sonu-github-arc` par défaut)

## Utilisation

```yaml
name: "ROS2 CI/CD"
on:
  push:

jobs:
  ros:
    uses: catie-aq/ros_workflows/.github/workflows/ros2.yml@main
    secrets:
      PAT: ${{ secrets.GITHUB_TOKEN }}
```

Pour un paquet qui importe des dépôts privés, passer un jeton personnel à la place de `GITHUB_TOKEN` (par exemple `${{ secrets.PERSONAL_ACCESS_TOKEN }}`).

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `run-tests` | boolean | Lance les tests des paquets (`colcon test`). | non | `false` |
| `rosdep-install` | boolean | Installe avec rosdep les dépendances déclarées dans `package.xml`. | non | `false` |
| `distributions` | string | Tableau JSON des distributions ROS 2, une entrée de matrice chacune. | non | `'["jazzy","rolling"]'` |
| `docker-image` | string | Image du conteneur, la même pour toutes les distributions. Vide : `osrf/ros:<distribution>-desktop`. | non | `""` |
| `packages` | string | Paquets à compiler et tester, séparés par des espaces. Vide : nom du dépôt appelant. | non | `""` |
| `pytest-args` | string | Tableau JSON de chaînes passé à `colcon test` (`--pytest-args`). Vide ou `[]` : rien n'est passé. | non | `'[]'` |
| `timeout-minutes` | number | Délai maximal du job, en minutes. Le défaut est celui de GitHub, comme avant l'ajout de l'entrée. | non | `360` |
| `container-env` | string | Objet JSON de variables d'environnement définies dans le conteneur. | non | `'{}'` |
| `runner` | string | Runner du job : `sonu-github-arc` ou `sonu-github-arc-gpu`. | non | `sonu-github-arc` |

`pytest-args` est un tableau JSON, pas une ligne de commande : `'["-m","not integration"]'` donne `--pytest-args -m "not integration"`. Il est transmis à `action-ros-ci` via `colcon-defaults` (`{"test": {"pytest-args": [...]}}`).

Exemple avec tests et rosdep :

```yaml
jobs:
  ros:
    uses: catie-aq/ros_workflows/.github/workflows/ros2.yml@main
    with:
      distributions: '["jazzy"]'
      rosdep-install: true
      run-tests: true
      packages: "pkg_a pkg_b"
      pytest-args: '["-m","not integration"]'
      container-env: '{"LIBGL_ALWAYS_SOFTWARE":"1"}'
      timeout-minutes: 45
    secrets:
      PAT: ${{ secrets.GITHUB_TOKEN }}
```

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |
| `PAT` | Jeton d'accès personnel GitHub utilisé pour importer les dépôts privés dans le conteneur. Passer `GITHUB_TOKEN` si le dépôt et ses dépendances sont publics. | oui |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Job `build_and_test_ros2_package` (runner = entrée `runner`, matrice `fail-fast: false`, `timeout-minutes` = entrée du même nom, conteneur selon la matrice). La matrice vient de `distributions` ; avec les défauts :

| Distribution | Image du conteneur |
| ------------ | ---------------------------------------- |
| `jazzy` | `osrf/ros:jazzy-desktop` |
| `rolling` | `osrf/ros:rolling-desktop` |

Pour chaque entrée de la matrice :

1. Compilation avec `ros-tooling/action-ros-ci@0.3.13` : `package-name` = `packages`, sinon nom du dépôt appelant ; `target-ros2-distro` = distribution de la matrice ; `import-token` = secret `PAT` ; `skip-tests` = `!run-tests` ; `skip-rosdep-install` = `!rosdep-install` ; `rosdep-check: false` ; `colcon-defaults` = `{"test":{"pytest-args":<pytest-args>}}` seulement si `pytest-args` n'est ni vide ni `[]`.

Avec `fail-fast: false`, l'échec d'une distribution n'annule pas l'autre.

## Dépendances

- Aucune (aucun workflow ni action `catie-aq` appelé). Actions tierces : `ros-tooling/action-ros-ci@0.3.13`.

## Points d'attention

- Par défaut (`run-tests: false`), les tests ne sont pas lancés : un appelant existant garde ce comportement. Il faut passer `run-tests: true` pour les activer.
- Par défaut (`rosdep-install: false`), les dépendances système déclarées dans `package.xml` ne sont pas installées par rosdep ; elles doivent être présentes dans l'image. Passer `rosdep-install: true` sinon.
- `docker-image` s'applique à toutes les distributions : avec une image fixe, ne demander qu'une distribution cohérente avec elle dans `distributions`.
- `pytest-args` doit être un tableau JSON valide ; une valeur invalide fait échouer l'action (`colcon-defaults value is not a valid JSON string`).
- Un dépôt dont le paquet porte un autre nom, ou qui contient plusieurs paquets, passe `packages`.
- Pas de `ros-tooling/setup-ros` ni d'étape de lint `ros-tooling/action-ros-lint`, contrairement à ce qu'indiquait l'ancien README (lint retiré au commit `886178f`, distribution Humble retirée au commit `3d6c081`).
- Pas de `pre-commit` dans ce workflow, contrairement à `ros.yml`.
- Le nom des jobs de la matrice a changé avec les entrées configurables : `build_and_test_ros2_package (jazzy)` au lieu de `build_and_test_ros2_package (osrf/ros:jazzy-desktop, jazzy)`. Aucun appelant n'en fait un contrôle obligatoire (vérifié le 25/11/2026).
- Sur `sonu-github-arc-gpu`, la carte n'est pas visible du conteneur du job : ce runner n'apporte rien à ce workflow. Le rendu matériel passe par le job `integration` de `ros2-ci.yml`.
- `stelia_aoa-ros-driver` appelle ce workflow sans le secret `PAT`, pourtant requis : son appel est refusé par GitHub, indépendamment de ce dépôt.
