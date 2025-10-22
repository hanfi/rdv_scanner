# 🌟 Guide de Déploiement Railway

## 🚀 Railway - Hébergement Gratuit H24

Railway est la solution parfaite pour héberger ton scanner gratuitement avec **2000h/mois** (83 jours complets).

### 📋 **Étapes de Déploiement**

#### 1. **Créer un Compte Railway**
- Va sur [railway.app](https://railway.app)
- Connecte-toi avec ton compte GitHub

#### 2. **Déployer depuis GitHub**
- Clique sur "New Project"
- Sélectionne "Deploy from GitHub"
- Choisis ton repo `rdv_scanner`
- Railway détecte automatiquement le Dockerfile

#### 3. **Configurer les Variables d'Environnement**

```bash
# Variables OBLIGATOIRES
GEMINI_API_KEY=your_gemini_key_here
PAGE_1_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/2381/cgu/
PAGE_2_URL=https://www.rdv-prefecture.interieur.gouv.fr/rdvpref/reservation/demarche/3260/cgu/

# Configuration anti-Cloudflare (CRITIQUE)
HEADLESS=false
MUTE_BROWSER=true
BACKGROUND_MODE=true
DISPLAY=:99
XVFB_WHD=1366x768x24

# Intervalle de scan
CHECK_INTERVAL=300  # 5 minutes

# Notifications Slack (optionnel)
NOTIFICATION_WEBHOOK=https://hooks.slack.com/services/XXX
```

#### 4. **Test Local Avant Déploiement**
```bash
# Test Python local
python scanner.py --once

# Test Docker (simulation exacte du cloud)
docker build -t rdv-scanner-test .
docker run --rm --env-file .env rdv-scanner-test
```

#### 5. **Déploiement Automatique**
- Railway détecte les changements sur GitHub
- Build + déploiement automatique
- Ton scanner tourne H24 !

---

## 🎯 **Configuration Railway Optimale**

### **Mode Continu H24**
Le container utilise `/start.sh` qui lance :
```bash
python scanner.py --continuous
```

### **Consommation Gratuite**
- **720 heures/mois** utilisées
- **1280 heures** restantes en réserve
- **100% gratuit** pour ton usage

### **Monitoring Railway**
- **Logs en temps réel** dans l'interface
- **Métriques** de performance
- **Redémarrage automatique** si crash
- **Variables d'environnement** sécurisées

---

## 🛡️ **Anti-Cloudflare Intégré**

### **Display Virtuel Automatique**
- Xvfb démarre automatiquement avec `/start.sh`
- Mode non-headless pour contourner Cloudflare
- Aucune configuration supplémentaire nécessaire

### **Arguments Optimisés**
- User-Agent réaliste
- Résolution standard (1366x768)
- Mode arrière-plan sans prise de focus

---

## 📊 **Avantages Railway**

✅ **2000h/mois gratuit** - Plus que suffisant  
✅ **Déploiement automatique** depuis GitHub  
✅ **Variables d'environnement** sécurisées  
✅ **Logs en temps réel** et monitoring  
✅ **Redémarrage automatique** en cas d'erreur  
✅ **SSL automatique** et domaine fourni  
✅ **Support Docker** natif  
✅ **Scaling automatique** si besoin  

---

## 🎯 **Résumé - 3 Étapes Simples**

1. **Test local** : `docker run --rm --env-file .env rdv-scanner-test`
2. **Push sur GitHub** : `git push`
3. **Connecter Railway** → Variables d'env → Deploy automatique !

Ton scanner tournera H24 gratuitement avec scans toutes les 5 minutes ! 🚀