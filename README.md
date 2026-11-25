---
titre: ROS Workflows
---

# ROS Workflows

Ce dépôt contient des workflows GitHub Actions réutilisables et des actions composites pour compiler, tester, analyser et livrer des paquets ROS 2 : CI complète (`ros2-ci.yml`), paquets Debian et documentation d'API (`ros2-release.yml`), tag et release (`ros-tag.yml`). Chaque workflow et chaque action est décrit dans `docs/`. Vue d'ensemble de tous les workflows `catie-aq` : dépôt `catie-aq/sonu_workflow` (REF-001).

## Workflows réutilisables

| Workflow | Rôle | Doc |
| -------------------- | ---------------------------------------- | ---- |
| `ros2-ci.yml` | CI ROS 2 : pre-commit, lint, build et tests par distribution et type de build, couverture, résumé des tests, intégration sur runner CPU ou GPU. | [CI ROS 2](docs/ros2-ci.md) |
| `ros2-release.yml` | Paquets Debian (bloom) et documentation d'API (rosdoc2) en artefacts. | [Paquets Debian et documentation d'API ROS 2](docs/ros2-release.md) |
| `ros-tag.yml` | Tag à partir de la version du `package.xml` et brouillon de release ; notes tirées du changelog et livrables joints en option. | [Tag et brouillon de release ROS](docs/ros-tag.md) |
| `ros2.yml` | Ancienne CI ROS 2 par `action-ros-ci`, gardée pour ses appelants ; préférer `ros2-ci.yml`. | [Compilation de paquets ROS 2](docs/ros2.md) |
| `ros.yml` | Déprécié : `pre-commit` puis compilation et tests d'un paquet ROS 1 sur Noetic. | [Compilation et tests de paquets ROS 1](docs/ros.md) |
| `selftest.yml` | CI de ce dépôt (interne). | [Auto-test de ros_workflows](docs/selftest.md) |

## Actions composites

| Action | Rôle | Doc |
| -------------------- | ---------------------------------------- | ---- |
| `ros2_setup` | ROS 2 si absent, dépôts amont (`vcs`), `rosdep install` et `rosdep check`. | [ros2_setup](docs/ros2_setup.md) |
| `colcon_build` | `colcon build` : sélection, type de build, couverture, ASan, ccache. | [colcon_build](docs/colcon_build.md) |
| `colcon_test` | `colcon test`, couverture Python et C++, résumé Markdown, annotations, rapports en artefact. | [colcon_test](docs/colcon_test.md) |
| `ros2_lint` | `ament_xmllint`, `ament_lint_cmake`, `ruff` en option. | [ros2_lint](docs/ros2_lint.md) |
| `ros2_logs` | Logs colcon et ROS en artefact après un échec. | [ros2_logs](docs/ros2_logs.md) |
| `ros2_debs` | Paquets Debian par `bloom-generate rosdebian`, dans l'ordre des dépendances. | [ros2_debs](docs/ros2_debs.md) |

La logique des actions vit dans `scripts/` (Bash pour l'enchaînement des commandes, Python sans dépendance pour le résumé, le changelog, la table rosdep et l'export de variables), testée par `tests/` et par l'auto-test sur le workspace d'exemple `tests/fixtures/ros_ws`.

Exemple minimal :

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

Constaté le 28/09/2026 : aucun tag n'est publié sur ce dépôt ; les workflows s'appellent donc sur `@main`.

## Développement

```bash
uv run --group dev pytest
```

```bash
uvx pre-commit run --all-files
```

Les scripts se testent aussi dans une image ROS, sans GitHub : les variables d'environnement documentées en tête de chaque script remplacent les entrées des actions.

```bash
docker run --rm -v "$PWD":/toolkit:ro ros:jazzy-ros-base bash -c 'mkdir -p /w/ws/src && cp -r /toolkit/tests/fixtures/ros_ws/src/. /w/ws/src/ && cd /w && /toolkit/scripts/ros2_setup.sh && /toolkit/scripts/colcon_build.sh && COVERAGE=true /toolkit/scripts/colcon_test.sh'
```

## Licence

Ce projet est sous licence Apache 2.0, une licence open source permissive qui vous permet d'utiliser, de modifier, de distribuer et de vendre
librement vos propres produits qui incluent ce logiciel. Le texte intégral de la licence peut être obtenu sur
le [site web d'Apache](https://www.apache.org/licenses/LICENSE-2.0).
