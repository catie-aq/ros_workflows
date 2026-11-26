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
| `packages` | string | Limite rosdep à ces paquets et à leurs dépendances du workspace. Vide : tous les paquets que colcon trouve. | non | `""` |
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

1. Si `/opt/ros/<distribution>/setup.bash` manque et `install-ros` vaut `true` : `scripts/install_ros.sh`, sur le modèle de `ros-tooling/setup-ros` (paquet `ros2-apt-source` épinglé et vérifié par `sha256sum`, `ros-<distribution>-ros-base`, `ros-dev-tools`). Commandes en `sudo` hors conteneur root.
2. `git config --global --add safe.directory '*'` ; avec `token`, réécriture de `https://github.com/` en `https://x-access-token:<token>@github.com/`.
3. Si `repos-file` : `vcs import`.
4. Si `apt-packages` : installation des paquets absents.
5. Chemins des paquets : `colcon list --base-paths <workspace>/src --paths-only`, avec `--packages-up-to <packages>` si `packages` est renseigné. rosdep ne reçoit que ces dossiers : les arborescences marquées `COLCON_IGNORE` ou `AMENT_IGNORE` (fixtures de test, sources vendorisées) restent hors de sa portée, alors que `rosdep install --from-paths <workspace>/src` lirait tous les `package.xml` et échouerait sur le premier invalide. Aucun paquet trouvé : échec.
6. `rosdep init` si besoin, `rosdep update --rosdistro <distribution>` (5 min au plus, 3 essais), `apt-get update` (une fois par job, avec `Acquire::Retries 3` et des délais de 60 s écrits dans `/etc/apt/apt.conf.d/80-ros2-ci`), `rosdep install --from-paths <chemins> --ignore-src -y --rosdistro <distribution> --skip-keys <skip-keys>` avec `DEBIAN_FRONTEND=noninteractive`.
7. Si `rosdep-check` : `rosdep check` sur les mêmes chemins.

## Dépendances

- Aucune action. Outils de l'image ROS : `rosdep`, `vcs`, `colcon`.

## Points d'attention

- `rosdep install` échoue sur une clé inconnue (pas d'option `-r`) : une dépendance sans clé rosdep se déclare dans `skip-keys`.
- Pas de cache apt : les runners passent déjà par le cache apt du cluster (`apt-cacher-ng`, `helm_github-arc`) et l'archive d'un cache GitHub coûterait autant que le téléchargement. Pour aller plus vite, utiliser une image qui contient déjà les dépendances.
- Le jeton est écrit dans la configuration git globale du conteneur, qui disparaît avec le job.
- `apt-get update` n'est lancé qu'une fois par job, grâce au marqueur `/tmp/.ros2-ci-apt-updated` : cela suppose un runner ou un conteneur éphémère (un job, un `/tmp`), ce que sont les runners `sonu-github-arc`. Sur une machine réutilisée, supprimer ce fichier avant le job.
- `install_ros.sh` vérifie le `sha256` du paquet `ros2-apt-source` (version 1.3.0 épinglée pour `noble` et `jammy`) ; une autre version ou distribution demande `ROS_APT_SOURCE_VERSION` et `ROS_APT_SOURCE_SHA256`.
