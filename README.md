---
titre: ROS Workflows
---

# ROS Workflows

Ce dépôt contient des workflows GitHub Actions réutilisables pour compiler, tester et étiqueter des paquets ROS 1 et ROS 2. Chaque workflow est décrit dans `docs/`. Vue d'ensemble de tous les workflows `catie-aq` : dépôt `catie-aq/sonu_workflow` (REF-001).

## Workflows réutilisables

| Workflow | Rôle | Doc |
| -------------------- | ---------------------------------------- | ---- |
| `ros2.yml` | Compilation d'un paquet ROS 2 (Jazzy et Rolling par défaut) ; tests, rosdep, image et paquets configurables. | [Compilation de paquets ROS 2](docs/ros2.md) |
| `ros.yml` | `pre-commit` puis compilation et tests d'un paquet ROS 1 sur Noetic. | [Compilation et tests de paquets ROS 1](docs/ros.md) |
| `ros-tag.yml` | Tag à partir de la version du `package.xml` et brouillon de release. | [Tag et brouillon de release ROS](docs/ros-tag.md) |

Exemple minimal :

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

Constaté le 28/09/2026 : aucun tag n'est publié sur ce dépôt ; les workflows s'appellent donc sur `@main`.

## Licence

Ce projet est sous licence Apache 2.0, une licence open source permissive qui vous permet d'utiliser, de modifier, de distribuer et de vendre
librement vos propres produits qui incluent ce logiciel. Le texte intégral de la licence peut être obtenu sur
le [site web d'Apache](https://www.apache.org/licenses/LICENSE-2.0).
