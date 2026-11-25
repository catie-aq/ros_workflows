---
titre: Préparation d'un workspace ROS 2 (action)
---

# Préparation d'un workspace ROS 2 (action)

Prépare un workspace colcon : installe ROS 2 s'il manque (job sans conteneur), importe les dépôts amont d'un fichier `.repos`, installe les dépendances système avec rosdep et vérifie qu'il n'en manque aucune. À placer après l'extraction des sources dans `<workspace>/src`.

Fichier : `ros2_setup/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      path: ws/src/mon_depot
  - uses: catie-aq/ros_workflows/ros2_setup@main
    with:
      repos-file: ws/src/mon_depot/deps.repos
      skip-keys: "fastcdr rti-connext-dds-6.0.1"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `workspace` | string | Workspace colcon, sources dans `<workspace>/src`. | non | `ws` |
| `distribution` | string | Distribution ROS. Vide : `ROS_DISTRO` de l'image. | non | `""` |
| `install-ros` | string | Installe ROS 2 (`ros-<distribution>-ros-base`, outils de build) si `/opt/ros/<distribution>` manque. | non | `true` |
| `repos-file` | string | Fichier `.repos` importé avec `vcs import --recursive --shallow` dans `<workspace>/src`. | non | `""` |
| `packages` | string | Limite rosdep à ces paquets et à leurs dépendances du workspace. Vide : tous. | non | `""` |
| `skip-keys` | string | Clés rosdep ignorées, séparées par des espaces. | non | `""` |
| `rosdep-check` | string | Lance `rosdep check` après l'installation. | non | `true` |
| `apt-packages` | string | Paquets apt supplémentaires. | non | `""` |
| `token` | string | Jeton pour les dépôts privés `https://github.com/`. | non | `""` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |

Aucune.

## Fonctionnement

Une étape `bash` qui lance `scripts/ros2_setup.sh` :

1. Si `/opt/ros/<distribution>/setup.bash` manque et `install-ros` vaut `true` : `scripts/install_ros.sh`, sur le modèle de `ros-tooling/setup-ros` (paquet `ros2-apt-source` épinglé, `ros-<distribution>-ros-base`, `ros-dev-tools`). Commandes en `sudo` hors conteneur root.
2. `git config --global --add safe.directory '*'` ; avec `token`, réécriture de `https://github.com/` en `https://x-access-token:<token>@github.com/`.
3. Si `repos-file` : `vcs import`.
4. Si `apt-packages` : installation des paquets absents.
5. `rosdep init` si besoin, `rosdep update --rosdistro <distribution>`, `rosdep install --from-paths <chemins> --ignore-src -y --rosdistro <distribution> --skip-keys <skip-keys>`. Avec `packages`, les chemins sont ceux de `colcon list --packages-up-to <packages>`, sinon `<workspace>/src`.
6. Si `rosdep-check` : `rosdep check` sur les mêmes chemins.

## Dépendances

- Aucune action. Outils de l'image ROS : `rosdep`, `vcs`, `colcon`.

## Points d'attention

- `rosdep install` échoue sur une clé inconnue (pas d'option `-r`) : une dépendance sans clé rosdep se déclare dans `skip-keys`.
- Pas de cache apt : les runners passent déjà par le cache apt du cluster (`apt-cacher-ng`, `helm_github-arc`) et l'archive d'un cache GitHub coûterait autant que le téléchargement. Pour aller plus vite, utiliser une image qui contient déjà les dépendances.
- Le jeton est écrit dans la configuration git globale du conteneur, qui disparaît avec le job.
