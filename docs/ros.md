---
titre: Compilation et tests de paquets ROS 1
---

# Compilation et tests de paquets ROS 1

Lance `pre-commit` puis compile et teste un paquet ROS 1 sur la distribution Noetic, la seule prise en charge. À utiliser comme CI d'un dépôt de paquet ROS 1.

Fichier : `.github/workflows/ros.yml` · Déclencheur : `workflow_call` · Runner : `group: default` (job de compilation) ; `sonu-github-arc` (job `pre-commit`, via `generic_workflows`)

## Utilisation

```yaml
name: "ROS CI/CD"
on:
  push:

jobs:
  ros:
    uses: catie-aq/ros_workflows/.github/workflows/ros.yml@main
    with:
      package-name: mon_paquet
    secrets:
      PAT: ${{ secrets.PERSONAL_ACCESS_TOKEN }}
```

Le secret `PAT` n'est utile que si le paquet importe des dépôts privés ; sinon il peut être omis ou valoir `${{ secrets.GITHUB_TOKEN }}`.

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `package-name` | string | Nom du paquet ROS à compiler et tester. | oui | |

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |
| `PAT` | Jeton d'accès personnel GitHub utilisé pour importer les dépôts privés dans le conteneur. | non |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Deux jobs indépendants (pas de `needs`), exécutés en parallèle :

Job `pre-commit` : appel de `catie-aq/generic_workflows/.github/workflows/pre-commit.yaml@main` avec ses valeurs par défaut (image `ghcr.io/catie-aq/pre-commit_docker:latest`, runner `sonu-github-arc`), qui lance `pre-commit run --all-files` sur le dépôt appelant.

Job `build_and_test_ros_package` (runner `group: default`, conteneur `osrf/ros:noetic-desktop-full`, matrice à une seule entrée `noetic`) :

1. Préparation de l'environnement avec `ros-tooling/setup-ros@v0.7` (`required-ros-distributions: noetic`).
2. Compilation et tests avec `ros-tooling/action-ros-ci@v0.2` : `package-name` = entrée `package-name`, `target-ros1-distro: noetic`, `import-token` = secret `PAT`.

## Dépendances

- `catie-aq/generic_workflows/.github/workflows/pre-commit.yaml@main`
- Actions tierces : `ros-tooling/setup-ros@v0.7`, `ros-tooling/action-ros-ci@v0.2`.

## Points d'attention

- ROS 1 Noetic est en fin de vie (mai 2025) ; l'image `osrf/ros:noetic-desktop-full` n'évolue plus.
- Versions d'actions anciennes : `ros-tooling/action-ros-ci@v0.2` (alors que `ros2.yml` utilise `0.3.13`) et `ros-tooling/setup-ros@v0.7`.
- Le job `pre-commit` s'exécute sans condition : le dépôt appelant doit contenir un `.pre-commit-config.yaml`.
- `PAT` est facultatif : s'il n'est pas passé, `import-token` est vide et l'import de dépôts privés échoue.
- Pas d'étape de lint `ros-tooling/action-ros-lint`, contrairement à ce qu'indiquait l'ancien README.
