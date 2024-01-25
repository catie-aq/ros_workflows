# ROS Workflows

Ce dépôt contient une collection de workflows réutilisables, spécifiquement conçus pour la construction et les tests de paquets ROS, utilisables dans
le cadre d'Actions Github.

## Workflows Disponibles

### Construction & Test des Paquets ROS 2

Ce workflow est conçu pour automatiser la construction et les tests de paquets ROS 2. Il utilise un runner auto-hébergé et prend en charge plusieurs
distributions ROS.

1. *Configuration de l'environnement ROS* - Cette étape prépare l'environnement ROS à l'aide de l'outil `ros-tooling/setup-ros`.
2. *Construire et tester ROS 2* - Cette étape construit et teste le paquet ROS 2 à l'aide de l'outil `ros-tooling/action-ros-ci`.
3. *Vérifier les problèmes de style Python* - C'est une étape optionnelle pour vérifier les problèmes de style Python à l'aide de
   l'outil `ros-tooling/action-ros-lint`.

### Construction & Test des Paquets ROS 1

Ce workflow est conçu pour automatiser la construction et les tests de paquets ROS 1. Il utilise un runner auto-hébergé et prend en charge **uniquement** la distribution ROS Noetic.

1. *Configuration de l'environnement ROS* - Cette étape prépare l'environnement ROS à l'aide de l'outil `ros-tooling/setup-ros`.
2. *Construire et tester ROS 1* - Cette étape construit et teste le paquet ROS 1 à l'aide de l'outil `ros-tooling/action-ros-ci`.
3. *Vérifier les problèmes de style Python* - C'est une étape optionnelle pour vérifier les problèmes de style Python à l'aide de
   l'outil `ros-tooling/action-ros-lint`.

Le workflow possèdes les paramètres suivants :

`package-name` : Nom du paquet ROS à construire et tester, **Obligatoire**.

`pat` : Token d'accès personnel (PAT) à utiliser pour cloner les dépôts privés. Si il n'y a pas de *dépendances privées*, ce paramètre peut être mis à `${{ secrets.GITHUB_TOKEN }}`.

## Utilisation

Vous pouvez utiliser ce workflow dans votre dépôt en ajoutant le bloc de code suivant à votre fichier `.github/workflows/<name>.yml` :

```yaml
name: "ROS2 CI/CD"
on:
  push:

jobs:
  ros:
    uses: catie-aq/ros_workflows/.github/workflows/ros2.yml@main
```

Remarque : Vous pouvez également utiliser un tag spécifique pour le workflow, par exemple `ros2.yml@v1.0.0`.
Voir les [releases displonibles](https://github.com/catie-aq/ros_workflows/releases).

## Licence

Ce projet est sous licence Apache 2.0, une licence open source permissive qui vous permet d'utiliser, de modifier, de distribuer et de vendre
librement vos propres produits qui incluent ce logiciel. Le texte intégral de la licence peut être obtenu sur
le [site web d'Apache](https://www.apache.org/licenses/LICENSE-2.0).
