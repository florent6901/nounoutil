# Changelog
Format : [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) · versionnage [SemVer](https://semver.org/lang/fr/).

## [1.3.1] - 2026-11-12
### Modifié
- Les jours fériés français sont ajoutés automatiquement au calendrier (une fois par année, modifiables ensuite).
- Le bouton « Jour férié » passe sous la section Nounou dans la fiche du jour ; la carte d'ajout manuel est retirée des Réglages.

## [1.3.0] - 2026-11-12
### Ajouté
- Jours fériés : saisie par jour (🎉) ou ajout automatique des jours fériés français, enfant présent ou absent.
- Réglages : jours fériés payés (oui par défaut) et majoration des jours fériés travaillés.

## [1.2.0] - 2026-11-12
### Ajouté
- Majoration des dimanches travaillés (taux réglable dans Réglages → Rémunération).
- Option « Déduire nounou malade » (activée par défaut).
- README illustré, guide HTTPS (Tailscale Serve, Caddy, Traefik).
### Modifié
- Textes d'aide à l'installation reformulés à l'infinitif.

## [1.1.0] - 2026-11-12
### Ajouté
- Bouton « Installer » dans Réglages (Android : invite native ; iPhone : instructions Safari), service worker, manifeste PWA complété.
- Guide HTTPS (Tailscale, Caddy) pour l'installation complète sur Android.

## [1.0.0] - 2026-11-11
### Ajouté
- Calendrier mensuel : enfant présent / absent / malade, nounou en vacances / malade, heures, repas, km, commentaires.
- Sélection multiple de jours, blocage de l'enfant quand la nounou est absente.
- Plusieurs enfants et plusieurs nounous, historique des contrats (changement de tarif ou de nounou sans toucher au passé).
- Récapitulatif mensuel (heures normales / complémentaires / majorées, salaire net et brut estimé, indemnités).
- Exports PDF et Excel, en lot (ZIP) par enfant, mois et année.
- Thèmes clair, bleu marine et sombre ; PWA installable ; Docker + SQLite.
