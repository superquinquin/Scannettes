# Changelog V1.0

## Global
* réécriture et redisign de l'application.
* amélioration globale des performances.
* système de notification intégré dans le lobby et les salons. Une notification est envoyée quand vous ou une autre device réalise une action importante.

## Logging Page
* refonte Graphique de la page.
* Authentification via JWT. Une fois authentifiée, votre browser garde en mémoire l'autorisation d'accès pour toutes les parties /admin/ de l'application pour une durée configurable.

## Lobby
* refonte Graphique de la page
* Unique table pour toutes les étapes du processus.
* Les données de la table sont triables par : Nom de salon, Nom de commandes / inventaires, statuts et par date.
* Les dates référencées dans la table du lobby sont celles de création de la commande sur Odoo pour les commandes et la date de création du salon d'inventaire pour les inventaires.
* Barre de recherche basée sur les noms de salon et les noms de commandes / inventaires.
* Les inventaires peuvent être constitués sur des templates vide et ou des templates de catégories.
* La création des inventaires est au minimum 2 fois plus rapide.
* L'assemblement des inventaires est désormais automatique
* L'option pour désactiver l'utilisation des mots de passe de salon bloque désormais les champs de mot de passe.

## Salons
* refonte Graphique de la page
* Schéma de couleur et conditions d'application pour les produits d'inventaire modifié.
  * Les couleurs ne s'appliquent qu'une fois un salon fermé et assemblé.
  * seuls les Produits vérifiés seront coloré.
  * La couleur dépend désormais de la différence entre le stock Odoo et le stock réellement scanné
* Le processus de scanning est devenu individuel. Les produits scannés ne sont plus partagés entre les devices lors de la phase de scan.
* Vous pouvez modifier la quantité des produits vrac / au poids sans utiliser le scanner (il est nécessaire que l'unité de mesure du produit ne soit pas "unité").
* Le processus de validation est désormais plus rapide.
* Le processus de validation n'empêchera plus des produits sans code-barres ou sans codes-barres principaux d'être validés, tant que ces produits sont bien référencés dans la base de données Odoo.
* La validation automatique sur Odoo des inventaires est désormais activable. Celle des commandes n'est toujours pas effective.

