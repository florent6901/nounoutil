<div align="center">

<img src="app/static/icon-192.png" width="110" alt="Nounoutil">

# Nounoutil (Suivi Assmat)

**Présences, salaire et indemnités de l'assistante maternelle, en quelques touches.**
Exports PDF et Excel pour faciliter la déclaration **Pajemploi**.

![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![PWA](https://img.shields.io/badge/PWA-installable-5A0FC8?logo=pwa&logoColor=white)
[![CI](https://github.com/<votre-compte>/nounoutil/actions/workflows/docker-image.yml/badge.svg)](https://github.com/<votre-compte>/nounoutil/actions/workflows/docker-image.yml)
![License](https://img.shields.io/badge/licence-MIT-22c58b)

[Fonctionnalités](#-fonctionnalités) · [Démarrage rapide](#-démarrage-rapide) · [Installer comme application](#-installer-comme-application-pwa) · [Règles de calcul](#-règles-de-calcul) · [Sécurité](#-sécurité)

<img src="docs/hero.png" alt="Aperçu de Nounoutil : calendrier et récapitulatif mensuel" width="100%">

</div>

---

## ✨ Fonctionnalités

| | |
|---|---|
| 📅 **Calendrier** | Enfant *présent / absent / malade*, nounou *en vacances / malade*, heures, repas, km, commentaire par jour |
| ☑️ **Saisie rapide** | Sélection multiple de jours, raccourci « Lun-Ven » |
| 🎉 **Jours fériés** | Jours fériés français ajoutés automatiquement (modifiables jour par jour), enfant présent ou absent, jours payés ou non, majoration réglable |
| 🔒 **Cohérence** | Nounou absente : aucun état possible pour l'enfant ce jour-là |
| 👨‍👩‍👧 **Multi-profils** | Plusieurs enfants, plusieurs nounous |
| 🕓 **Historique des contrats** | Un changement de nounou ou de tarif à une date donnée ne modifie jamais les mois passés |
| 📊 **Récap mensuel** | Heures normales / complémentaires / majorées, dimanches, salaire net et brut estimé, indemnités |
| 📄 **Exports** | PDF et Excel au mois, ou en lot (ZIP par enfant, mois et année) |
| 🎨 **Thèmes** | Clair, bleu marine, sombre |
| 📍 **Repères** | Date du jour entourée en vert, retour au mois courant d'un toucher sur le titre |
| 📱 **Mobile d'abord** | Responsive, installable comme une application |

<div align="center">
<img src="docs/themes.png" alt="Thèmes clair, bleu et sombre" width="85%">
</div>

## 🚀 Démarrage rapide

```bash
git clone https://github.com/<votre-compte>/nounoutil.git
cd nounoutil
docker compose up -d --build
```

Ouvrir `http://<ip-du-serveur>:8080`, puis aller dans **Réglages** pour ajouter une nounou, puis un enfant avec son contrat.

Les données sont stockées dans `./data/asmat.db` (volume Docker) et survivent aux reconstructions.

**Sauvegarde** (cron) :

```bash
0 3 * * * cp /chemin/nounoutil/data/asmat.db /chemin/backup/asmat-$(date +\%F).db
```

**Mise à jour** :

```bash
git pull && docker compose up -d --build
```

## 📲 Installer comme application (PWA)

Dans **Réglages → Application**, le bouton **📲 Installer** lance l'installation (Android) ou affiche les étapes à suivre (iPhone : Safari → Partager → *Sur l'écran d'accueil*).

> ⚠️ **Android / Chrome exige une adresse HTTPS** pour proposer « Installer l'application ». Sur `http://192.168.x.x:8080`, Chrome ne propose que « Créer un raccourci ». L'iPhone accepte l'ajout à l'écran d'accueil, même en HTTP.

Il suffit de placer un **reverse proxy HTTPS** devant l'application. Cinq solutions :

### Option 1 : HTTPS natif (dans `docker-compose.yml`)

L'application sait servir directement en HTTPS, sans reverse proxy. Tout se règle dans la section `environment` de `docker-compose.yml` :

| Variable | Rôle | Défaut |
|---|---|---|
| `HTTPS` | `"true"` pour activer HTTPS, `"false"` pour HTTP | `false` |
| `TLS_MODE` | `selfsigned` : certificat créé automatiquement. `custom` : certificat personnel | `selfsigned` |
| `TLS_DOMAIN` | Mode `selfsigned` : noms et/ou IP du certificat, séparés par des virgules (ex. `192.168.1.82,nounoutil.local`) | `localhost` |
| `TLS_CERT` / `TLS_KEY` | Chemins du certificat et de la clé privée dans le conteneur | `/data/certs/cert.pem` / `key.pem` |

**Certificat auto-signé (automatique)** : mettre `HTTPS: "true"` et renseigner `TLS_DOMAIN` avec l'adresse IP ou le nom d'accès, puis `docker compose up -d --build`. Le certificat est créé au premier démarrage dans `./data/certs/`, conservé ensuite, et régénéré seulement si `TLS_DOMAIN` change ou si moins de 30 jours de validité restent.

Le téléphone ne reconnaît pas ce certificat d'office : l'installation en application ne sera proposée qu'après l'avoir installé sur l'appareil. Le certificat se télécharge sur `https://<ip>:8080/certificat` (passer l'avertissement du navigateur pour cette seule page), puis :
- **Android** : Paramètres → Sécurité → Chiffrement et identifiants → Installer un certificat → *Certificat d'autorité de certification*.
- **iPhone** : ouvrir le fichier, installer le profil, puis Réglages → Général → Informations → Réglages des certificats → activer la confiance totale.

**Certificat personnel (Let's Encrypt, autorité interne…)** : mettre `HTTPS: "true"` et `TLS_MODE: custom`, puis fournir les fichiers au format PEM :
- soit en les déposant dans `./data/certs/` sous les noms `cert.pem` (certificat, chaîne complète incluse) et `key.pem` ;
- soit en montant un dossier (`./certs:/certs:ro`) et en renseignant `TLS_CERT` et `TLS_KEY`.

Un certificat de confiance (par exemple Let's Encrypt) évite toute installation sur le téléphone. Si les fichiers sont absents, le conteneur s'arrête avec un message explicite.

Le certificat est lu au démarrage : après un renouvellement, relancer avec `docker compose restart`.

### Option 2 : Tailscale Serve (simple, sans nom de domaine)

[Tailscale Serve](https://tailscale.com/kb/1312/serve) agit comme un reverse proxy HTTPS, accessible uniquement depuis le réseau privé Tailscale (*tailnet*), avec un certificat valide pour le nom `*.ts.net`.

1. Activer **MagicDNS** et **HTTPS Certificates** dans la console d'administration Tailscale (page *DNS*).
2. Installer Tailscale sur le serveur **et** sur le téléphone (connecté au même compte).
3. Sur le serveur :

```bash
tailscale serve --bg 8080
```

L'application est alors disponible sur `https://<machine>.<tailnet>.ts.net`, y compris hors du domicile.

### Option 3 : Caddy externe (nom de domaine)

[Caddy](https://caddyserver.com/) obtient et renouvelle automatiquement un certificat Let's Encrypt. Il faut un nom de domaine pointant vers le serveur, et les ports 80 et 443 joignables depuis Internet (ou un challenge DNS pour un usage purement domestique).

```caddyfile
nounoutil.exemple.fr {
    reverse_proxy localhost:8080
}
```

### Option 4 : Traefik (environnement Docker)

[Traefik](https://traefik.io/) détecte les conteneurs via leurs labels. Prérequis : une instance Traefik avec un *certresolver* (ici `letsencrypt`) et un réseau Docker partagé (ici `proxy`). Le port interne de l'application est `8000`, la publication du port `8080` devient inutile.

```yaml
services:
  nounoutil:
    build: .
    restart: unless-stopped
    volumes: ["./data:/data"]
    networks: [proxy]
    labels:
      - traefik.enable=true
      - traefik.docker.network=proxy
      - traefik.http.routers.nounoutil.rule=Host(`nounoutil.exemple.fr`)
      - traefik.http.routers.nounoutil.entrypoints=websecure
      - traefik.http.routers.nounoutil.tls.certresolver=letsencrypt
      - traefik.http.services.nounoutil.loadbalancer.server.port=8000
networks:
  proxy:
    external: true
```

Un middleware `basicauth` peut s'ajouter pour protéger l'accès (voir [Sécurité](#-sécurité)).

### Option 5 : test sur un seul téléphone (sans HTTPS)

Dans Chrome Android, ouvrir `chrome://flags/#unsafely-treat-insecure-origin-as-secure`, activer l'option, ajouter l'adresse `http://IP:port`, relancer Chrome, puis menu ⋮ → **Installer l'application**. Réservé aux tests.

## 🧮 Règles de calcul

| Élément | Règle |
|---|---|
| Mensualisé | heures/semaine × semaines/an ÷ 12 × taux horaire net |
| Heures réelles | somme des heures de présence × taux horaire net |
| Heures complémentaires | au-delà du contrat, jusqu'à 45 h/semaine (mensualisé) |
| Heures majorées | au-delà de 45 h/semaine, majoration paramétrable (25 % par défaut) |
| Dimanche travaillé | heures du dimanche × taux horaire × majoration dimanche (0 % par défaut, à régler dans **Réglages → Rémunération**) |
| Jour férié travaillé | heures × taux × majoration jour férié (0 % par défaut, **Réglages → Rémunération**). Dimanche et férié le même jour : la majoration la plus élevée s'applique |
| Jour férié non travaillé | payé par défaut. Mensualisé : salaire maintenu, ou déduit si « non payé ». Heures réelles : payé seulement si « payé » (jours de semaine) |
| Nounou malade | jours déduits par défaut (mensualisé), désactivable dans **Réglages → Rémunération** |
| Enfant malade | déduit seulement si l'option « certificat médical » est activée |
| Brut estimé | net ÷ coefficient (0,7812 par défaut, modifiable) |
| Indemnités | entretien × jours de présence, repas × nombre de repas, km × taux/km |
| Mois à cheval sur deux contrats | calcul par période, mensualisation au prorata des jours calendaires |

> ⚠️ Les montants sont **indicatifs** et ne remplacent ni le contrat, ni la convention collective, ni les règles officielles. Toujours vérifier avant de déclarer sur Pajemploi. Ce projet n'est pas affilié à Pajemploi / URSSAF.

## 🔐 Sécurité

L'application n'a **pas d'authentification**. Ne pas exposer le port directement sur Internet : passer par un VPN (Tailscale, WireGuard) ou placer un reverse proxy avec mot de passe (Caddy, Traefik, Nginx) devant.

## 🗂️ Structure du projet

```
nounoutil/
├── app/
│   ├── app.py              # API Flask, calculs, exports PDF/Excel
│   └── static/             # interface (index.html), service worker, manifeste PWA, icônes
├── docs/                   # visuels du README
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## 🛠️ Développement local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd app && DB=../data/asmat.db flask --app app run --debug
```

## 🔌 API (résumé)

`GET /api/state` · `GET /api/month?child=&ym=` · `POST /api/day` · `POST /api/nday` · `POST /api/child` · `GET /api/export/{pdf|xlsx}?child=&ym=` · `GET /api/bulk?children=&months=&fmt=`

## 🤝 Contribuer

Branches `feat/…`, `fix/…`, `docs/…` · messages de commit [Conventional Commits](https://www.conventionalcommits.org/fr/) (`feat: …`, `fix: …`) · versions `vMAJEUR.MINEUR.CORRECTIF`.

## 📄 Licence

[MIT](LICENSE)
