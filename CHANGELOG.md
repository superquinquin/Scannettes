# Changelog V1.0

## Global
* réécriture et redisign de l'application.
* amélioration globale des performance et utilisation de Websockets.
* systeme de notification intégré dans le lobby et les salons. Une notification est envoyé quand vous ou une autre device réalise une action importante.

## Logging Page
* refonte Graphique de la page.
* Authentification via JWT. Lié au à votre navigateur.

## Lobby
* refonte Graphique de la page
* Unique table pour toute les étapes du processus.
* Les données sont triable par: Nom de salon, Nom de commandes / inventaires, status et par date.
* Les dates référencées dans la table du lobby sont celles de création de la commande sur Odoo pour les commandes et la date de création du salon d'inventaire pour les inventaires.
* Barre de recherche basée sur les nom de salon et les noms de commandes / inventaires.
* Les inventaires peuvent être constitué sur des templates vide et ou des templates de catégories.
* La création des inventaires est au minimum 2 fois plus rapide.
* L'assemblement des inventaires est automatique
* L'option pour désactiver l'utilisation des mots de passe de salon bloque désormais les champs de mot de passe.

## Salons
* refonte Graphique de la page
* Schéma de couleur et leur conditions d'application pour les produits d'inventaire revu.
  * Les coulleurs ne s'appliquent qu'une fois un salon fermé et assemblé.
  * seul les Produits vérifié se véront apposé une couleur.
  * La couleur dépend de la différence entre le stock Odoo et le stock réellement scanné (du vert vers le rouge/violet).
* Le processus de scanning est devenu individuel. Les produits scannés ne sont plus partagé entre les devices lors du scan.
* Vous pouvez modifier la quantités des produits vrac / au poid sans utiliser le scanner (il est nécessaire que l'unité de mesure du produits ne soit pas "unité").
* Le processus de validation est désormais plus rapide.
* Le processus de validation n'empechera plus des produits sans code-barres ou sans code-barres principaux d'être validé, tant que ces produits sont bien référencé dans la base de donnée Odoo.
* La validation automatique sur Odoo des inventaire est désormais activable. Celle des commandes n'est toujours pas éffective.

