---
titre: Compilation colcon (action)
---

# Compilation colcon (action)

Compile un workspace colcon : sélection des paquets, type de build, options de couverture et de sanitizer pour le C et le C++, ccache conservé entre les exécutions. À placer après `ros2_setup`.

Fichier : `colcon_build/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - uses: catie-aq/ros_workflows/colcon_build@main
    with:
      packages: "mon_paquet"
      build-type: "Debug"
      coverage: "true"
      cache-key: "jazzy-debug"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `workspace` | string | Workspace colcon. | non | `ws` |
| `distribution` | string | Distribution ROS. Vide : `ROS_DISTRO` de l'image. | non | `""` |
| `packages` | string | Paquets compilés avec leurs dépendances (`--packages-up-to`). Vide : tous. | non | `""` |
| `merge-install` | string | `--merge-install`. | non | `false` |
| `symlink-install` | string | `--symlink-install`. | non | `false` |
| `build-type` | string | `CMAKE_BUILD_TYPE`. | non | `RelWithDebInfo` |
| `coverage` | string | Compile le C et le C++ avec `--coverage` (rapports gcovr dans `colcon_test`). | non | `false` |
| `sanitizer` | string | `none` ou `asan`. | non | `none` |
| `ccache` | string | Compilation via ccache, dossier `.ccache` sauvé par `actions/cache`. | non | `true` |
| `cache-key` | string | Partie de la clé de cache qui distingue les builds. | non | `default` |
| `cmake-args` | string | Arguments CMake supplémentaires. | non | `""` |
| `colcon-args` | string | Arguments `colcon build` supplémentaires. | non | `""` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

1. Si `ccache` : `actions/cache@v4` sur `.ccache`, clé `ccache-<cache-key>-<sha>`, restauration depuis le dernier cache de même préfixe.
2. `scripts/colcon_build.sh` : `colcon build --event-handlers console_cohesion+ summary+ status- desktop_notification-`, options de sélection et d'installation, puis `--cmake-args -DCMAKE_BUILD_TYPE=<build-type>` et, selon les entrées :
   - `coverage` : `--coverage` dans `CMAKE_C_FLAGS`, `CMAKE_CXX_FLAGS` et les options d'édition de liens (équivalent du mixin colcon `coverage-gcc`) ;
   - `asan` : `-fsanitize=address -fno-omit-frame-pointer` (équivalent du mixin `asan`) ;
   - `ccache` : installation de `ccache` si absent, `CMAKE_<LANG>_COMPILER_LAUNCHER=ccache`, statistiques en fin de build.

## Dépendances

- Actions tierces : `actions/cache@v4`.

## Points d'attention

- Les options passent par `--cmake-args` plutôt que par les mixins colcon : le dépôt de mixins n'est pas enregistré hors des images `ros:*`, et les options restent visibles dans le log.
- ccache ne sert que si le chemin de compilation reste le même d'une exécution à l'autre (le répertoire courant entre dans le hachage avec `-g`), ce qui est le cas en CI. Mesuré sur le paquet d'exemple : 4 succès sur 4 au second build.
- `coverage` et `asan` changent les objets compilés : `cache-key` doit les distinguer.
