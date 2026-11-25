---
titre: Lint de paquets ROS 2 (action)
---

# Lint de paquets ROS 2 (action)

Vérifie les paquets ROS 2 d'une arborescence sans les compiler : `package.xml` contre son schéma (`ament_xmllint`), style des `CMakeLists.txt` (`ament_lint_cmake`) et, en option, Python avec `ruff`. Écrit un tableau de résultats dans le résumé du job.

Fichier : `ros2_lint/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - uses: catie-aq/ros_workflows/ros2_lint@main
    with:
      path: ws/src
      ruff: "true"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `path` | string | Arborescence vérifiée. | non | `ws/src` |
| `distribution` | string | Distribution ROS. Vide : `ROS_DISTRO` de l'image. | non | `""` |
| `xmllint` | string | `ament_xmllint` sur chaque `package.xml`. | non | `true` |
| `cmake-lint` | string | `ament_lint_cmake` sur chaque `CMakeLists.txt` de paquet. | non | `true` |
| `ruff` | string | `ruff check` avec la configuration de l'arborescence. | non | `false` |
| `ruff-version` | string | Version de ruff installée si l'image n'en a pas. | non | `0.17.6` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Une étape `bash` qui lance `scripts/ros2_lint.sh` :

1. Liste des dossiers de paquets (`package.xml`), hors arborescences marquées `COLCON_IGNORE` ou `AMENT_IGNORE`.
2. `ament_xmllint` sur tous les `package.xml` : validation contre le schéma déclaré par `<?xml-model?>` (format 2 ou 3), téléchargé depuis `download.ros.org`.
3. `ament_lint_cmake` sur les `CMakeLists.txt` des paquets.
4. Si `ruff` : s'il manque, binaire ruff téléchargé depuis la release GitHub `astral-sh/ruff` de la version `ruff-version` et vérifié par `sha256sum` (somme épinglée pour la version par défaut, sinon celle publiée à côté de l'archive), puis `ruff check` (annotations GitHub).
5. Tableau des résultats dans `$GITHUB_STEP_SUMMARY` ; l'étape échoue si un outil échoue, après avoir lancé tous les autres.

## Dépendances

- Aucune action. Outils de l'image ROS (`ros-<distribution>-ament-xmllint`, `ros-<distribution>-ament-lint-cmake`, présents dans `ros-base`).

## Points d'attention

- Les autres linters ament (`ament_flake8`, `ament_pep257`, `ament_copyright`, `ament_cpplint`, `ament_uncrustify`) ne sont pas lancés : le Python est couvert par ruff (standard CATIE, via pre-commit ou l'entrée `ruff`), et le style C++ par la configuration propre à chaque dépôt. Un paquet qui les déclare dans `ament_lint_auto` les lance de toute façon dans `colcon test`.
- `ament_xmllint` a besoin du réseau pour télécharger le schéma.
