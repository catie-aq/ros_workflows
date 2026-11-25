---
titre: Tests colcon et résumé (action)
---

# Tests colcon et résumé (action)

Lance les tests d'un workspace compilé, écrit un résumé Markdown dans le job (tests réussis, en échec et ignorés par paquet, liste des tests en échec, couverture par paquet), annote les tests en échec et publie les rapports JUnit et de couverture en artefact. À placer après `colcon_build`.

Fichier : `colcon_test/action.yml` · Type : action composite

## Utilisation

```yaml
steps:
  - uses: catie-aq/ros_workflows/colcon_test@main
    with:
      pytest-args: '["-m", "not integration"]'
      coverage: "true"
      artifact-name: "test-reports-jazzy"
```

## Entrées

| Nom | Type | Description | Requis | Défaut |
| ------------ | ------- | ---------------------------------------- | ----- | ------------ |
| `workspace` | string | Workspace colcon. | non | `ws` |
| `distribution` | string | Distribution ROS. Vide : `ROS_DISTRO` de l'image. | non | `""` |
| `packages` | string | Paquets testés (`--packages-select`). Vide : tous. | non | `""` |
| `merge-install` | string | Le workspace a été compilé avec `--merge-install`. | non | `false` |
| `pytest-args` | string | Tableau JSON d'arguments pytest. | non | `'[]'` |
| `retries` | string | Relance des tests en échec jusqu'à N fois. | non | `0` |
| `coverage` | string | Rapports de couverture : pytest-cov (Python), gcovr (C, C++). | non | `false` |
| `report-title` | string | Titre du résumé. Vide : `Tests ROS 2 (<distribution>)`. | non | `""` |
| `artifact-name` | string | Nom de l'artefact des rapports. Vide : pas d'envoi. | non | `test-reports` |
| `colcon-args` | string | Arguments `colcon test` supplémentaires. | non | `""` |

## Sorties

| Nom | Description |
| ------------ | ---------------------------------------- |
| `tests` | Nombre de cas de test. |
| `failures` | Nombre de cas en échec ou en erreur. |
| `skipped` | Nombre de cas ignorés. |

## Fonctionnement

1. `scripts/colcon_test.sh` :
   - installe `python3-pytest-cov` et `gcovr` si `coverage`, `python3-pytest-rerunfailures` si `retries` ;
   - `colcon test` avec la sélection, `--retest-until-pass <retries>` (CTest), `--pytest-with-coverage` (colcon écrit `build/<paquet>/coverage.xml`) et `--pytest-args` en dernier, chaque argument commençant par `-` préfixé d'une espace comme colcon le demande ;
   - si `coverage` : `gcovr` pour chaque paquet CMake qui a produit des `.gcda`, limité aux sources du paquet hors `test/`, vers `build/<paquet>/coverage-gcovr.xml` (format Cobertura) ;
   - `scripts/ros2_ci_report.py` : lit `build/<paquet>/pytest.xml`, `build/<paquet>/test_results/**/*.xml`, `coverage.xml` et `coverage-gcovr.xml`, écrit le résumé dans `$GITHUB_STEP_SUMMARY`, une annotation `::error` par test en échec, les sorties `tests`, `failures`, `skipped`, et copie les rapports dans `<workspace>/test-reports` avec `summary.md` ;
   - `colcon test-result --verbose` ; le code de sortie de l'étape est celui de `colcon test` s'il a échoué, sinon celui de `colcon test-result`.
2. Si `artifact-name` et que le job n'est pas annulé, même après un échec : `actions/upload-artifact@v4` de `<workspace>/test-reports`.

Exemple de résumé (MiniPock, tests unitaires) : voir le rapport de la tâche 8 du refactor MiniPock.

## Dépendances

- Actions tierces : `actions/upload-artifact@v4`.

## Points d'attention

- `pytest-args` est un tableau JSON, pas une ligne de commande : `'["-m", "not integration"]'`.
- Les relances (`retries`) masquent un test instable : à réserver aux tests d'intégration, avec un ticket pour le test concerné.
- La couverture Python est mesurée par colcon sur tout le dossier du paquet (`--cov=<paquet>`), tests compris.
- Le résumé ignore les fichiers XML de CTest lui-même ; `colcon test-result` les compte.
