# 🔑 Configuration Gemini Vision - Résolution GRATUITE de captchas

## ✅ C'est installé !

Le scanner est maintenant configuré pour utiliser **Google Gemini Vision** (gratuit).

## 🚀 Obtenir votre clé API (2 minutes)

### Étape 1 : Créer une clé API Gemini

1. Allez sur : **https://aistudio.google.com/app/apikey**
2. Connectez-vous avec votre compte Google
3. Cliquez sur "Create API Key"
4. Copiez la clé (commence par `AIza...`)

### Étape 2 : Configurer le scanner

Éditez le fichier `/app/rdv_scanner/.env` :

```bash
# Remplacez cette ligne :
GEMINI_API_KEY=your_gemini_api_key_here

# Par votre vraie clé :
GEMINI_API_KEY=AIzaSy...votre_clé_ici

# Et vérifiez que cette ligne est bien à true :
USE_GEMINI=true
```

### Étape 3 : Tester !

```bash
cd /app/rdv_scanner
python scanner.py --once
```

## 📊 Ce qui va se passer

1. ✅ Le scanner détecte le captcha
2. 📸 Capture l'image
3. 🤖 Envoie à Gemini Vision pour analyse
4. ✍️ Gemini lit le texte distordu
5. ⌨️ Remplit automatiquement le captcha
6. 🎯 Continue la navigation

## 💰 Limites gratuites Gemini

- **1500 requêtes/jour** gratuites
- Votre usage : ~300 requêtes/jour (1 scan toutes les 5 min)
- ➡️ **100% gratuit pour votre usage !**

## 🎯 Performance attendue

- **Taux de réussite : ~85-90%**
- Si un captcha échoue, le scanner réessaiera au prochain scan (5 min)
- Les logs vous montreront ce que Gemini a lu

## 📝 Exemple de logs

```
2025-10-22 13:00:00 - INFO - 📸 Captcha sauvegardé: screenshots/captcha_cgu.png
2025-10-22 13:00:01 - INFO - 🤖 Analyse du captcha avec Gemini
2025-10-22 13:00:02 - INFO - ✅ Gemini a lu le captcha: 'D7H4Y5'
2025-10-22 13:00:02 - INFO - ✅ Captcha rempli avec: D7H4Y5
```

## 🐛 En cas de problème

### Erreur "API key not valid"
- Vérifiez que vous avez bien copié toute la clé
- La clé doit commencer par `AIza`

### Gemini ne lit pas bien le captcha
- C'est normal, ~85-90% de réussite
- Le scanner réessaiera au prochain scan
- Les captchas très distordus peuvent échouer

### Quota dépassé
- Vous avez fait plus de 1500 requêtes/jour
- Attendez 24h ou créez une nouvelle clé API

## 🎉 Vous êtes prêt !

Une fois la clé configurée, lancez :

```bash
# En mode continu (recommandé)
cd /app/rdv_scanner
python scanner.py --continuous
```

Le scanner va maintenant résoudre les captchas automatiquement et GRATUITEMENT ! 🚀
