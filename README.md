# FICT Lobbying — Minisite

Site statique généré automatiquement depuis le pipeline FICT.

## GitHub Pages Setup

1. Pousser ce dossier `site/` dans un repo GitHub
2. Dans Settings → Pages : sélectionner la branche `main` et le dossier `/docs` (ou renommer `site/` en `docs/`)
3. L'URL sera : `https://{username}.github.io/{repo}/`

## Structure

- `index.html` — Carte Leaflet interactive (choroplèthe + marqueurs)
- `parlementaires.html` — Tableau filtrable/triable des 925 parlementaires
- `fiche.html` — Fiche détaillée par parlementaire (votes + commissions + sites)
- `partis.html` — Analyse par parti politique
- `groupes.html` — Groupes industriels multi-sites
- `data/` — Fichiers JSON (régénérés par `python3 generate_site.py`)

## Données

Générées par `pipeline.py` puis converties en JSON par `generate_site.py`.
Pour mettre à jour, relancer `python3 pipeline.py` puis `python3 generate_site.py`.
