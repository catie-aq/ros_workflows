---
titre: Compilation de paquets ROS 2
---

# Compilation de paquets ROS 2

Compile le paquet ROS 2 porté par le dépôt appelant sur les distributions Jazzy et Rolling. À utiliser comme CI d'un dépôt de paquet ROS 2 ; les tests ne sont pas lancés (voir « Points d'attention »).

Fichier : `.github/workflows/ros2.yml` · Déclencheur : `workflow_call` · Runner : `sonu-github-arc`

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

Aucune. Le nom du paquet compilé est le nom du dépôt appelant (`github.event.repository.name`).

## Secrets

| Nom | Description | Requis |
| ------------ | ---------------------------------------- | ----- |
| `PAT` | Jeton d'accès personnel GitHub utilisé pour importer les dépôts privés dans le conteneur. Passer `GITHUB_TOKEN` si le dépôt et ses dépendances sont publics. | oui |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Job `build_and_test_ros2_package` (runner `sonu-github-arc`, matrice `fail-fast: false`, conteneur selon la matrice) :

| Distribution | Image du conteneur |
| ------------ | ---------------------------------------- |
| `jazzy` | `osrf/ros:jazzy-desktop` |
| `rolling` | `osrf/ros:rolling-desktop` |

Pour chaque entrée de la matrice :

1. Compilation avec `ros-tooling/action-ros-ci@0.3.13` : `package-name` = nom du dépôt appelant, `target-ros2-distro` = distribution de la matrice, `import-token` = secret `PAT`, `skip-tests: true`, `skip-rosdep-install: true`, `rosdep-check: false`.

Avec `fail-fast: false`, l'échec d'une distribution n'annule pas l'autre.

## Dépendances

- Aucune (aucun workflow ni action `catie-aq` appelé). Actions tierces : `ros-tooling/action-ros-ci@0.3.13`.

## Points d'attention

- Le nom du workflow (« Build & Test ») ne correspond pas au code : `skip-tests: true`, les tests du paquet ne sont jamais lancés.
- `skip-rosdep-install: true` : les dépendances système déclarées dans `package.xml` ne sont pas installées par rosdep ; elles doivent être présentes dans l'image `osrf/ros:*-desktop`.
- Le nom du paquet est imposé (nom du dépôt) : un dépôt dont le paquet porte un autre nom, ou qui contient plusieurs paquets, n'est pas couvert.
- Pas de `ros-tooling/setup-ros` ni d'étape de lint `ros-tooling/action-ros-lint`, contrairement à ce qu'indiquait l'ancien README (lint retiré au commit `886178f`, distribution Humble retirée au commit `3d6c081`).
- Pas de `pre-commit` dans ce workflow, contrairement à `ros.yml`.
