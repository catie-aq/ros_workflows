---
titre: Auto-test de ros_workflows
---

# Auto-test de ros_workflows

CI de ce dépôt : tests des scripts, puis passage du workspace d'exemple `tests/fixtures/ros_ws` dans les workflows réutilisables de la révision testée. Un changement d'action, de script ou de workflow est donc vérifié avant d'arriver sur `main`.

Fichier : `.github/workflows/selftest.yml` · Déclencheur : `pull_request`, `push` sur `main`, `workflow_dispatch` · Runner : `sonu-github-arc`

## Utilisation

Aucune : workflow interne au dépôt, lancé par GitHub.

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |

Aucune.

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |

Aucun.

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Job `scripts` (conteneur `ghcr.io/astral-sh/uv:python3.12-bookworm-slim`) : `uv run --group dev pytest` sur Python 3.12 puis 3.10 (version de Humble). Les tests couvrent le résumé des tests et de la couverture, l'extraction du changelog, la table rosdep du workspace, l'export de variables, et la cohérence entre workflows, actions, scripts et docs.

Job `ros2-ci` : appel de `./.github/workflows/ros2-ci.yml` avec `toolkit-ref` = commit testé, sur `sample_pkg` (ament_python) et `sample_cpp_pkg` (ament_cmake, gtest) : `pre-commit` (dont actionlint, ruff, shellcheck), `lint` avec ruff, `build-test` sur Jazzy et Humble en `RelWithDebInfo` et `Debug`, job `integration` (talker et listener rclpy marqués `integration`, image `ros:jazzy-ros-base`).

Job `ros2-ci-asan` : même workflow, `sample_cpp_pkg` seul, `Debug`, `sanitizer: asan`.

Job `ros2-release` : appel de `./.github/workflows/ros2-release.yml` sur le workspace d'exemple (paquets Debian et documentation d'API).

## Dépendances

- Workflows et actions de ce dépôt, à la révision testée.

## Points d'attention

- `ros-tag.yml` n'est pas exercé : il crée un tag et une release. Ses scripts (`changelog_section.py`) sont couverts par les tests du job `scripts`.
- Le job `integration` de l'auto-test tourne sur le runner CPU ; le chemin GPU (sans conteneur) n'est pas exercé ici.
