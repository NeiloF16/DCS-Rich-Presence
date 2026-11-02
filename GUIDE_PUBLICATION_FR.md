# Publier DCS WORLD Rich Presence v1.0.0

Ce pack contient **le code source et l'automatisation qui construisent l'installateur Windows**. Il ne contient PAS un installateur `.exe` précompilé. L'installation auprès de tes joueurs se fait via la page **Releases** de ton futur dépôt GitHub.

## 1 — Première publication GitHub

Depuis Windows, installe **Git for Windows** et **GitHub CLI** (https://cli.github.com/) si nécessaire. Connecte-toi :

```powershell
gh auth login
```

Extrais ce ZIP dans un dossier, ouvre PowerShell **dans ce dossier** et lance :

```powershell
.\publish-github.ps1
```

Le script affiche les actions prévues et attend que tu écrives **PUBLIC** pour créer un dépôt public, pousser les fichiers, créer le tag `v1.0.0` et lancer la construction. Aucun fichier de ton projet DCS local ne doit être copié dans ce dossier de publication.

## 2 — Récupérer l'installateur

Ouvre ton dépôt GitHub → **Actions** → **Windows installer**. Une fois le workflow terminé avec succès, l'onglet **Releases** doit afficher `DCS-Rich-Presence-Setup-v1.0.0.exe` et `SHA256SUMS.txt`. Si le workflow échoue, lis ses logs ; ne partage pas un binaire non validé.

Il faut un vrai PC/runner Windows pour générer et tester le `.exe`. Les tests effectués dans ce pack ne certifient pas encore l'installateur lui-même sur toutes les configurations DCS/Discord.

## 3 — Test de validation avant partage large

Sur une machine Windows avec DCS et Discord :

1. Fermer DCS, télécharger l'installateur depuis GitHub Releases et l'exécuter.
2. Choisir `Saved Games\DCS`, cliquer sur **Install & Start**.
3. Ouvrir DCS : vérifier avion, théâtre, solo/multi, chronomètre et logo HD dans Discord.
4. Fermer DCS : vérifier que l'activité s'efface. Redémarrer Windows : vérifier le démarrage silencieux si coché.
5. Tester l'option **Remove Hook** et la désinstallation Windows. Vérifier que les autres hooks DCS restent en place.

**Important :** l'identifiant Discord partagé et son asset `dcs_logo` dépendent de l'application Discord configurée par le créateur. Ne supprime pas cette application.

L'installateur n'est pas signé numériquement. Une alerte de réputation Windows SmartScreen peut se produire ; publier le code source et les sommes SHA-256 aide à permettre aux utilisateurs de vérifier le projet. Cela ne remplace pas une signature de code.
