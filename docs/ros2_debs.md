---
titre: Paquets Debian ROS 2 (action)
---

# Paquets Debian ROS 2 (action)

Construit les paquets Debian des paquets du workspace avec bloom, comme le buildfarm ROS : `bloom-generate rosdebian` puis `debian/rules binary`, dans l'ordre des dépendances, et les publie en artefact. À placer après `ros2_setup`, dans un conteneur root.

Fichier : `ros2_debs/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - uses: catie-aq/ros_workflows/ros2_debs@main
    with:
      packages: "mon_paquet"
      artifact-name: debs-jazzy
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `workspace` | string | Workspace colcon, dépendances installées. | non | `ws` |
| `distribution` | string | Distribution ROS. Vide : `ROS_DISTRO` de l'image. | non | `""` |
| `packages` | string | Paquets empaquetés avec leurs dépendances du workspace. Vide : tous. | non | `""` |
| `output-dir` | string | Dossier des `.deb`. | non | `debs` |
| `artifact-name` | string | Nom de l'artefact des `.deb`. Vide : pas d'envoi. | non | `debs` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

1. `scripts/build_debs.sh` :
   - installe `python3-bloom`, `fakeroot`, `debhelper`, `dh-python` ;
   - liste les paquets dans l'ordre topologique (`colcon list --topological-order`) ;
   - écrit avec `scripts/workspace_rosdep.py` une table rosdep qui associe chaque paquet du workspace à son nom Debian (`ros-<distribution>-<nom avec tirets>`), déclarée dans `/etc/ros/rosdep/sources.list.d/00-workspace.list`, puis `rosdep update` : un paquet qui dépend d'un autre paquet du workspace se résout ;
   - pour chaque paquet, sur une copie des sources : `bloom-generate rosdebian --os-name ubuntu --os-version <codename> --ros-distro <distribution>`, `fakeroot debian/rules binary`, installation du `.deb` produit, déplacement dans `output-dir` ;
   - liste des `.deb` dans `$GITHUB_STEP_SUMMARY`.
2. Si `artifact-name` : `actions/upload-artifact@v4` des `.deb`.

## Dépendances

- Actions tierces : `actions/upload-artifact@v4`.

## Points d'attention

- L'action modifie la configuration rosdep et installe les paquets dans `/opt/ros/<distribution>` : à lancer dans un job dédié.
- Les `.deb` ne sont pas signés et ne sont publiés dans aucun dépôt apt.
