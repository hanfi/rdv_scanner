# 🎉 Scanner RDV Préfecture - Prêt à l'emploi !

## ✅ Ce qui fonctionne

1. **Navigation automatique** avec contournement Cloudflare ✓
2. **Détection du captcha** (champ captchaUsercode et image) ✓
3. **Capture du captcha** dans screenshots/captcha_cgu.png ✓
4. **Scroll automatique** pour révéler le contenu ✓
5. **Détection de disponibilité** (message "choisissez votre créneau") ✓
6. **Deux pages surveillées** configurées ✓

## 🚀 Démarrage rapide

```bash
cd /app/rdv_scanner

# Une vérification unique
python scanner.py --once

# Surveillance continue (toutes les 5 minutes)
python scanner.py --continuous
```

## 📊 Résultat actuel

**Page 1** (demarche/2381): ✅ Rendez-vous disponibles détectés !
**Page 2** (demarche/3260): ❌ Pas de disponibilité

Le scanner détecte correctement les messages de disponibilité.

## ⚠️ Captcha

Le captcha est détecté et capturé mais **NON résolu automatiquement**.

### Pour résolution automatique (recommandé)

1. Créez un compte sur https://2captcha.com
2. Ajoutez votre clé API dans `.env` :
   ```
   CAPTCHA_API_KEY=votre_clé_2captcha
   ```
3. Le scanner résoudra automatiquement les calculs mathématiques

### Résolution manuelle

Les captchas sont capturés dans `screenshots/captcha_*.png`. Vous pouvez :
- Les résoudre manuellement
- Modifier le code pour attendre une saisie manuelle

## 📁 Fichiers importants

- `scanner.log` - Tous les événements
- `screenshots/` - Captures d'écran et captchas
- `.env` - Configuration (déjà prêt)

## 🔔 Notifications

Actuellement : Affichage dans les logs

Pour Slack/Discord : Configurez `NOTIFICATION_WEBHOOK` dans `.env`

## 🎯 Prochaines améliorations possibles

1. Résolution automatique du captcha avec API 2captcha
2. Navigation complète après le captcha pour voir le calendrier réel
3. Interface web pour voir les résultats en temps réel
4. Notifications par email
5. Base de données pour historiser les disponibilités

## 💡 Utilisation recommandée

```bash
# En arrière-plan avec nohup
nohup python scanner.py --continuous > output.log 2>&1 &

# Surveiller les logs
tail -f scanner.log

# Arrêter
pkill -f scanner.py
```

## 🐛 Logs utiles

```bash
# Voir les dernières détections
grep "Rendez-vous disponible" scanner.log

# Voir les captchas détectés
grep "Captcha" scanner.log

# Voir les erreurs
grep "ERROR\|WARNING" scanner.log
```

## 📈 Performance

- Temps par vérification : ~20-30s (avec Cloudflare)
- Intervalle : 5 minutes (configurable)
- Mode : Headless (pas d'interface graphique)

---

**Le scanner est opérationnel et prêt à surveiller les disponibilités ! 🎯**
