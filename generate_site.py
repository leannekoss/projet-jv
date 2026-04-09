#!/usr/bin/env python3
"""
Génère le minisite statique FICT (GitHub Pages) depuis les CSV de sortie du pipeline.
Outputs dans ~/fict-lobbying/site/
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

OUTPUT_DIR = Path('/Users/henri/fict-lobbying')
SITE_DIR = OUTPUT_DIR / 'site'
DATA_DIR = SITE_DIR / 'data'

SCRUTINS_META = [
    {'id': 'egalim1',          'label': 'EGALIM 1 (2018)', 'loi': '2018-938'},
    {'id': 'egalim2',          'label': 'EGALIM 2 (2021)', 'loi': '2021-1357'},
    {'id': 'egalim3',          'label': 'EGALIM 3 / Descrozaille (2023)', 'loi': '2023-221'},
    {'id': 'loa2024',          'label': 'LOA 2024', 'loi': 'PLOA-2024'},
    {'id': 'revenu_agri',      'label': 'PPL Revenu agri (2024)', 'loi': 'PPL'},
    {'id': 'marges_agroalim',  'label': 'PPL Marges agroalim (rejeté)', 'loi': 'PPL'},
    {'id': 'stabilite_agro',   'label': 'PPL Stabilité éco agroalimentaire (2025)', 'loi': 'PPL-17e'},
]

ENGAGEMENT_COLS = [
    'commission_enquete_gd', 'mission_nitrites', 'mission_suivi_gd',
    'mission_controle_egalim1', 'mission_appli_loi2022', 'groupe_etude_iaa',
    'groupe_etude_agri', 'observatoire_marges', 'mission_autonomie_alim',
]

GROUP_COLORS = {
    'RN': '#003189', 'DR': '#4b0082', 'NFP': '#e31d1c', 'EPR': '#ff8c00',
    'LIOT': '#008000', 'UDR': '#6a0dad', 'GDR': '#cc0000', 'Ensemble': '#ff8c00',
    'Socialistes': '#e31d1c', 'Écologiste': '#00aa44', 'LFI': '#cc0000',
}

def group_color(groupe):
    for k, v in GROUP_COLORS.items():
        if k.lower() in groupe.lower():
            return v
    return '#666'


def csv_to_list(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def build_json_data():
    print('[1] Chargement des CSV et génération JSON...')
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Parlementaires
    parl = csv_to_list(OUTPUT_DIR / 'parlementaires_fict.csv')
    parl_json = []
    for p in parl:
        votes = {sc['id']: (p.get(f'vote_{sc["id"]}') or None) for sc in SCRUTINS_META}
        engagement = {col: p.get(col, '') == 'True' for col in ENGAGEMENT_COLS}
        parl_json.append({
            'id': p.get('id', '') or p.get('nom_complet', '').lower().replace(' ', '-'),
            'nom': p['nom_complet'],
            'chambre': p['chambre'],
            'groupe': p['groupe'],
            'groupe_abrev': p.get('groupe_abrev', p['groupe'][:6]),
            'dept': p['code_dept'],
            'nom_dept': p['nom_dept'],
            'circo': p.get('circo', ''),
            'commission': p.get('commission', ''),
            'commission_agri': p.get('membre_commission_agri', '') == 'True',
            'commission_eco': p.get('membre_commission_eco', '') == 'True',
            'mission_egalim': p.get('membre_mission_egalim', '') == 'True',
            'nb_commissions': int(p.get('nb_commissions_fict', 0) or 0),
            'participation': float(p.get('score_participation', 0) or 0),
            'loyaute': float(p.get('score_loyaute', 0) or 0),
            'nb_sites': int(p.get('nb_sites_fict', 0) or 0),
            'score_eco': float(p.get('score_eco', 0) or 0),
            'score_impl': float(p.get('score_implication', 0) or 0),
            'score_engagement': int(p.get('score_engagement', 0) or 0),
            'nb_amendements_deposes': int(p.get('nb_amendements_deposes', 0) or 0),
            'nb_amendements_cosignes': int(p.get('nb_amendements_cosignes', 0) or 0),
            'nb_amendements_adoptes': int(p.get('nb_amendements_adoptes', 0) or 0),
            'hemicycle_interventions': int(p.get('hemicycle_interventions', 0) or 0),
            'questions_orales': int(p.get('questions_orales', 0) or 0),
            'questions_ecrites': int(p.get('questions_ecrites', 0) or 0),
            'propositions_ecrites': int(p.get('propositions_ecrites', 0) or 0),
            'propositions_signees': int(p.get('propositions_signees', 0) or 0),
            'amendements_adoptes_nd': int(p.get('amendements_adoptes_nd', 0) or 0),
            'semaines_presence': int(p.get('semaines_presence', 0) or 0),
            'interventions_nitrites': int(p.get('interventions_nitrites', 0) or 0),
            # Score recalculé avec enrichissements (score_engagement inclus)
            'score': round(
                float(p.get('score_eco', 0) or 0) *
                (1 + (float(p.get('score_implication', 0) or 0) + int(p.get('score_engagement', 0) or 0)) / 10),
                2
            ),
            'position': p.get('position_votes_agri', 'inconnu'),
            'entreprises': p.get('entreprises_fict_zone', ''),
            'mail': p.get('mail', ''),
            'twitter': p.get('twitter', ''),
            'votes': votes,
            'engagement': engagement,
        })
    (DATA_DIR / 'parlementaires.json').write_text(
        json.dumps(parl_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ parlementaires.json ({len(parl_json)} entrées)')

    # Sites de production
    sites_raw = csv_to_list(OUTPUT_DIR / 'sites_production_fict.csv')
    naf_labels = {
        '10.13A': 'Préparation industrielle viande', '10.13B': 'Charcuterie',
        '10.11Z': 'Abattage / transformation viande', '10.12Z': 'Transformation volaille',
    }
    sites_json = []
    for s in sites_raw:
        try:
            lat = float(s['latitude']) if s.get('latitude') else None
            lng = float(s['longitude']) if s.get('longitude') else None
        except (ValueError, TypeError):
            lat = lng = None
        if not lat or not lng:
            continue
        sites_json.append({
            'nom': s['nom_entreprise_fict'],
            'nom_api': s.get('nom_api', s['nom_entreprise_fict']),
            'siren': s.get('siren', ''),
            'syndicat': s.get('syndicat_regional', ''),
            'dept': s['code_dept'],
            'commune': s.get('commune', ''),
            'cp': s.get('code_postal', ''),
            'naf': s.get('naf', ''),
            'naf_label': naf_labels.get(s.get('naf', ''), s.get('naf', '')),
            'type_site': s.get('type_site', 'production'),
            'lat': lat,
            'lng': lng,
        })
    (DATA_DIR / 'sites.json').write_text(
        json.dumps(sites_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ sites.json ({len(sites_json)} sites)')

    # Partis
    partis_raw = csv_to_list(OUTPUT_DIR / 'analyse_partis_fict.csv')
    partis_json = [
        {
            'groupe': p['groupe'],
            'chambre': p['chambre'],
            'nb_elus': int(p.get('nb_elus', 0) or 0),
            'nb_elus_zone': int(p.get('nb_elus_zone_fict', 0) or 0),
            'pct_zone': float(p.get('pct_elus_zone_fict', 0) or 0),
            'total_sites': int(p.get('total_sites_zones', 0) or 0),
            'score_moyen': float(p.get('score_moyen', 0) or 0),
            'color': group_color(p['groupe']),
        }
        for p in partis_raw
    ]
    (DATA_DIR / 'partis.json').write_text(
        json.dumps(partis_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ partis.json ({len(partis_json)} groupes)')

    # Groupes industriels
    groupes_raw = csv_to_list(OUTPUT_DIR / 'groupes_industriels_multisite.csv')
    groupes_json = [
        {
            'nom': g['nom_complet'],
            'siren': g.get('siren', ''),
            'nb_sites': int(g.get('nb_sites', 0) or 0),
            'nb_depts': int(g.get('nb_departements', 0) or 0),
            'depts': g.get('departements', ''),
            'categorie': g.get('categorie', ''),
        }
        for g in groupes_raw
    ]
    (DATA_DIR / 'groupes.json').write_text(
        json.dumps(groupes_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ groupes.json ({len(groupes_json)} groupes industriels)')

    # Membres travaux parlementaires
    membres_raw = csv_to_list(OUTPUT_DIR / 'membres_travaux_parlementaires.csv')
    vote_ids = [sc['id'] for sc in SCRUTINS_META]

    membres_json = []
    for m in membres_raw:
        votes = {vid: (m.get(f'vote_{vid}') or None) for vid in vote_ids}
        engagement = {col: m.get(col, '') == 'True' for col in ENGAGEMENT_COLS}
        membres_json.append({
            'nom': m['nom_complet'],
            'chambre': m['chambre'],
            'groupe': m['groupe'],
            'groupe_abrev': m.get('groupe_abrev', m['groupe'][:6]),
            'dept': m['code_dept'],
            'nom_dept': m['nom_dept'],
            'commission': m.get('commission', ''),
            'commission_eco': m.get('membre_commission_eco', '') == 'True',
            'mission_egalim': m.get('membre_mission_egalim', '') == 'True',
            'position': m.get('position_votes_agri', 'inconnu'),
            'nb_sites': int(m.get('nb_sites_fict', 0) or 0),
            'score': float(m.get('score_fict', 0) or 0),
            'score_engagement': int(m.get('score_engagement', 0) or 0),
            'nb_amendements_deposes': int(m.get('nb_amendements_deposes', 0) or 0),
            'nb_amendements_cosignes': int(m.get('nb_amendements_cosignes', 0) or 0),
            'nb_amendements_adoptes': int(m.get('nb_amendements_adoptes', 0) or 0),
            'hemicycle_interventions': int(m.get('hemicycle_interventions', 0) or 0),
            'questions_orales': int(m.get('questions_orales', 0) or 0),
            'propositions_ecrites': int(m.get('propositions_ecrites', 0) or 0),
            'propositions_signees': int(m.get('propositions_signees', 0) or 0),
            'interventions_nitrites': int(m.get('interventions_nitrites', 0) or 0),
            'mail': m.get('mail', ''),
            'votes': votes,
            'engagement': engagement,
        })
    (DATA_DIR / 'membres_travaux.json').write_text(
        json.dumps(membres_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ membres_travaux.json ({len(membres_json)} membres)')

    # Entreprises FICT enrichies
    entr_raw = csv_to_list(OUTPUT_DIR / 'entreprises_fict_enrichies.csv')
    entr_json = []
    for e in entr_raw:
        if e.get('statut') == 'non trouvé':
            continue
        ca = e.get('ca', '')
        entr_json.append({
            'siren': e.get('siren', ''),
            'nom_fict': e.get('nom_fict', ''),
            'denomination': e.get('denomination', ''),
            'syndicat': e.get('syndicat', ''),
            'nb_sites': int(e.get('nb_sites', 0) or 0),
            'naf': e.get('naf', ''),
            'statut': e.get('statut', ''),
            'forme_juridique': e.get('forme_juridique', ''),
            'date_creation': e.get('date_creation', ''),
            'effectif': e.get('effectif_label', ''),
            'ca': int(ca) if ca else None,
            'resultat_net': int(e.get('resultat_net', '') or 0) if e.get('resultat_net') else None,
            'annee_comptes': e.get('annee_comptes', ''),
            'dirigeants': e.get('dirigeants', ''),
        })
    entr_json.sort(key=lambda x: -(x.get('ca') or 0))
    (DATA_DIR / 'entreprises.json').write_text(
        json.dumps(entr_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'    ✅ entreprises.json ({len(entr_json)} entreprises enrichies)')

    # Eurodéputés (V2)
    eu_csv = OUTPUT_DIR / 'parlementaires_eu.csv'
    if eu_csv.exists():
        meps_raw = csv_to_list(eu_csv)
        meps_json = [{
            'id':            m['id'],
            'nom':           m['nom_complet'],
            'prenom':        m.get('prenom', ''),
            'nom_famille':   m.get('nom', ''),
            'groupe':        m.get('groupe', ''),
            'groupe_abrev':  m.get('groupe_abrev', ''),
            'chambre':       'PE',
            'url_photo':     m.get('url_photo', ''),
            'url_fiche':     m.get('url_fiche', ''),
            'additifs':      int(m.get('additifs_alimentaires', 0) or 0),
            'farm_to_fork':  int(m.get('farm_to_fork', 0) or 0),
            'nitrites':      int(m.get('nitrites', 0) or 0),
            'egalim':        int(m.get('egalim', 0) or 0),
            'score_eu':      int(m.get('score_eu', 0) or 0),
        } for m in meps_raw]
        meps_json.sort(key=lambda x: -x['score_eu'])
        (DATA_DIR / 'meps.json').write_text(
            json.dumps(meps_json, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'    ✅ meps.json ({len(meps_json)} eurodéputés français)')
    else:
        meps_json = []
        print(f'    ⚠️  parlementaires_eu.csv absent - page Europe ignorée')

    return parl_json, sites_json, partis_json, groupes_json, meps_json


NOINDEX = '<meta name="robots" content="noindex, nofollow">'
FAVICON = '<link rel="icon" href="data:image/svg+xml,<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'><rect x=\'2\' y=\'17\' width=\'6\' height=\'13\' fill=\'%23e85d04\'/><rect x=\'11\' y=\'9\' width=\'6\' height=\'21\' fill=\'%231a1a2e\'/><rect x=\'20\' y=\'2\' width=\'6\' height=\'28\' fill=\'%23e85d04\'/><rect x=\'1\' y=\'30\' width=\'30\' height=\'2\' fill=\'%231a1a2e\'/></svg>">'


def write_nav(active_page):
    pages = [
        ('index.html', '🗺️ Carte'),
        ('parlementaires.html', '👥 Parlementaires'),
        ('partis.html', '🏛️ Partis'),
        ('groupes.html', '🏭 Industriels'),
        ('entreprises.html', '🏢 Entreprises'),
        ('europe.html', '🇪🇺 Europe V2'),
        ('methodologie.html', '📖 Méthode'),
    ]
    items = ''
    for href, label in pages:
        cls = 'active' if href == active_page else ''
        items += f'<a href="{href}" class="nav-link {cls}">{label}</a>'
    brand_cls = 'active' if active_page == 'accueil.html' else ''
    brand = f'<a href="accueil.html" class="nav-brand-link {brand_cls}">🥩 FICT</a>'
    return (f'<nav class="top-nav">{brand}'
            f'<div class="nav-links">{items}</div></nav>'
            f'<style>.nav-brand-link{{color:white;text-decoration:none;font-weight:700;'
            f'font-size:16px;white-space:nowrap;padding:4px 8px;border-radius:6px;transition:all .2s}}'
            f'.nav-brand-link:hover,.nav-brand-link.active{{background:rgba(255,255,255,.15)}}</style>')


BASE_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f7; color: #1d1d1f; color-scheme: light; }
.top-nav { background: #1a1a2e; color: white; padding: 0 24px; display: flex; align-items: center; gap: 24px; height: 52px; position: sticky; top: 0; z-index: 1000; }
.nav-brand { font-weight: 700; font-size: 16px; white-space: nowrap; }
.nav-links { display: flex; gap: 4px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.nav-link { color: rgba(255,255,255,0.75); text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 13px; transition: all .2s; white-space: nowrap; }
.nav-link:hover, .nav-link.active { background: rgba(255,255,255,0.15); color: white; }
.container { max-width: 1200px; margin: 0 auto; padding: 24px 20px; }
.page-title { font-size: 28px; font-weight: 800; margin-bottom: 6px; }
.page-subtitle { font-size: 14px; color: #666; margin-bottom: 24px; }
.card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: box-shadow .2s; }
.card:hover { box-shadow: 0 4px 16px rgba(0,0,0,.12); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
.badge-agri { background: #d4edda; color: #155724; }
.badge-eco { background: #cce5ff; color: #004085; }
.badge-egalim { background: #fff3cd; color: #856404; }
.badge-an { background: #fce8d5; color: #8a3a00; }
.badge-sen { background: #d9e8ff; color: #003680; }
.vote-pour { background: #28a745; color: white; }
.vote-contre { background: #dc3545; color: white; }
.vote-abstention { background: #fd7e14; color: white; }
.vote-absent { background: #aaa; color: white; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { text-align: left; padding: 10px 12px; background: #f8f9fa; font-weight: 600; font-size: 12px; color: #555; border-bottom: 2px solid #eee; cursor: pointer; user-select: none; white-space: nowrap; }
th:hover { background: #e9ecef; }
td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
tr:hover td { background: #fafafa; }
.search-bar { width: 100%; padding: 10px 14px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; margin-bottom: 12px; position: relative; z-index: 1; }
.search-bar:focus { outline: 2px solid #e85d04; outline-offset: 1px; border-color: #e85d04; }
.filter-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.filter-select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; background: white; color: #1d1d1f; }
.filter-select option { background: white; color: #1d1d1f; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }
.stat-card { background: white; border-radius: 10px; padding: 20px 16px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: box-shadow .2s, transform .2s; border: 1px solid transparent; }
.stat-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.12); transform: translateY(-1px); border-color: rgba(232,93,4,0.15); }
.stat-value { font-size: 36px; font-weight: 700; color: #1a1a2e; font-feature-settings: "tnum"; }
.stat-label { font-size: 12px; color: #666; margin-top: 6px; }
.pagination { display: flex; gap: 4px; justify-content: center; margin-top: 16px; flex-wrap: wrap; }
.page-btn { padding: 5px 10px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer; font-size: 13px; }
.page-btn.active { background: #1a1a2e; color: white; border-color: #1a1a2e; }
.page-btn:hover:not(.active) { background: #f0f0f0; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
:focus-visible { outline: 2px solid #e85d04; outline-offset: 2px; }
@media(max-width:640px) {
  .top-nav { padding: 6px 12px; gap: 8px; height: auto; flex-wrap: wrap; }
  .nav-links { width: 100%; overflow-x: auto; }
  .nav-link { padding: 4px 8px; font-size: 11px; }
}
@media(max-width:768px) {
  table { font-size: 12px; }
  th, td { padding: 6px 8px; }
  .filter-row { flex-direction: column; }
  .filter-select { width: 100%; }
}
"""


def write_index():
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Carte parlementaire</title>
{FAVICON}
<style>{BASE_CSS}
#map {{ width:100%; height:calc(100vh - 52px); }}
#side-panel {{ width:380px; flex-shrink:0; background:white; border-left:1px solid #ddd; overflow-y:auto; display:flex; flex-direction:column; }}
.map-wrap {{ display:flex; height:calc(100vh - 52px); }}
@media(max-width:768px) {{
  .map-wrap {{ flex-direction:column; height:auto; }}
  #map {{ height:50vh; }}
  #side-panel {{ width:100%; border-left:none; border-top:1px solid #ddd; max-height:50vh; }}
}}
#panel-header {{ padding:14px 16px; background:#1a1a2e; color:white; font-weight:600; font-size:14px; }}
#panel-header span {{ display:block; font-size:11px; font-weight:400; opacity:.7; margin-top:3px; }}
#panel-filters {{ padding:8px 12px; border-bottom:1px solid #eee; }}
#filter-chambre {{ width:100%; padding:5px 8px; border:1px solid #ddd; border-radius:4px; font-size:12px; background:white; color:#1d1d1f; }}
#panel-content {{ padding:12px; flex:1; }}
.dept-title {{ font-size:17px; font-weight:700; color:#1a1a2e; margin-bottom:3px; }}
.dept-stats {{ font-size:12px; color:#666; margin-bottom:10px; }}
.parl-card {{ background:#f8f9fa; border-radius:8px; padding:10px 12px; margin-bottom:8px; border-left:4px solid #ccc; }}
.parl-card.an {{ border-left-color:#e85d04; }}
.parl-card.sen {{ border-left-color:#4361ee; }}
.parl-nom {{ font-weight:600; font-size:13px; }}
.parl-groupe {{ font-size:11px; color:#666; margin-top:2px; }}
.parl-score {{ float:right; font-size:12px; background:#1a1a2e; color:white; padding:2px 7px; border-radius:4px; }}
.empty-state {{ text-align:center; color:#999; padding:40px 16px; font-size:13px; }}
.legend {{ background:white; padding:10px 14px; border-radius:8px; box-shadow:0 1px 5px rgba(0,0,0,.3); font-size:11px; }}
</style>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
</head>
<body>
{write_nav('index.html')}
<div class="map-wrap">
<div id="map"></div>
<div id="side-panel">
  <div id="panel-header">Carte FICT - Implantations industrielles
    <span>Cliquez sur un département pour voir les parlementaires</span>
  </div>
  <div id="panel-filters">
    <label for="filter-chambre" class="sr-only">Filtrer par chambre</label>
    <select id="filter-chambre" onchange="renderPanel()">
      <option value="">AN + Sénat</option>
      <option value="AN">Assemblée Nationale</option>
      <option value="SEN">Sénat</option>
    </select>
  </div>
  <div id="panel-content"><div class="empty-state">👆 Cliquez sur un département coloré pour explorer</div></div>
</div>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const SCRUTIN_LABELS = {{"egalim1":"EGALIM 1","egalim2":"EGALIM 2","egalim3":"EGALIM 3","loa2024":"LOA 2024","revenu_agri":"PPL Revenu Agri","marges_agroalim":"PPL Marges"}};
const VOTE_COLORS = {{pour:"#28a745",contre:"#dc3545",abstention:"#fd7e14",absent:"#aaa"}};
const NAF_COLORS = {{"10.13B":"#e85d04","10.13A":"#f77f00","10.11Z":"#7b2d8b","10.12Z":"#2e6db4"}};

function voteCell(v) {{
  if (!v) return '<span style="color:#bbb;font-size:10px">-</span>';
  const c = VOTE_COLORS[v] || '#ddd';
  return `<span style="display:inline-block;padding:1px 5px;border-radius:3px;background:${{c}};color:${{v==='absent'?'#555':'white'}};font-size:10px;font-weight:600">${{v}}</span>`;
}}

const map = L.map('map').setView([46.5, 2.5], 6);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution:'© OpenStreetMap © CartoDB', subdomains:'abcd', maxZoom:19
}}).addTo(map);

function getColor(nb) {{
  return nb>=20?'#800026':nb>=15?'#BD0026':nb>=10?'#E31A1C':nb>=7?'#FC4E2A':nb>=4?'#FD8D3C':nb>=2?'#FEB24C':nb>=1?'#FED976':'#eee';
}}

let currentDept=null, geojsonLayer=null, deptData={{}};

Promise.all([
  fetch('data/sites.json').then(r=>r.json()),
  fetch('data/parlementaires.json').then(r=>r.json()),
]).then(([sites, parls]) => {{
  // Index parlementaires par dept
  parls.forEach(p => {{
    if (!p.dept) return;
    if (!deptData[p.dept]) deptData[p.dept] = {{nb_sites:0, parl:[]}};
    deptData[p.dept].parl.push(p);
  }});

  // Sites markers
  sites.forEach(s => {{
    if (!s.lat||!s.lng) return;
    const color = NAF_COLORS[s.naf] || '#555';
    const icon = L.divIcon({{
      className:'',
      html:`<div style="width:10px;height:10px;border-radius:50%;background:${{color}};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.5)"></div>`,
      iconSize:[10,10], iconAnchor:[5,5]
    }});
    L.marker([s.lat,s.lng],{{icon}}).bindPopup(
      `<div style="min-width:190px;font-size:13px"><b>${{s.nom}}</b>` +
      (s.nom_api&&s.nom_api!==s.nom?`<div style="font-size:11px;color:#666">${{s.nom_api}}</div>`:'') +
      `<div style="margin-top:5px"><span style="background:${{color}};color:white;padding:2px 6px;border-radius:3px;font-size:11px">${{s.naf_label}}</span></div>` +
      `<div style="margin-top:4px;color:#444">📍 ${{s.commune}} ${{s.cp}}</div>` +
      (s.syndicat?`<div style="font-size:11px;color:#888">Syndicat : ${{s.syndicat}}</div>`:'') +
      `</div>`
    ).addTo(map);
    if (s.dept) {{ if (!deptData[s.dept]) deptData[s.dept]={{nb_sites:0,parl:[]}}; deptData[s.dept].nb_sites++; }}
  }});

  // GeoJSON choroplèthe
  return fetch('https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson');
}}).then(r=>r.json()).then(geo => {{
  function style(f) {{
    const nb = (deptData[f.properties.code]||{{}}).nb_sites||0;
    return {{fillColor:getColor(nb),weight:1,color:'#666',fillOpacity:.75}};
  }}
  function onEach(f,l) {{
    l.on({{
      mouseover: e => {{ e.target.setStyle({{weight:2.5,color:'#333',fillOpacity:.9}}); e.target.bringToFront(); }},
      mouseout: e => {{ if (currentDept!==f.properties.code) geojsonLayer.resetStyle(e.target); }},
      click: e => {{
        if (currentDept) geojsonLayer.eachLayer(ll => {{ if(ll.feature&&ll.feature.properties.code===currentDept) geojsonLayer.resetStyle(ll); }});
        currentDept=f.properties.code;
        e.target.setStyle({{weight:3,color:'#1a1a2e',fillOpacity:.9}});
        renderPanel(f.properties);
      }}
    }});
    const nb=(deptData[f.properties.code]||{{}}).nb_sites||0;
    const nbParl=(deptData[f.properties.code]||{{parl:[]}}).parl?((deptData[f.properties.code]||{{}}).parl||[]).length:0;
    l.bindTooltip(`<b>${{f.properties.nom}} (${{f.properties.code}})</b><br>${{nb}} site${{nb>1?'s':''}} FICT - ${{nbParl}} elu${{nbParl>1?'s':''}}`,{{sticky:true}});
  }}
  geojsonLayer = L.geoJSON(geo,{{style,onEachFeature:onEach}}).addTo(map);
}}).catch(e=>console.warn('GeoJSON error',e));

function renderPanel(deptProps) {{
  const content=document.getElementById('panel-content');
  if(!deptProps) return;
  const code=deptProps.code, nom=deptProps.nom;
  const dd=deptData[code]||{{}};
  const nb=dd.nb_sites||0;
  const parl=dd.parl||[];
  const filter=document.getElementById('filter-chambre').value;
  const filtered=filter?parl.filter(p=>p.chambre===filter):parl;
  filtered.sort((a,b)=>b.score-a.score);

  let html=`<div class="dept-title">📍 ${{nom}} (${{code}})</div>
    <div class="dept-stats">${{nb}} site(s) FICT · ${{parl.filter(p=>p.chambre==='AN').length}} député(s) · ${{parl.filter(p=>p.chambre==='SEN').length}} sénateur(s)</div>`;

  if (!filtered.length) {{
    html+='<div class="empty-state">Aucun parlementaire</div>';
  }} else {{
    filtered.forEach(p => {{
      const posColor=p.position&&p.position.includes('pro')?'color:#155724':p.position&&p.position.includes('réservé')?'color:#721c24':'color:#555';
      let votesHtml='';
      if (p.chambre==='AN'&&p.votes) {{
        const hasVotes=Object.values(p.votes).some(v=>v&&v!=='absent');
        if (hasVotes) {{
          votesHtml='<div style="margin-top:5px;border-top:1px solid #eee;padding-top:4px">'+
            Object.entries(SCRUTIN_LABELS).map(([k,label])=>
              `<div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;margin:1px 0"><span style="color:#777">${{label}}</span>${{voteCell((p.votes||{{}})[k])}}</div>`
            ).join('')+'</div>';
        }}
      }}
      html+=`<div class="parl-card ${{p.chambre.toLowerCase()}}">
        <span class="parl-score">⭐ ${{p.score.toFixed(1)}}</span>
        <div class="parl-nom">${{p.nom}} ${{p.mail?`<a href="mailto:${{p.mail}}" style="color:#4361ee;font-size:11px">✉️</a>`:''}}</div>
        <div class="parl-groupe">${{p.chambre==='AN'?'🏛️ AN':'🏦 Sénat'}} · ${{p.groupe}}</div>
        ${{p.commission_agri?'<span class="badge badge-agri">🌾 Agri</span>':''}}
        ${{p.commission_eco?'<span class="badge badge-eco">🏦 Eco</span>':''}}
        ${{p.mission_egalim?'<span class="badge badge-egalim">⚖️ EGALIM</span>':''}}
        ${{p.position&&p.chambre==='AN'?`<div style="font-size:10px;margin-top:3px;${{posColor}}">↗ ${{p.position}}</div>`:''}}
        ${{p.nb_sites>0?`<div style="font-size:11px;color:#666;margin-top:2px">Zone : ${{p.nb_sites}} site(s)</div>`:''}}
        ${{votesHtml}}
      </div>`;
    }});
  }}
  content.innerHTML=html;
}}

// Légende choroplèthe
const leg=L.control({{position:'bottomleft'}});
leg.onAdd=()=>{{
  const d=L.DomUtil.create('div','legend');
  d.style.cssText='background:white;padding:12px 16px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.25);font-size:12px;min-width:140px';
  d.innerHTML='<div style="font-weight:700;font-size:13px;margin-bottom:8px;color:#1a1a2e">Sites FICT par dept.</div>'+
    [{{n:20,l:'20+'}},{{n:15,l:'15-19'}},{{n:10,l:'10-14'}},{{n:7,l:'7-9'}},{{n:4,l:'4-6'}},{{n:2,l:'2-3'}},{{n:1,l:'1'}},{{n:0,l:'0'}}]
    .map(({{n,l}})=>`<div style="display:flex;align-items:center;gap:8px;margin:3px 0"><div style="width:18px;height:14px;border-radius:2px;background:${{getColor(n)}};border:1px solid rgba(0,0,0,.1)"></div><span>${{l}}</span></div>`)
    .join('');
  return d;
}};
leg.addTo(map);
</script>
</body>
</html>"""
    (SITE_DIR / 'index.html').write_text(html, encoding='utf-8')
    print('    ✅ index.html (carte Leaflet)')


def write_parlementaires():
    # Colonnes fixes: 0-Nom 1-Chambre 2-Groupe 3-Dept 4-Sites 5-Score 6-Engagement 7-Interventions 8-PPL 9-Position 10-Commissions → scrutins à partir de 11
    scrutin_headers = ''.join(f'<th onclick="sortTable({11+i})">{s["label"][:12]}</th>' for i, s in enumerate(SCRUTINS_META))
    scrutin_id_list = json.dumps([s['id'] for s in SCRUTINS_META])
    scrutin_label_list = json.dumps({s['id']: s['label'] for s in SCRUTINS_META})

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Parlementaires</title>
{FAVICON}
<style>{BASE_CSS}
@media(max-width:768px) {{ #table th:nth-child(n+7), #table td:nth-child(n+7) {{ display:none; }} }}
</style>
</head>
<body>
{write_nav('parlementaires.html')}
<div class="container">
  <div class="page-title">👥 Parlementaires</div>
  <div class="page-subtitle">925 élus classés par score FICT (implantation × implication)</div>
  <div class="stats-grid" id="stats-grid"></div>
  <div class="card">
    <label for="search" class="sr-only">Rechercher un parlementaire</label>
    <input type="text" class="search-bar" id="search" placeholder="🔍 Rechercher par nom, groupe, département..." oninput="renderTable()">
    <div class="filter-row">
      <label for="f-chambre" class="sr-only">Filtrer par chambre</label>
      <select class="filter-select" id="f-chambre" onchange="renderTable()"><option value="">AN + Sénat</option><option value="AN">Assemblée Nationale</option><option value="SEN">Sénat</option></select>
      <label for="f-dept" class="sr-only">Filtrer par département</label>
      <select class="filter-select" id="f-dept" onchange="renderTable()"><option value="">Tous les depts</option></select>
      <label for="f-groupe" class="sr-only">Filtrer par groupe politique</label>
      <select class="filter-select" id="f-groupe" onchange="renderTable()"><option value="">Tous les groupes</option></select>
      <label for="f-commission" class="sr-only">Filtrer par commission</label>
      <select class="filter-select" id="f-commission" onchange="renderTable()">
        <option value="">Toutes commissions</option>
        <option value="agri">Commission Agriculture</option>
        <option value="eco">Commission Économique</option>
        <option value="egalim">Mission EGALIM</option>
      </select>
      <label for="f-sites" class="sr-only">Filtrer par présence sites</label>
      <select class="filter-select" id="f-sites" onchange="renderTable()"><option value="">Tous les élus</option><option value="1">Avec sites FICT</option></select>
    </div>
    <div id="result-count" style="font-size:12px;color:#666;margin-bottom:8px"></div>
    <div style="overflow-x:auto">
    <table id="table">
      <thead><tr>
        <th onclick="sortTable(0)">Nom ↕</th>
        <th onclick="sortTable(1)">Chambre ↕</th>
        <th onclick="sortTable(2)">Groupe ↕</th>
        <th onclick="sortTable(3)">Dept ↕</th>
        <th onclick="sortTable(4)">Sites ↕</th>
        <th onclick="sortTable(5)">Score FICT ↕</th>
        <th onclick="sortTable(6)">Engagement ↕</th>
        <th onclick="sortTable(7)">Interv. ↕</th>
        <th onclick="sortTable(8)">PPL ↕</th>
        <th>Position votes</th>
        <th>Commissions</th>
        {scrutin_headers}
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
    <div class="pagination" id="pagination"></div>
  </div>
</div>
<script>
const SCRUTIN_IDS = {scrutin_id_list};
const SCRUTIN_LABELS = {scrutin_label_list};
const VOTE_COLORS = {{pour:'#28a745',contre:'#dc3545',abstention:'#fd7e14',absent:'#aaa'}};
const PAGE_SIZE = 50;
let allData = [], filtered = [], sortCol = 5, sortDir = -1, page = 0;

function voteCell(v) {{
  if (!v) return '<span style="color:#ccc">-</span>';
  const c = VOTE_COLORS[v] || '#eee';
  return `<span class="badge" style="background:${{c}};color:${{v==='absent'?'#555':'white'}}">${{v}}</span>`;
}}

fetch('data/parlementaires.json').then(r=>r.json()).then(data => {{
  allData = data;
  // Populate dept and groupe filters
  const depts = [...new Set(data.map(p=>p.dept+' - '+p.nom_dept).filter(Boolean))].sort();
  const groupes = [...new Set(data.map(p=>p.groupe).filter(Boolean))].sort();
  const sel_d = document.getElementById('f-dept');
  depts.forEach(d => sel_d.add(new Option(d, d.split(' - ')[0])));
  const sel_g = document.getElementById('f-groupe');
  groupes.forEach(g => sel_g.add(new Option(g, g)));

  // Stats
  document.getElementById('stats-grid').innerHTML = `
    <div class="stat-card"><div class="stat-value">${{data.filter(p=>p.chambre==='AN').length}}</div><div class="stat-label">Députés</div></div>
    <div class="stat-card"><div class="stat-value">${{data.filter(p=>p.chambre==='SEN').length}}</div><div class="stat-label">Sénateurs</div></div>
    <div class="stat-card"><div class="stat-value">${{data.filter(p=>p.nb_sites>0).length}}</div><div class="stat-label">En zone FICT</div></div>
    <div class="stat-card"><div class="stat-value">${{data.filter(p=>p.commission_agri||p.commission_eco||p.mission_egalim).length}}</div><div class="stat-label">Actifs sur sujets agri</div></div>
  `;
  restoreFilters();
  renderTable();
}});

function filterData() {{
  const q = document.getElementById('search').value.toLowerCase();
  const fc = document.getElementById('f-chambre').value;
  const fd = document.getElementById('f-dept').value;
  const fg = document.getElementById('f-groupe').value;
  const fcom = document.getElementById('f-commission').value;
  const fs = document.getElementById('f-sites').value;
  return allData.filter(p =>
    (!q || p.nom.toLowerCase().includes(q) || (p.groupe||'').toLowerCase().includes(q) || (p.nom_dept||'').toLowerCase().includes(q)) &&
    (!fc || p.chambre === fc) &&
    (!fd || p.dept === fd) &&
    (!fg || p.groupe === fg) &&
    (!fcom || (fcom==='agri'&&p.commission_agri) || (fcom==='eco'&&p.commission_eco) || (fcom==='egalim'&&p.mission_egalim)) &&
    (!fs || p.nb_sites > 0)
  );
}}

function sortTable(col) {{
  if (sortCol === col) sortDir *= -1;
  else {{ sortCol = col; sortDir = col === 0 ? 1 : -1; }}
  page = 0;
  renderTable();
}}

function sortKey(p, col) {{
  switch(col) {{
    case 0: return p.nom;
    case 1: return p.chambre;
    case 2: return p.groupe;
    case 3: return p.dept;
    case 4: return p.nb_sites;
    case 5: return p.score;
    case 6: return p.score_engagement||0;
    case 7: return p.hemicycle_interventions||0;
    case 8: return p.propositions_ecrites||0;
    default: return (p.votes||{{}})[SCRUTIN_IDS[col-11]]||'';
  }}
}}

function renderTable() {{
  filtered = filterData();
  filtered.sort((a,b) => {{
    const ka=sortKey(a,sortCol), kb=sortKey(b,sortCol);
    return typeof ka==='number' ? (ka-kb)*sortDir : (ka<kb?-1:ka>kb?1:0)*sortDir;
  }});
  page = Math.min(page, Math.floor((filtered.length-1)/PAGE_SIZE));
  if (page < 0) page = 0;
  document.getElementById('result-count').textContent = `${{filtered.length}} résultats`;

  const slice = filtered.slice(page*PAGE_SIZE, (page+1)*PAGE_SIZE);
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = slice.map(p => {{
    const link = `<a href="fiche.html?id=${{encodeURIComponent(p.id)}}" style="color:#1a1a2e;text-decoration:none;font-weight:600">${{p.nom}}</a>`;
    const badges = [p.commission_agri?'<span class="badge badge-agri">Agri</span>':'', p.commission_eco?'<span class="badge badge-eco">Eco</span>':'', p.mission_egalim?'<span class="badge badge-egalim">EGALIM</span>':''].filter(Boolean).join(' ');
    const votesCells = SCRUTIN_IDS.map(id => `<td>${{voteCell((p.votes||{{}})[id])}}</td>`).join('');
    const scoreMax = 60;
    const scorePct = Math.min(100, Math.round((p.score / scoreMax) * 100));
    const scoreColor = p.score > 20 ? '#e85d04' : p.score > 5 ? '#1a1a2e' : '#555';
    const scoreStyle = `font-weight:${{p.score>5?'700':'400'}};color:${{scoreColor}};background:linear-gradient(to right,rgba(232,93,4,0.1) ${{scorePct}}%,transparent ${{scorePct}}%);font-feature-settings:"tnum"`;
    return `<tr>
      <td>${{link}}</td>
      <td><span class="badge ${{p.chambre==='AN'?'badge-an':'badge-sen'}}">${{p.chambre}}</span></td>
      <td style="font-size:12px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${{p.groupe}}</td>
      <td><span title="${{p.nom_dept}}">${{p.dept}}</span></td>
      <td style="text-align:center">${{p.nb_sites>0?`<b>${{p.nb_sites}}</b>`:0}}</td>
      <td style="${{scoreStyle}}">${{p.score.toFixed(1)}}</td>
      <td style="text-align:center">${{p.score_engagement>0?`<b style="color:#1a1a2e">${{p.score_engagement}}</b>`:'-'}}</td>
      <td style="text-align:center">${{p.hemicycle_interventions>0?p.hemicycle_interventions:'-'}}</td>
      <td style="text-align:center">${{p.propositions_ecrites>0?p.propositions_ecrites:'-'}}</td>
      <td style="font-size:11px;white-space:nowrap">${{p.position||''}}</td>
      <td>${{badges}}</td>
      ${{votesCells}}
    </tr>`;
  }}).join('');

  // Pagination
  const totalPages = Math.ceil(filtered.length/PAGE_SIZE);
  const pag = document.getElementById('pagination');
  let pagHtml = '';
  for (let i=0; i<totalPages; i++) {{
    if (i===0||i===totalPages-1||Math.abs(i-page)<=2) {{
      pagHtml+=`<button class="page-btn${{i===page?' active':''}}" onclick="goPage(${{i}})">${{i+1}}</button>`;
    }} else if (Math.abs(i-page)===3) {{
      pagHtml+='<span style="padding:5px">…</span>';
    }}
  }}
  pag.innerHTML = pagHtml;
  saveFilters();
}}

function goPage(p) {{ page=p; renderTable(); window.scrollTo(0,0); }}

const STORAGE_KEY='fict_parl_filters';
function saveFilters(){{
  const s={{}};
  document.querySelectorAll('.filter-select,.search-bar').forEach(el=>{{s[el.id]=el.value;}});
  s._page=page;s._sortCol=sortCol;s._sortDir=sortDir;
  sessionStorage.setItem(STORAGE_KEY,JSON.stringify(s));
}}
function restoreFilters(){{
  const raw=sessionStorage.getItem(STORAGE_KEY);
  if(!raw)return;
  try{{
    const s=JSON.parse(raw);
    Object.keys(s).forEach(k=>{{if(k.startsWith('_'))return;const el=document.getElementById(k);if(el)el.value=s[k];}});
    if(s._page!==undefined)page=s._page;
    if(s._sortCol!==undefined)sortCol=s._sortCol;
    if(s._sortDir!==undefined)sortDir=s._sortDir;
  }}catch(e){{}}
}}
</script>
</body>
</html>"""
    (SITE_DIR / 'parlementaires.html').write_text(html, encoding='utf-8')
    print('    ✅ parlementaires.html')


def write_fiche():
    scrutin_meta_json = json.dumps(SCRUTINS_META, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Fiche parlementaire</title>
<style>{BASE_CSS}
.fiche-header {{ background:#1a1a2e; color:white; padding:28px 32px; border-radius:12px; margin-bottom:20px; }}
.fiche-nom {{ font-size:26px; font-weight:700; margin-bottom:6px; }}
.fiche-meta {{ font-size:14px; opacity:.8; display:flex; gap:16px; flex-wrap:wrap; }}
.section-title {{ font-size:15px; font-weight:700; margin-bottom:12px; color:#1a1a2e; }}
.grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:16px; }}
.vote-row {{ display:flex; justify-content:space-between; align-items:center; padding:8px 12px; border-bottom:1px solid #f0f0f0; font-size:13px; }}
.vote-row:last-child {{ border-bottom:none; }}
.score-bar {{ background:#eee; border-radius:4px; height:8px; margin-top:4px; }}
.score-bar-fill {{ height:8px; border-radius:4px; background:#e85d04; }}
@media(max-width:768px) {{ .grid-2 {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
{write_nav('parlementaires.html')}
<div class="container" style="max-width:900px">
<a href="parlementaires.html" style="color:#666;font-size:13px;display:inline-block;margin-bottom:16px">← Retour à la liste</a>
<div id="content"><div class="empty-state card" style="padding:40px">Chargement...</div></div>
</div>
<script>
const SCRUTINS_META = {scrutin_meta_json};
const VOTE_COLORS = {{pour:'#28a745',contre:'#dc3545',abstention:'#fd7e14',absent:'#bbb'}};
const VOTE_ICONS = {{pour:'✅',contre:'❌',abstention:'🟡',absent:'⬜'}};

function voteRow(label, v, loi) {{
  const c = VOTE_COLORS[v] || '#eee';
  const icon = VOTE_ICONS[v] || '-';
  return `<div class="vote-row">
    <div>
      <div style="font-weight:600">${{label}}</div>
      ${{loi?`<div style="font-size:11px;color:#888">Loi ${{loi}}</div>`:''}}
    </div>
    <span style="background:${{c}};color:${{v==='absent'||!v?'#555':'white'}};padding:4px 12px;border-radius:5px;font-size:12px;font-weight:600">${{icon}} ${{v||'-'}}</span>
  </div>`;
}}

const params = new URLSearchParams(window.location.search);
const id = params.get('id');
if (!id) {{ document.getElementById('content').innerHTML='<div class="card" style="padding:24px">ID manquant dans l\\'URL</div>'; }}

fetch('data/parlementaires.json').then(r=>r.json()).then(data => {{
  const p = data.find(d => d.id === id || d.nom.toLowerCase().replace(/\\s+/g,'-') === id);
  if (!p) {{
    document.getElementById('content').innerHTML = '<div class="card" style="padding:24px">Parlementaire non trouvé.</div>';
    return;
  }}
  document.title = `FICT - ${{p.nom}}`;
  const chambreColor = p.chambre === 'AN' ? '#e85d04' : '#4361ee';
  const posColor = p.position&&p.position.includes('pro') ? '#28a745' : p.position&&p.position.includes('réservé') ? '#dc3545' : '#555';

  const badgesHtml = [
    p.commission_agri ? '<span class="badge badge-agri">🌾 Commission Agriculture</span>' : '',
    p.commission_eco  ? '<span class="badge badge-eco">🏦 Commission Économique</span>' : '',
    p.mission_egalim  ? '<span class="badge badge-egalim">⚖️ Mission / Groupe suivi EGALIM</span>' : '',
  ].filter(Boolean).join(' ');

  const votesHtml = p.chambre === 'AN' ?
    SCRUTINS_META.map(s => voteRow(s.label, (p.votes||{{}})[s.id], s.loi)).join('') :
    '<div style="padding:16px;color:#888;font-size:13px">Les votes nominatifs sont disponibles uniquement pour les députés (AN). Les sénateurs votent selon des procédures différentes.</div>';

  const scoreMax = 50;
  const scoreWidth = Math.min(100, (p.score / scoreMax) * 100);
  const entreprisesList = p.entreprises ? p.entreprises.split(';').filter(Boolean).map(e=>`<div style="font-size:12px;padding:3px 0;border-bottom:1px solid #f5f5f5">${{e.trim()}}</div>`).join('') : '<span style="color:#999;font-size:12px">Aucun site FICT dans la zone</span>';

  document.getElementById('content').innerHTML = `
    <div class="fiche-header">
      <div class="fiche-nom">${{p.nom}}</div>
      <div class="fiche-meta">
        <span style="background:${{chambreColor}};padding:3px 10px;border-radius:5px;font-size:13px;font-weight:600">${{p.chambre === 'AN' ? '🏛️ Assemblée Nationale' : '🏦 Sénat'}}</span>
        <span>🏷️ ${{p.groupe}}</span>
        <span>📍 Dept. ${{p.dept}} - ${{p.nom_dept}}</span>
        ${{p.circo ? `<span>Circonscription ${{p.circo}}</span>` : ''}}
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="section-title">📊 Scores FICT</div>
        <div style="font-size:13px;color:#666;margin-bottom:4px">Score global (implantation × implication)</div>
        <div style="font-size:32px;font-weight:700;color:#e85d04">${{p.score.toFixed(1)}}</div>
        <div class="score-bar"><div class="score-bar-fill" style="width:${{scoreWidth}}%"></div></div>
        <div style="margin-top:12px;display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px">
          <div style="text-align:center;background:#f8f9fa;border-radius:6px;padding:8px">
            <div style="font-size:18px;font-weight:700">${{p.score_eco.toFixed(1)}}</div>
            <div style="font-size:10px;color:#888">Implantation</div>
          </div>
          <div style="text-align:center;background:#f8f9fa;border-radius:6px;padding:8px">
            <div style="font-size:18px;font-weight:700">${{p.score_impl.toFixed(1)}}</div>
            <div style="font-size:10px;color:#888">Implication</div>
          </div>
          <div style="text-align:center;background:#f8f9fa;border-radius:6px;padding:8px">
            <div style="font-size:18px;font-weight:700;color:${{p.score_engagement>0?'#1a1a2e':'#ccc'}}">${{p.score_engagement}}</div>
            <div style="font-size:10px;color:#888">Engagement</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="section-title">🎭 Engagement parlementaire</div>
        ${{badgesHtml || '<span style="color:#999;font-size:13px">Pas de commission agriculture identifiée</span>'}}
        ${{p.position && p.chambre==='AN' ? `<div style="margin-top:10px;font-size:13px;font-weight:600;color:${{posColor}}">↗ Position : ${{p.position}}</div>` : ''}}
        ${{p.commission ? `<div style="font-size:12px;color:#888;margin-top:8px">Commission : ${{p.commission}}</div>` : ''}}
        ${{p.mail ? `<div style="margin-top:12px"><a href="mailto:${{p.mail}}" style="color:#4361ee;font-size:13px">✉️ ${{p.mail}}</a></div>` : ''}}
        ${{p.twitter ? `<div style="margin-top:4px"><a href="https://twitter.com/${{p.twitter.replace('@','')}}" target="_blank" style="color:#1d9bf0;font-size:13px">🐦 @${{p.twitter.replace('@','')}}</a></div>` : ''}}
      </div>
    </div>

    ${{p.chambre === 'AN' ? `
    ${{p.interventions_nitrites > 0 ? `<div style="background:rgba(232,93,4,.08);border:1px solid rgba(232,93,4,.25);border-radius:10px;padding:14px 18px;margin-bottom:16px;display:flex;align-items:center;gap:16px">
      <div style="font-size:32px;font-weight:800;color:#e85d04;min-width:48px;text-align:center">${{p.interventions_nitrites}}</div>
      <div>
        <div style="font-weight:700;color:#1a1a2e;font-size:14px">intervention${{p.interventions_nitrites>1?'s':''}} parlementaire${{p.interventions_nitrites>1?'s':''}} sur <em>nitrites / charcuterie</em></div>
        <div style="font-size:12px;color:#888;margin-top:2px">Source : Pappers Politique - amendements, PPL, rapports, questions au gouvernement</div>
      </div>
    </div>` : ''}}
    <div class="card" style="margin-bottom:16px">
      <div class="section-title">📢 Activité parlementaire (17e législature)</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-top:8px">
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.hemicycle_interventions||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Interventions hémicycle</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.questions_orales||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Questions orales</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.questions_ecrites||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Questions écrites</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.propositions_ecrites||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">PPL déposées</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.propositions_signees||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">PPL co-signées</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.nb_amendements_deposes||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Amdt agroalim.</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.nb_amendements_cosignes||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Amdt co-signés</div>
        </div>
        <div style="text-align:center;background:#f8f9fa;border-radius:8px;padding:12px">
          <div style="font-size:24px;font-weight:700;color:#1a1a2e">${{p.semaines_presence||'-'}}</div>
          <div style="font-size:11px;color:#888;margin-top:3px">Semaines présence</div>
        </div>
      </div>
    </div>` : ''}}

    <div class="grid-2">
      <div class="card">
        <div class="section-title">🗳️ Votes nominatifs</div>
        ${{votesHtml}}
      </div>

      <div class="card">
        <div class="section-title">🏭 Sites FICT dans la zone (${{p.nb_sites}} site(s))</div>
        ${{entreprisesList}}
      </div>
    </div>
  `;
}});
</script>
</body>
</html>"""
    (SITE_DIR / 'fiche.html').write_text(html, encoding='utf-8')
    print('    ✅ fiche.html')


def write_partis():
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Analyse par parti</title>
<style>{BASE_CSS}
.parti-card {{ background:white; border-radius:10px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:12px; display:flex; align-items:center; gap:16px; }}
.parti-bar-bg {{ flex:1; background:#eee; border-radius:4px; height:8px; }}
.parti-bar-fill {{ height:8px; border-radius:4px; }}
.parti-name {{ font-weight:700; font-size:14px; min-width:200px; }}
.parti-stats {{ font-size:12px; color:#666; margin-top:3px; }}
</style>
</head>
<body>
{write_nav('partis.html')}
<div class="container">
  <div class="page-title">🏛️ Analyse par parti politique</div>
  <div class="page-subtitle">Classement par exposition aux zones de production FICT</div>
  <div class="filter-row">
    <select class="filter-select" id="f-chambre" onchange="renderPartis()"><option value="">AN + Sénat</option><option value="AN">Assemblée Nationale</option><option value="SEN">Sénat</option></select>
    <select class="filter-select" id="f-sort" onchange="renderPartis()">
      <option value="total_sites">Total sites en zone</option>
      <option value="pct_zone">% élus en zone FICT</option>
      <option value="score_moyen">Score FICT moyen</option>
      <option value="nb_elus">Nombre d'élus</option>
    </select>
  </div>
  <div id="partis-content"></div>
</div>
<script>
let partisData = [];
fetch('data/partis.json').then(r=>r.json()).then(data => {{
  partisData = data;
  renderPartis();
}});

function renderPartis() {{
  const fc = document.getElementById('f-chambre').value;
  const fs = document.getElementById('f-sort').value;
  let data = fc ? partisData.filter(p=>p.chambre===fc) : partisData;
  data = [...data].sort((a,b) => b[fs] - a[fs]);
  const maxSites = Math.max(...data.map(p=>p.total_sites)) || 1;

  document.getElementById('partis-content').innerHTML = data.map(p => {{
    const pct = Math.round(p.pct_zone);
    const barW = Math.round((p.total_sites/maxSites)*100);
    const chambreLabel = p.chambre === 'AN' ? '<span class="badge badge-an">AN</span>' : '<span class="badge badge-sen">Sénat</span>';
    return `<div class="parti-card">
      <div style="width:14px;height:44px;border-radius:3px;background:${{p.color}};flex-shrink:0"></div>
      <div style="flex:1">
        <div class="parti-name">${{chambreLabel}} ${{p.groupe}}</div>
        <div class="parti-stats">${{p.nb_elus}} élu(s) · ${{p.nb_elus_zone}} en zone FICT (${{pct}}%) · Score moy. ${{p.score_moyen.toFixed(1)}}</div>
        <div style="margin-top:6px;display:flex;align-items:center;gap:8px">
          <div class="parti-bar-bg"><div class="parti-bar-fill" style="width:${{barW}}%;background:${{p.color}}"></div></div>
          <span style="font-size:13px;font-weight:700;min-width:30px">${{p.total_sites}}</span>
          <span style="font-size:11px;color:#888">sites</span>
        </div>
      </div>
    </div>`;
  }}).join('');
}}
</script>
</body>
</html>"""
    (SITE_DIR / 'partis.html').write_text(html, encoding='utf-8')
    print('    ✅ partis.html')


def write_groupes():
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Groupes industriels</title>
<style>{BASE_CSS}
@media(max-width:768px) {{ table th:nth-child(2), table td:nth-child(2), table th:nth-child(3), table td:nth-child(3) {{ display:none; }} }}
tbody tr {{ cursor: pointer; }}
.detail-row td {{ background: #f8f9fa; padding: 16px 20px !important; border-left: 4px solid #e85d04; cursor: default; }}
.detail-content {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; font-size: 12px; }}
@media(max-width:768px) {{ .detail-content {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
{write_nav('groupes.html')}
<div class="container">
  <div class="page-title">🏭 Groupes industriels</div>
  <div class="page-subtitle">Implantation multi-sites des membres FICT (classés par nombre de départements couverts)</div>
  <div class="card">
    <label for="search" class="sr-only">Rechercher un groupe industriel</label>
    <input type="text" class="search-bar" id="search" placeholder="🔍 Rechercher un groupe..." oninput="renderGroupes()">
    <div style="overflow-x:auto">
    <table>
      <thead><tr>
        <th onclick="sortTable(0)">Groupe ↕</th>
        <th onclick="sortTable(1)">SIREN</th>
        <th onclick="sortTable(2)">Catégorie</th>
        <th onclick="sortTable(3)">Sites ↕</th>
        <th onclick="sortTable(4)">Depts ↕</th>
        <th>Départements couverts</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
  </div>
</div>
<script>
let allData = [], allSites = [], allParls = [], sortCol = 4, sortDir = -1;

Promise.all([
  fetch('data/groupes.json').then(r=>r.json()),
  fetch('data/sites.json').then(r=>r.json()),
  fetch('data/parlementaires.json').then(r=>r.json())
]).then(([groupes, sites, parls]) => {{
  allData = groupes;
  allSites = sites;
  allParls = parls;
  renderGroupes();
}});

function renderGroupes() {{
  const q = document.getElementById('search').value.toLowerCase();
  let data = q ? allData.filter(g=>g.nom.toLowerCase().includes(q)) : allData;
  data = [...data].sort((a,b) => {{
    const ka = [a.nom, a.siren, a.categorie, a.nb_sites, a.nb_depts][sortCol];
    const kb = [b.nom, b.siren, b.categorie, b.nb_sites, b.nb_depts][sortCol];
    return typeof ka === 'number' ? (ka-kb)*sortDir : (ka<kb?-1:ka>kb?1:0)*sortDir;
  }});
  document.getElementById('tbody').innerHTML = data.map(g => {{
    const depts = g.depts.split(',').map(d=>d.trim()).filter(Boolean);
    const deptsHtml = depts.map(d=>`<span style="background:#f0f0f0;border-radius:3px;padding:1px 5px;font-size:11px;margin:1px">${{d}}</span>`).join('');
    const multiStyle = g.nb_depts >= 5 ? 'font-weight:700;color:#e85d04' : g.nb_depts >= 3 ? 'font-weight:600' : '';
    return `<tr onclick="toggleDetail(this,'${{g.siren}}')">
      <td><b>${{g.nom}}</b></td>
      <td style="font-size:11px;color:#888">${{g.siren}}</td>
      <td style="font-size:12px">${{g.categorie||'-'}}</td>
      <td style="text-align:center">${{g.nb_sites}}</td>
      <td style="text-align:center;${{multiStyle}}">${{g.nb_depts}}</td>
      <td>${{deptsHtml}}</td>
    </tr>`;
  }}).join('');
}}

function sortTable(col) {{
  if (sortCol===col) sortDir*=-1; else {{sortCol=col;sortDir=col>=3?-1:1;}}
  renderGroupes();
}}

function toggleDetail(row, siren) {{
  const next = row.nextElementSibling;
  if (next && next.classList.contains('detail-row')) {{ next.remove(); return; }}
  document.querySelectorAll('.detail-row').forEach(r=>r.remove());
  const grpSites = allSites.filter(s=>s.siren===siren);
  const depts = [...new Set(grpSites.map(s=>s.dept).filter(Boolean))];
  const grpParls = allParls.filter(p=>depts.includes(p.dept)).sort((a,b)=>b.score-a.score).slice(0,5);
  const tr = document.createElement('tr');
  tr.className = 'detail-row';
  tr.innerHTML = `<td colspan="6"><div class="detail-content">
    <div><strong>Sites (${{grpSites.length}})</strong><br>${{grpSites.length ? grpSites.map(s=>`${{s.commune||''}} (${{s.dept}})`).join(', ') : 'Aucun site trouve'}}</div>
    <div><strong>Elus cles</strong><br>${{grpParls.length ? grpParls.map(p=>`<a href="fiche.html?id=${{encodeURIComponent(p.id)}}" style="color:#4361ee;text-decoration:none">${{p.nom}}</a> <span style="color:#888">(${{p.score.toFixed(1)}})</span>`).join(', ') : 'Aucun elu dans ces departements'}}</div>
  </div></td>`;
  row.after(tr);
}}
</script>
</body>
</html>"""
    (SITE_DIR / 'groupes.html').write_text(html, encoding='utf-8')
    print('    ✅ groupes.html')


def write_entreprises():
    nav = write_nav('entreprises.html')
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{NOINDEX}
<title>Entreprises FICT - Projet JV</title>
<style>{BASE_CSS}
.ca-bar {{ height: 6px; background: #e9ecef; border-radius: 3px; margin-top: 4px; }}
.ca-fill {{ height: 100%; background: #1a1a2e; border-radius: 3px; }}
@media(max-width:768px) {{ table th:nth-child(n+5), table td:nth-child(n+5) {{ display:none; }} }}
</style>
</head>
<body>
{nav}
<div class="container">
<h1 class="page-title">Entreprises adhérentes FICT</h1>
<p class="page-subtitle">Données INPI + INSEE - dirigeants et chiffres d'affaires enrichis</p>
<div class="stats-grid" id="stats"></div>
<div class="card">
<label for="search" class="sr-only">Rechercher une entreprise</label>
<input class="search-bar" id="search" placeholder="Rechercher une entreprise, un dirigeant..." oninput="render()">
<div class="filter-row">
  <label for="fSyndicat" class="sr-only">Filtrer par syndicat</label>
  <select class="filter-select" id="fSyndicat" onchange="render()"><option value="">Tous les syndicats</option></select>
  <label for="fNaf" class="sr-only">Filtrer par code NAF</label>
  <select class="filter-select" id="fNaf" onchange="render()"><option value="">Tous les codes NAF</option></select>
  <label for="fCa" class="sr-only">Filtrer par chiffre d'affaires</label>
  <select class="filter-select" id="fCa" onchange="render()">
    <option value="">Tous les CA</option>
    <option value="100">CA &gt; 100M€</option>
    <option value="50">CA &gt; 50M€</option>
    <option value="10">CA &gt; 10M€</option>
    <option value="1">CA disponible</option>
  </select>
</div>
<div id="count" style="font-size:13px;color:#888;margin-bottom:12px;"></div>
<div style="overflow-x:auto"><table><thead><tr>
  <th onclick="sortBy('nom_fict')">Entreprise</th>
  <th onclick="sortBy('syndicat')">Syndicat</th>
  <th onclick="sortBy('nb_sites')">Sites</th>
  <th onclick="sortBy('ca')">CA (M€)</th>
  <th>Forme</th>
  <th>Dirigeants</th>
  <th>Création</th>
</tr></thead><tbody id="tbody"></tbody></table></div>
<div class="pagination" id="pagination"></div>
</div>
</div>
<script>
const NAF_LABELS = {{'10.13A':'Prépa viande','10.13B':'Charcuterie','10.11Z':'Abattage','10.12Z':'Volaille'}};
let data = [], filtered = [], sortCol = 'ca', sortDir = -1, page = 1;
const PAGE = 50;
fetch('data/entreprises.json').then(r=>r.json()).then(d=>{{
  data = d;
  const syndicats = [...new Set(d.map(e=>e.syndicat).filter(Boolean))].sort();
  const nafs = [...new Set(d.map(e=>e.naf).filter(Boolean))].sort();
  syndicats.forEach(s=>{{const o=document.createElement('option');o.value=s;o.textContent=s;document.getElementById('fSyndicat').appendChild(o);}});
  nafs.forEach(n=>{{const o=document.createElement('option');o.value=n;o.textContent=NAF_LABELS[n]||n;document.getElementById('fNaf').appendChild(o);}});
  const avecCa = d.filter(e=>e.ca).length;
  const totalCa = d.filter(e=>e.ca).reduce((a,e)=>a+(e.ca||0),0);
  const avecDir = d.filter(e=>e.dirigeants).length;
  document.getElementById('stats').innerHTML = `
    <div class="stat-card"><div class="stat-value">${{d.length}}</div><div class="stat-label">Entreprises enrichies</div></div>
    <div class="stat-card"><div class="stat-value">${{avecCa}}</div><div class="stat-label">Avec CA disponible</div></div>
    <div class="stat-card"><div class="stat-value">${{(totalCa/1e9).toFixed(1)}}Md€</div><div class="stat-label">CA total agrégé</div></div>
    <div class="stat-card"><div class="stat-value">${{avecDir}}</div><div class="stat-label">Avec dirigeants</div></div>
  `;
  restoreFilters();
  render();
}});

const STORAGE_KEY='fict_ent_filters';
function saveFilters(){{const s={{}};document.querySelectorAll('.filter-select,.search-bar').forEach(el=>{{s[el.id]=el.value;}});s._sortCol=sortCol;s._sortDir=sortDir;sessionStorage.setItem(STORAGE_KEY,JSON.stringify(s));}}
function restoreFilters(){{const raw=sessionStorage.getItem(STORAGE_KEY);if(!raw)return;try{{const s=JSON.parse(raw);Object.keys(s).forEach(k=>{{if(k.startsWith('_'))return;const el=document.getElementById(k);if(el)el.value=s[k];}});if(s._sortCol!==undefined)sortCol=s._sortCol;if(s._sortDir!==undefined)sortDir=s._sortDir;}}catch(e){{}}}}

function render(){{
  const q = document.getElementById('search').value.toLowerCase();
  const syn = document.getElementById('fSyndicat').value;
  const naf = document.getElementById('fNaf').value;
  const caMin = parseFloat(document.getElementById('fCa').value)||0;
  filtered = data.filter(e=>{{
    if(q && !JSON.stringify(e).toLowerCase().includes(q)) return false;
    if(syn && e.syndicat !== syn) return false;
    if(naf && e.naf !== naf) return false;
    if(caMin===1 && !e.ca) return false;
    if(caMin>1 && (e.ca||0) < caMin*1e6) return false;
    return true;
  }});
  filtered.sort((a,b)=>{{
    const va=a[sortCol]??-1, vb=b[sortCol]??-1;
    return sortDir*(va>vb?1:va<vb?-1:0);
  }});
  page=1; paginate(); saveFilters();
}}
function sortBy(col){{sortCol===col?sortDir*=-1:(sortCol=col,sortDir=-1);render();}}
function paginate(){{
  const total=filtered.length, pages=Math.ceil(total/PAGE)||1;
  document.getElementById('count').textContent=`${{total}} entreprise${{total>1?'s':''}}`;
  const slice=filtered.slice((page-1)*PAGE, page*PAGE);
  const maxCa = Math.max(...data.map(e=>e.ca||0));
  document.getElementById('tbody').innerHTML = slice.map(e=>{{
    const ca = e.ca ? (e.ca/1e6).toFixed(1)+'M€' : '-';
    const pct = e.ca ? Math.round(e.ca/maxCa*100) : 0;
    const dirs = e.dirigeants ? e.dirigeants.split(' | ').map(d=>`<div style="font-size:11px;color:#555">${{d}}</div>`).join('') : '-';
    return `<tr>
      <td><strong>${{e.nom_fict}}</strong><div style="font-size:11px;color:#888">${{e.denomination||''}}</div></td>
      <td style="font-size:12px">${{e.syndicat||'-'}}</td>
      <td style="text-align:center">${{e.nb_sites}}</td>
      <td><div>${{ca}}</div><div class="ca-bar"><div class="ca-fill" style="width:${{pct}}%"></div></div></td>
      <td style="font-size:11px">${{e.forme_juridique||'-'}}</td>
      <td>${{dirs}}</td>
      <td style="font-size:12px">${{e.date_creation?(e.date_creation.slice(0,4)||'-'):'-'}}</td>
    </tr>`;
  }}).join('');
  const pag=document.getElementById('pagination');
  pag.innerHTML='';
  for(let i=1;i<=pages;i++){{
    const b=document.createElement('button');
    b.className='page-btn'+(i===page?' active':'');
    b.textContent=i; b.onclick=()=>{{page=i;paginate();}};
    pag.appendChild(b);
  }}
}}
</script>
</body></html>"""
    (SITE_DIR / 'entreprises.html').write_text(html, encoding='utf-8')
    print('    ✅ entreprises.html')


def write_accueil(parl_json, sites_json, partis_json):
    nb_parls = len(parl_json)
    nb_an = sum(1 for p in parl_json if p['chambre'] == 'AN')
    nb_sen = sum(1 for p in parl_json if p['chambre'] == 'SEN')
    nb_sites = len(sites_json)
    nb_zone = sum(1 for p in parl_json if p['nb_sites'] > 0)
    nb_partis = len({p['groupe'] for p in parl_json})
    top10 = sorted(parl_json, key=lambda p: -p['score'])[:10]
    top10_html = ''.join(
        f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0f0">'
        f'<span style="width:22px;height:22px;border-radius:50%;background:#e85d04;color:white;'
        f'font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0">{i+1}</span>'
        f'<div style="flex:1;min-width:0">'
        f'<div style="font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{p["nom"]}</div>'
        f'<div style="font-size:11px;color:#888">{p["chambre"]} · {p["dept"]} {p["nom_dept"]}</div>'
        f'</div>'
        f'<span style="background:#1a1a2e;color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;flex-shrink:0">{p["score"]:.1f}</span>'
        f'</div>'
        for i, p in enumerate(top10)
    )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Veille parlementaire</title>
<style>{BASE_CSS}
.hero {{ background: #1a1a2e; background-image: radial-gradient(rgba(255,255,255,.06) 1px, transparent 1px); background-size: 24px 24px; color: white; padding: 56px 20px; text-align: center; }}
.hero-title {{ font-size: clamp(24px, 4vw, 42px); font-weight: 800; line-height: 1.2; margin-bottom: 16px; }}
.hero-subtitle {{ font-size: 16px; opacity: .75; max-width: 620px; margin: 0 auto 32px; line-height: 1.6; }}
.hero-cta {{ display: inline-flex; gap: 12px; flex-wrap: wrap; justify-content: center; }}
.btn-primary {{ background: #e85d04; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; transition: all .2s; }}
.btn-primary:hover {{ background: #c94e00; }}
.btn-secondary {{ background: rgba(255,255,255,.15); color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px; border: 1px solid rgba(255,255,255,.3); transition: all .2s; }}
.btn-secondary:hover {{ background: rgba(255,255,255,.25); }}
.section-cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }}
.section-cards-secondary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }}
.main-grid {{ margin-bottom: 32px; }}
@media(max-width:900px) {{ .section-cards {{ grid-template-columns: 1fr; }} }}
.feature-card {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); text-decoration: none; color: inherit; transition: all .2s; border-top: 4px solid #e85d04; }}
.feature-card.secondary {{ border-top-color: #ddd; padding: 18px; }}
.feature-card.secondary .feature-icon {{ font-size: 22px; margin-bottom: 6px; }}
.feature-card.secondary .feature-title {{ font-size: 14px; }}
.feature-card.secondary .feature-desc {{ font-size: 12px; }}
.feature-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.12); }}
.feature-icon {{ font-size: 28px; margin-bottom: 10px; }}
.feature-title {{ font-size: 16px; font-weight: 700; margin-bottom: 6px; }}
.feature-desc {{ font-size: 13px; color: #666; line-height: 1.5; }}
.credit-card {{ background: #1a1a2e; color: white; border-radius: 12px; padding: 24px 28px; display: flex; align-items: center; gap: 20px; margin-bottom: 32px; flex-wrap: wrap; }}
.credit-text {{ flex: 1; min-width: 200px; }}
.credit-name {{ font-size: 18px; font-weight: 700; margin-bottom: 4px; }}
.credit-desc {{ font-size: 13px; opacity: .75; line-height: 1.5; }}
.credit-link {{ background: #0a66c2; color: white; padding: 8px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 13px; white-space: nowrap; transition: all .2s; }}
.credit-link:hover {{ background: #0857a6; }}
</style>
</head>
<body>
{write_nav('accueil.html')}

<div class="hero">
  <div style="max-width:800px;margin:0 auto">
    <div style="display:inline-block;background:rgba(232,93,4,.2);color:#e85d04;border:1px solid rgba(232,93,4,.4);padding:4px 16px;border-radius:20px;font-size:12px;font-weight:600;margin-bottom:18px;letter-spacing:.6px">OUTIL EXCLUSIF · DONNÉES AVRIL 2026</div>
    <div class="hero-title">Veille <span style="color:#e85d04">parlementaire</span><br>Charcuterie &amp; Filière viande</div>
    <div class="hero-subtitle">
      Identifiez les élus clés de la filière viande : implantation industrielle, votes EGALIM, commissions agricoles.
    </div>
    <div class="hero-cta">
      <a href="index.html" class="btn-primary">🗺️ Explorer la carte</a>
      <a href="parlementaires.html" class="btn-secondary">👥 Voir tous les élus</a>
    </div>
  </div>
</div>

<div class="container">
  <div class="stats-grid" style="margin-top:32px;grid-template-columns:repeat(3,1fr)">
    <div class="stat-card"><div class="stat-value">{nb_parls}</div><div class="stat-label">Parlementaires analysés</div></div>
    <div class="stat-card"><div class="stat-value">{nb_sites}</div><div class="stat-label">Sites de production FICT</div></div>
    <div class="stat-card"><div class="stat-value">7</div><div class="stat-label">Votes suivis (EGALIM...)</div></div>
  </div>

  <div class="section-cards">
    <a href="index.html" class="feature-card">
      <div class="feature-icon">🗺️</div>
      <div class="feature-title">Carte interactive</div>
      <div class="feature-desc">Choroplèthe départementale par intensité industrielle. Cliquez sur un département pour voir les parlementaires et leurs scores.</div>
    </a>
    <a href="parlementaires.html" class="feature-card">
      <div class="feature-icon">👥</div>
      <div class="feature-title">Parlementaires</div>
      <div class="feature-desc">{nb_parls} élus classés par score FICT. Filtres par chambre, groupe, département et commission.</div>
    </a>
    <a href="europe.html" class="feature-card">
      <div class="feature-icon">🇪🇺</div>
      <div class="feature-title">Eurodéputés</div>
      <div class="feature-desc">73 eurodéputés français : posture sur Farm to Fork, additifs et nitrites.</div>
    </a>
  </div>
  <div class="section-cards-secondary">
    <a href="partis.html" class="feature-card secondary">
      <div class="feature-icon">🏛️</div>
      <div class="feature-title">Partis</div>
      <div class="feature-desc">Exposition par groupe politique aux zones FICT.</div>
    </a>
    <a href="groupes.html" class="feature-card secondary">
      <div class="feature-icon">🏭</div>
      <div class="feature-title">Industriels</div>
      <div class="feature-desc">152 groupes multi-sites : Bigard, Herta, Fleury Michon...</div>
    </a>
    <a href="entreprises.html" class="feature-card secondary">
      <div class="feature-icon">🏢</div>
      <div class="feature-title">Entreprises</div>
      <div class="feature-desc">CA, effectifs, dirigeants enrichis via INPI + INSEE.</div>
    </a>
  </div>
  <div style="text-align:center;margin-bottom:24px">
    <a href="methodologie.html" style="font-size:13px;color:#666;text-decoration:none">📖 Voir la méthodologie et les sources →</a>
  </div>

  <div class="main-grid">
    <div class="card">
      <div style="font-size:15px;font-weight:700;margin-bottom:12px;color:#1a1a2e">🏆 Top 10 score FICT</div>
      {top10_html}
      <div style="margin-top:12px;text-align:right">
        <a href="parlementaires.html" style="font-size:12px;color:#e85d04;text-decoration:none;font-weight:600">Voir les {nb_parls} élus →</a>
      </div>
    </div>
  </div>

  <div class="credit-card">
    <div style="font-size:40px">💼</div>
    <div class="credit-text">
      <div class="credit-name">Réalisé par Julien Vieira</div>
      <div class="credit-desc">Consultant en affaires publiques · Veille réglementaire FICT (nitrites, PPWR, EGALIM)<br>Données mises à jour en avril 2026</div>
    </div>
    <a href="https://www.linkedin.com/in/julien-vieira-b59673b4/" target="_blank" rel="noopener" class="credit-link">
      🔗 LinkedIn
    </a>
  </div>

</div>

<footer style="background:#1a1a2e;color:rgba(255,255,255,.6);text-align:center;padding:20px;font-size:12px">
  Données : Assemblée Nationale · Sénat · SIRENE (INSEE) · nosdéputés.fr (Regards Citoyens) · Pappers · INPI<br>
  Site à usage interne - <a href="methodologie.html" style="color:rgba(255,255,255,.8)">Voir la méthodologie</a>
</footer>
</body>
</html>"""
    (SITE_DIR / 'accueil.html').write_text(html, encoding='utf-8')
    print('    ✅ accueil.html')


def write_europe():
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Eurodéputés français V2</title>
<style>{BASE_CSS}
.v2-banner {{ background: linear-gradient(135deg,#1a1a2e,#2d2d5e); color:white; border-radius:12px; padding:20px 24px; margin-bottom:20px; display:flex; gap:20px; align-items:center; flex-wrap:wrap; }}
.v2-badge {{ background:rgba(232,93,4,.25); border:1px solid rgba(232,93,4,.5); color:#ff9a5c; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; letter-spacing:.5px; white-space:nowrap; }}
.v2-title {{ font-size:22px; font-weight:800; margin:8px 0 4px; }}
.v2-sub {{ font-size:13px; opacity:.7; }}
.posture-ally    {{ background:#198754; color:white; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; display:inline-block; }}
.posture-watch   {{ background:#fd7e14; color:white; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; display:inline-block; }}
.posture-against {{ background:#dc3545; color:white; font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px; white-space:nowrap; display:inline-block; }}
.legend-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:10px; margin-bottom:20px; }}
.legend-card {{ border-radius:10px; padding:14px 16px; }}
.legend-card.ally    {{ background:#d1fae5; border-left:4px solid #198754; }}
.legend-card.watch   {{ background:#fff3cd; border-left:4px solid #fd7e14; }}
.legend-card.against {{ background:#fee2e2; border-left:4px solid #dc3545; }}
.legend-title {{ font-size:13px; font-weight:700; margin-bottom:4px; }}
.legend-desc  {{ font-size:11.5px; color:#555; line-height:1.5; }}
.legend-groups {{ font-size:10.5px; color:#777; margin-top:6px; font-style:italic; }}
tr.row-ally    {{ background:rgba(25,135,84,.04); }}
tr.row-against {{ background:rgba(220,53,69,.04); }}
@media(max-width:768px) {{ #meps-table th:nth-child(n+4):nth-child(-n+6), #meps-table td:nth-child(n+4):nth-child(-n+6) {{ display:none; }} }}
</style>
</head>
<body>
{write_nav('europe.html')}
<div class="container">

<div class="v2-banner">
  <div>
    <div class="v2-badge">APERÇU V2 - DONNÉES AVRIL 2026</div>
    <div class="v2-title">🇪🇺 Eurodéputés français · Réglementation alimentaire</div>
    <div class="v2-sub">73 eurodéputés français au Parlement Européen · Activité sur Farm to Fork, additifs et nitrites</div>
  </div>
</div>

<div class="stats-grid" style="grid-template-columns:repeat(auto-fit,minmax(150px,1fr));margin-bottom:20px">
  <div class="stat-card"><div class="stat-value" id="n-total">-</div><div class="stat-label">eurodéputés FR analysés</div></div>
  <div class="stat-card" style="border-top:3px solid #198754"><div class="stat-value" style="color:#198754" id="n-ally">-</div><div class="stat-label">🟢 favorables à nos positions</div></div>
  <div class="stat-card" style="border-top:3px solid #fd7e14"><div class="stat-value" style="color:#fd7e14" id="n-watch">-</div><div class="stat-label">🟡 neutres</div></div>
  <div class="stat-card" style="border-top:3px solid #dc3545"><div class="stat-value" style="color:#dc3545" id="n-against">-</div><div class="stat-label">🔴 défavorables à nos positions</div></div>
</div>

<div class="legend-grid">
  <div class="legend-card ally">
    <div class="legend-title">🟢 Favorables à nos positions</div>
    <div class="legend-desc">Groupes historiquement <strong>opposés à la surréglementation alimentaire</strong>. Ont voté contre la résolution Farm to Fork (2021). Potentiellement réceptifs aux arguments FICT sur les nitrites.</div>
    <div class="legend-groups">EPP · ECR · Patriotes pour l'Europe · ESN</div>
  </div>
  <div class="legend-card watch">
    <div class="legend-title">🟡 Neutres au cas par cas</div>
    <div class="legend-desc">Groupes aux positions <strong>divisées ou pragmatiques</strong> sur la réglementation alimentaire. Certains membres sont sensibles aux arguments économiques (emploi, filière).</div>
    <div class="legend-groups">Renew Europe · Non inscrits</div>
  </div>
  <div class="legend-card against">
    <div class="legend-title">🔴 Défavorables à nos positions</div>
    <div class="legend-desc">Groupes <strong>favorables à la restriction des additifs</strong> et à la stratégie Farm to Fork. Ont voté pour des réglementations plus strictes. Mobilisation difficile sauf cas exceptionnel.</div>
    <div class="legend-groups">Verts/ALE · S&D · Gauche GUE/NGL</div>
  </div>
</div>

<div class="card">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">
    <div style="font-size:15px;font-weight:700;color:#1a1a2e">Eurodéputés français · Activité sur agenda alimentaire</div>
    <div style="font-size:11px;color:#888">Score = Farm to Fork×3 + nitrites×3 + additifs×2 + EGAlim×1 · Proxy groupe politique pour la posture</div>
  </div>
  <label for="search-eu" class="sr-only">Rechercher un eurodéputé</label>
  <input type="text" id="search-eu" class="search-bar" placeholder="Rechercher un eurodéputé...">
  <div class="filter-row">
    <label for="filter-posture" class="sr-only">Filtrer par posture</label>
    <select id="filter-posture" class="filter-select">
      <option value="">Toutes postures</option>
      <option value="ally">🟢 Favorables</option>
      <option value="watch">🟡 Neutres</option>
      <option value="against">🔴 Défavorables</option>
    </select>
    <label for="filter-groupe" class="sr-only">Filtrer par groupe politique</label>
    <select id="filter-groupe" class="filter-select"><option value="">Tous les groupes</option></select>
    <label for="filter-actifs" class="sr-only">Filtrer par activité</label>
    <select id="filter-actifs" class="filter-select">
      <option value="">Tous les MEPs</option>
      <option value="actif">Actifs sur thèmes FICT</option>
    </select>
  </div>
  <div style="overflow-x:auto">
  <table id="meps-table">
    <thead><tr>
      <th onclick="sortTable('posture')">Posture ↕</th>
      <th onclick="sortTable('nom')">Eurodéputé ↕</th>
      <th onclick="sortTable('groupe')">Groupe ↕</th>
      <th onclick="sortTable('farm_to_fork')" title="Interventions Farm to Fork (EN)">Farm to Fork ↕</th>
      <th onclick="sortTable('additifs')" title="Interventions additifs alimentaires">Additifs ↕</th>
      <th onclick="sortTable('nitrites')" title="Interventions nitrites">Nitrites ↕</th>
      <th onclick="sortTable('score_eu')">Score activité ↕</th>
      <th>Profil EP</th>
    </tr></thead>
    <tbody id="meps-tbody"></tbody>
  </table>
  </div>
  <div style="font-size:11px;color:#aaa;margin-top:10px;font-style:italic">
    ⚠️ La posture est une estimation basée sur le groupe politique (vote PE sur Farm to Fork 2021). Elle ne reflète pas les positions individuelles. Score élevé = forte activité sur ces thèmes, pas nécessairement une position favorable à la FICT.
  </div>
</div>

</div>
<script>
let allMeps = [];
let sortKey = 'score_eu';
let sortAsc = false;

// Mapping groupe → posture (basé sur vote PE résolution Farm to Fork 2021)
const POSTURE_MAP = {{
  'Europe - Verts/Alliance libre européenne':                        'against',
  'Europe - Alliance Progressiste des Socialistes et Démocrates':   'against',
  'Europe - Gauche au Parlement européen - GUE/NGL':                'against',
  'Europe - Groupe confédéral de la Gauche unitaire européenne':    'against',
  'Europe - Renew Europe':                                           'watch',
  'Europe - Alliance des démocrates et des libéraux pour l\'Europe':'watch',
  'Europe - Non inscrits':                                           'watch',
  'Europe - Parti populaire européen (Démocrates-Chrétiens)':       'ally',
  'Europe - Conservateurs et Réformistes européens':                'ally',
  "Europe - Patriotes pour l'Europe":                               'ally',
  'Europe - Identité et démocratie':                                'ally',
  "Europe - L'Europe des nations souveraines (ENS)":               'ally',
  'Europe - Europe des Nations et des Libertés':                    'ally',
}};

const POSTURE_LABELS = {{
  ally:    '<span class="posture-ally">🟢 Favorable</span>',
  watch:   '<span class="posture-watch">🟡 Neutre</span>',
  against: '<span class="posture-against">🔴 Défavorable</span>',
}};
const POSTURE_ORDER = {{ ally: 0, watch: 1, against: 2 }};

function getPosture(m) {{
  return POSTURE_MAP[m.groupe] || 'watch';
}}

fetch('data/meps.json').then(r=>r.json()).then(data => {{
  allMeps = data;
  document.getElementById('n-total').textContent   = data.length;
  document.getElementById('n-ally').textContent    = data.filter(m=>getPosture(m)==='ally').length;
  document.getElementById('n-watch').textContent   = data.filter(m=>getPosture(m)==='watch').length;
  document.getElementById('n-against').textContent = data.filter(m=>getPosture(m)==='against').length;

  const groupes = [...new Set(data.map(m=>m.groupe).filter(Boolean))].sort();
  const sel = document.getElementById('filter-groupe');
  groupes.forEach(g => {{
    const opt = document.createElement('option');
    opt.value = g; opt.textContent = g.replace('Europe - ','');
    sel.appendChild(opt);
  }});

  restoreFilters();
  render();
}});

const STORAGE_KEY='fict_eu_filters';
function saveFilters(){{const s={{}};document.querySelectorAll('.filter-select,.search-bar').forEach(el=>{{s[el.id]=el.value;}});s._sortKey=sortKey;s._sortAsc=sortAsc;sessionStorage.setItem(STORAGE_KEY,JSON.stringify(s));}}
function restoreFilters(){{const raw=sessionStorage.getItem(STORAGE_KEY);if(!raw)return;try{{const s=JSON.parse(raw);Object.keys(s).forEach(k=>{{if(k.startsWith('_'))return;const el=document.getElementById(k);if(el)el.value=s[k];}});if(s._sortKey!==undefined)sortKey=s._sortKey;if(s._sortAsc!==undefined)sortAsc=s._sortAsc;}}catch(e){{}}}}

function render() {{
  const q       = document.getElementById('search-eu').value.toLowerCase();
  const grp     = document.getElementById('filter-groupe').value;
  const actifs  = document.getElementById('filter-actifs').value;
  const posture = document.getElementById('filter-posture').value;

  let data = allMeps.filter(m => {{
    if (q && !m.nom.toLowerCase().includes(q)) return false;
    if (grp && m.groupe !== grp) return false;
    if (actifs === 'actif' && m.score_eu === 0) return false;
    if (posture && getPosture(m) !== posture) return false;
    return true;
  }});

  data = data.slice().sort((a,b) => {{
    if (sortKey === 'posture') {{
      const pa = POSTURE_ORDER[getPosture(a)] ?? 1;
      const pb = POSTURE_ORDER[getPosture(b)] ?? 1;
      return sortAsc ? pa-pb : pb-pa;
    }}
    const av = a[sortKey], bv = b[sortKey];
    if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    return sortAsc ? av-bv : bv-av;
  }});

  const scoreMax = allMeps.reduce((mx,x)=>Math.max(mx,x.score_eu),1);
  const tbody = document.getElementById('meps-tbody');
  tbody.innerHTML = data.map(m => {{
    const p      = getPosture(m);
    const rowCls = p === 'ally' ? 'row-ally' : p === 'against' ? 'row-against' : '';
    const grpShort = (m.groupe||'').replace('Europe - ','').substring(0,22);
    const pct      = Math.min(100,(m.score_eu/scoreMax)*100).toFixed(0);
    const scoreStyle = m.score_eu > 30 ? 'font-weight:700;color:#e85d04' : m.score_eu > 5 ? 'font-weight:600' : '';
    const profil   = m.url_fiche ? `<a href="${{m.url_fiche}}" target="_blank" rel="noopener" style="color:#4361ee;font-size:12px">→ EP</a>` : '-';
    return `<tr class="${{rowCls}}">
      <td>${{POSTURE_LABELS[p] || ''}}</td>
      <td style="font-weight:600">${{m.nom}}</td>
      <td><span style="font-size:11px;background:#f0f0f0;padding:2px 7px;border-radius:10px;white-space:nowrap">${{grpShort}}</span></td>
      <td>${{m.farm_to_fork || '-'}}</td>
      <td>${{m.additifs || '-'}}</td>
      <td>${{m.nitrites || '-'}}</td>
      <td style="background:linear-gradient(to right,rgba(232,93,4,.1) ${{pct}}%,transparent ${{pct}}%);${{scoreStyle}}">${{m.score_eu || '-'}}</td>
      <td>${{profil}}</td>
    </tr>`;
  }}).join('');
  document.getElementById('meps-count').textContent = data.length + ' eurodéputés affichés';
  saveFilters();
}}

function sortTable(key) {{
  if (sortKey === key) sortAsc = !sortAsc;
  else {{ sortKey = key; sortAsc = false; }}
  render();
}}

document.getElementById('search-eu').addEventListener('input', render);
document.getElementById('filter-groupe').addEventListener('change', render);
document.getElementById('filter-actifs').addEventListener('change', render);
document.getElementById('filter-posture').addEventListener('change', render);

// Tri par défaut : posture d'abord (alliés en haut), puis score
</script>
</body>
</html>"""
    (SITE_DIR / 'europe.html').write_text(html, encoding='utf-8')
    print('    ✅ europe.html')


def write_methodologie():
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{NOINDEX}
<title>FICT - Méthodologie</title>
<style>{BASE_CSS}
.meth-section {{ background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 20px; }}
.meth-title {{ font-size: 17px; font-weight: 700; margin-bottom: 16px; color: #1a1a2e; border-bottom: 2px solid #e85d04; padding-bottom: 8px; }}
.formula-box {{ background: #1a1a2e; color: white; border-radius: 8px; padding: 16px 20px; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.8; margin: 12px 0; }}
.formula-comment {{ color: #aaa; font-size: 12px; }}
.source-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
.source-table th {{ background: #f8f9fa; padding: 10px 14px; text-align: left; font-weight: 600; font-size: 12px; color: #555; }}
.source-table td {{ padding: 10px 14px; border-bottom: 1px solid #f0f0f0; vertical-align: top; }}
.source-tag {{ display: inline-block; background: #e8f4e8; color: #1a5c1a; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
.vote-item {{ display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; align-items: flex-start; }}
.vote-badge {{ background: #1a1a2e; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; white-space: nowrap; }}
</style>
</head>
<body>
{write_nav('methodologie.html')}
<div class="container" style="max-width:900px">
  <div class="page-title">📖 Méthodologie &amp; Sources</div>
  <div class="page-subtitle">Comment sont calculés les scores et d'où viennent les données</div>

  <div class="meth-section">
    <div class="meth-title">📊 Formule du score FICT</div>
    <p style="font-size:13px;color:#555;margin-bottom:12px">Le score FICT mesure la <strong>priorité de contact</strong> d'un élu pour les affaires publiques FICT : un élu fortement ancré dans une zone de production ET actif sur les dossiers agricoles est prioritaire.</p>
    <div class="formula-box">
score_fict = score_eco × (1 + (score_impl + score_engagement) / 10)<br>
<br>
<span class="formula-comment"># Score implantation (poids économique de la zone)</span><br>
score_eco = nb_sites_fict<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 2 × nb_sites_charcuterie<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 1 × nb_sites_transformation_viande<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 0.5 × nb_sites_volaille<br>
<br>
<span class="formula-comment"># Score implication parlementaire</span><br>
score_impl = 3 × membre_commission_agriculture<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 2 × membre_mission_egalim<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 1 × membre_commission_economique<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ 0.5 × taux_participation<br>
<br>
<span class="formula-comment"># Score engagement (missions et groupes spécifiques FICT)</span><br>
score_engagement = Σ memberships (0–11 points max)<br>
&nbsp;&nbsp;&nbsp;&nbsp;<span class="formula-comment"># commission_enquete_gd, mission_nitrites, groupe_etude_iaa...</span>
    </div>
    <p style="font-size:12px;color:#888;margin-top:8px">Géographie : le score utilise le département (et non la circonscription) comme unité d'analyse - précision sub-départementale non disponible via SIRENE.</p>

    <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:18px 22px;margin-top:16px">
      <div style="font-weight:700;font-size:14px;color:#166534;margin-bottom:10px">Exemple : député fictif du dept. 42 (Loire)</div>
      <div style="font-size:13px;color:#555;line-height:1.8">
        <strong>1. Score implantation (score_eco)</strong><br>
        Dept. 42 : 13 sites FICT dont 8 charcuteries, 3 transfo viande, 2 abattoirs<br>
        <code style="background:#e8f5e9;padding:2px 6px;border-radius:3px">score_eco = 13 + 2x8 + 1x3 + 0.5x2 = 33.0</code><br><br>
        <strong>2. Score implication (score_impl)</strong><br>
        Membre commission agriculture (3 pts) + mission EGALIM (2 pts)<br>
        <code style="background:#e8f5e9;padding:2px 6px;border-radius:3px">score_impl = 3 + 2 = 5.0</code><br><br>
        <strong>3. Score engagement</strong><br>
        Groupe d'etude IAA (1 pt) + observatoire des marges (1 pt)<br>
        <code style="background:#e8f5e9;padding:2px 6px;border-radius:3px">score_engagement = 2</code><br><br>
        <strong>4. Score FICT final</strong><br>
        <code style="background:#e8f5e9;padding:2px 6px;border-radius:3px">score = 33.0 x (1 + (5.0 + 2) / 10) = 33.0 x 1.7 = <strong style="color:#e85d04;font-size:15px">56.1</strong></code>
      </div>
    </div>
  </div>

  <div class="meth-section">
    <div class="meth-title">🗳️ Votes nominatifs suivis (7 scrutins)</div>
    <div class="vote-item"><span class="vote-badge">EGALIM 1</span><div><strong>Loi 2018-938</strong> - Relations commerciales dans le secteur agricole et alimentation</div></div>
    <div class="vote-item"><span class="vote-badge">EGALIM 2</span><div><strong>Loi 2021-1357</strong> - Protection de la rémunération des agriculteurs</div></div>
    <div class="vote-item"><span class="vote-badge">EGALIM 3</span><div><strong>Loi 2023-221 / Descrozaille</strong> - Équilibre des relations commerciales entre producteurs et acheteurs</div></div>
    <div class="vote-item"><span class="vote-badge">LOA 2024</span><div><strong>Loi d'orientation agricole 2024</strong> - Souveraineté agricole et renouvellement des générations</div></div>
    <div class="vote-item"><span class="vote-badge">PPL Revenu Agri</span><div><strong>2024</strong> - PPL relative au revenu des agriculteurs</div></div>
    <div class="vote-item"><span class="vote-badge">PPL Marges</span><div><strong>PPL sur les marges agroalimentaires</strong> (rejeté)</div></div>
    <div class="vote-item" style="border-bottom:none"><span class="vote-badge">PPL Stabilité</span><div><strong>2025 - 17e législature</strong> - PPL renforcer la stabilité économique agroalimentaire (dossier AN 17e)</div></div>
  </div>

  <div class="meth-section">
    <div class="meth-title">🎯 Engagements parlementaires suivis (score_engagement)</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px">
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Commission d'enquête grande distribution</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Mission information nitrites</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Mission suivi grande distribution</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Mission contrôle EGALIM 1</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Mission application loi 2022</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Groupe d'étude industrie agroalimentaire</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Groupe d'étude agriculture</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Observatoire des marges</div>
      <div style="padding:8px;background:#f8f9fa;border-radius:6px">Mission autonomie alimentaire</div>
    </div>
  </div>

  <div class="meth-section">
    <div class="meth-title">📂 Sources de données</div>
    <table class="source-table">
      <thead><tr><th>Source</th><th>Données récupérées</th><th>Date collecte</th></tr></thead>
      <tbody>
        <tr><td><span class="source-tag">Assemblée Nationale</span><br><small>Open data AN (data.assemblee-nationale.fr)</small></td><td>Identités députés, groupes, scrutins nominatifs, commissions, missions</td><td>Avril 2026</td></tr>
        <tr><td><span class="source-tag">Sénat</span><br><small>Export SQL + nosdéputés.fr</small></td><td>Identités sénateurs, groupes politiques, commissions</td><td>Avril 2026</td></tr>
        <tr><td><span class="source-tag">nosdéputés.fr</span><br><small>API Regards Citoyens /synthese/json</small></td><td>Interventions hémicycle, questions écrites/orales, PPL déposées/signées, présence</td><td>Avril 2026</td></tr>
        <tr><td><span class="source-tag">SIRENE / INSEE</span><br><small>API Recherche Entreprises (api.entreprise.data.gouv.fr)</small></td><td>Établissements actifs codes NAF 10.11Z, 10.12Z, 10.13A, 10.13B - coordonnées, commune, département</td><td>Avril 2026</td></tr>
        <tr><td><span class="source-tag">INPI / Pappers</span><br><small>API Pappers (pappers.fr)</small></td><td>CA, résultat net, effectifs, dirigeants, forme juridique</td><td>Avril 2026</td></tr>
        <tr><td><span class="source-tag">FICT</span><br><small>Fichier adhérents par syndicat régional</small></td><td>Liste de référence des ~300 entreprises membres (source de vérité pour le périmètre)</td><td>Fourni par la FICT</td></tr>
      </tbody>
    </table>
  </div>

  <div class="meth-section">
    <div class="meth-title">⚠️ Limites à connaître</div>
    <ul style="font-size:13px;color:#555;line-height:2;padding-left:20px">
      <li><strong>Niveau département</strong> : le score utilise le département (pas la circonscription) - tous les élus d'un département reçoivent le même score d'implantation.</li>
      <li><strong>Interventions thématiques</strong> : les interventions hémicycle (nosdéputés.fr) sont globales, pas filtrées sur les thèmes agricoles.</li>
      <li><strong>Scrutins Sénat</strong> : les votes nominatifs ne sont disponibles que pour les députés (AN). Les sénateurs votent selon des procédures différentes.</li>
      <li><strong>SIRENE</strong> : délai de mise à jour possible (ouvertures/fermetures récentes peuvent manquer).</li>
      <li><strong>17e législature en cours</strong> : <code>sort: null</code> sur les amendements = normal pour la session en cours (pas encore finalisés).</li>
    </ul>
  </div>

  <div style="background:#1a1a2e;color:rgba(255,255,255,.7);border-radius:12px;padding:20px 24px;text-align:center;font-size:13px">
    Réalisé par <a href="https://www.linkedin.com/in/julien-vieira-b59673b4/" target="_blank" rel="noopener" style="color:#e85d04;font-weight:600">Julien Vieira</a> - Consultant affaires publiques · Données collectées en avril 2026
  </div>
</div>
</body>
</html>"""
    (SITE_DIR / 'methodologie.html').write_text(html, encoding='utf-8')
    print('    ✅ methodologie.html')


def write_readme():
    readme = """# FICT Lobbying - Minisite

Site statique généré automatiquement depuis le pipeline FICT.

## GitHub Pages Setup

1. Pousser ce dossier `site/` dans un repo GitHub
2. Dans Settings → Pages : sélectionner la branche `main` et le dossier `/docs` (ou renommer `site/` en `docs/`)
3. L'URL sera : `https://{username}.github.io/{repo}/`

## Structure

- `index.html` - Carte Leaflet interactive (choroplèthe + marqueurs)
- `parlementaires.html` - Tableau filtrable/triable des 925 parlementaires
- `fiche.html` - Fiche détaillée par parlementaire (votes + commissions + sites)
- `partis.html` - Analyse par parti politique
- `groupes.html` - Groupes industriels multi-sites
- `data/` - Fichiers JSON (régénérés par `python3 generate_site.py`)

## Données

Générées par `pipeline.py` puis converties en JSON par `generate_site.py`.
Pour mettre à jour, relancer `python3 pipeline.py` puis `python3 generate_site.py`.
"""
    (SITE_DIR / 'README.md').write_text(readme, encoding='utf-8')
    print('    ✅ README.md')


def main():
    print('=' * 55)
    print('GÉNÉRATEUR MINISITE FICT - GitHub Pages')
    print('=' * 55)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    parl, sites, partis, groupes, meps = build_json_data()

    print('\n[2] Génération des pages HTML...')
    write_accueil(parl, sites, partis)
    write_index()
    write_parlementaires()
    write_fiche()
    write_partis()
    write_groupes()
    write_entreprises()
    if meps:
        write_europe()
    write_methodologie()
    write_readme()

    print(f'\n✅ Minisite généré dans {SITE_DIR}/')
    print(f'   {len(list(SITE_DIR.glob("*.html")))} pages HTML')
    print(f'   {len(list(DATA_DIR.glob("*.json")))} fichiers JSON de données')
    print('\nPour déployer : pousser ~/fict-lobbying/site/ sur GitHub et activer Pages.')


if __name__ == '__main__':
    main()
