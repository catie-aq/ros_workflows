---
titre: Logs ROS 2 (action)
---

# Logs ROS 2 (action)

Rassemble les logs colcon (`<workspace>/log`) et les logs ROS (`~/.ros/log`, ou `ROS_LOG_DIR`, `ROS_HOME`) dans un seul artefact. À appeler avec `if: failure()` en fin de job.

Fichier : `ros2_logs/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - if: ${{ failure() }}
    uses: catie-aq/ros_workflows/ros2_logs@main
    with:
      artifact-name: ros2-logs-jazzy
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `workspace` | string | Workspace colcon. | non | `ws` |
| `artifact-name` | string | Nom de l'artefact. | non | `ros2-logs` |
| `retention-days` | string | Durée de conservation de l'artefact, en jours. | non | `7` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

1. `scripts/collect_logs.sh` : copie de `<workspace>/log` dans `ros2-logs/colcon` et des logs ROS dans `ros2-logs/ros` (liens symboliques suivis).
2. `actions/upload-artifact@v4` de `ros2-logs`, sans erreur si le dossier est vide.

## Dépendances

- Actions tierces : `actions/upload-artifact@v4`.

## Points d'attention

- Dans un conteneur de job, GitHub fixe `HOME=/github/home` : les logs ROS sont dans `/github/home/.ros/log`, que le script trouve par `HOME`.
