/* ==========================================================================
   Comptes — interface
   Tout est enregistré automatiquement : chaque modification part au serveur,
   qui renvoie le mois entier recalculé. Les totaux ne peuvent donc jamais
   diverger de ce qui est affiché.
   ========================================================================== */

'use strict';

const $  = (sel, racine = document) => racine.querySelector(sel);
const $$ = (sel, racine = document) => Array.from(racine.querySelectorAll(sel));

const etat = {
  moisId: null,
  detail: null,
  vue: 'tableau',
  filtreNature: 'tout',
  filtreRevenu: 'tout',
  recherche: '',
  masquerPause: false,
};

const POSTES_COURANTS = ['Marché', 'Carrefour', 'Wevrac', 'Boulangerie', 'Pharmacie'];
const ACHATS_COURANTS = ['Fruits/Légumes', 'Olives', 'Fromage', 'Viande', 'Poisson',
                         'Pain', 'Italien', 'Café', 'Poulet'];
const JOURS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
const LIENS = { '': '—', courses: 'Courses', heures: 'Heures gardées',
                garde: 'Garde (coût brut)', caf: 'CAF (aide garde)' };

/* -------------------------------------------------------------- Outils --- */

function el(balise, attributs = {}, ...enfants) {
  const noeud = document.createElement(balise);
  for (const [nom, valeur] of Object.entries(attributs)) {
    if (valeur === null || valeur === undefined || valeur === false) continue;
    if (nom === 'class') noeud.className = valeur;
    else if (nom === 'texte') noeud.textContent = valeur;
    else if (nom.startsWith('on')) noeud.addEventListener(nom.slice(2), valeur);
    else noeud.setAttribute(nom, valeur === true ? '' : valeur);
  }
  for (const enfant of enfants.flat()) {
    if (enfant === null || enfant === undefined || enfant === false) continue;
    noeud.append(enfant.nodeType ? enfant : document.createTextNode(String(enfant)));
  }
  return noeud;
}

const formatEuros = new Intl.NumberFormat('fr-FR',
  { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 });
const formatNombre = new Intl.NumberFormat('fr-FR',
  { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const euros = (v) => formatEuros.format(Number(v) || 0);
const signe = (v) => (Number(v) > 0 ? '+' : '') + euros(v);

/** Montant tel qu'on le saisit : « 19,99 », et rien du tout si c'est zéro. */
function montantSaisi(valeur) {
  const nombre = Number(valeur) || 0;
  return nombre === 0 ? '' : formatNombre.format(nombre).replace(/ | /g, ' ');
}

function libelleMois(code) {
  const [annee, mois] = String(code).split('-').map(Number);
  if (!annee || !mois) return code;
  const nom = new Date(annee, mois - 1, 1)
    .toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
  return nom.charAt(0).toUpperCase() + nom.slice(1);
}

function decaleMois(code, pas) {
  const [annee, mois] = String(code).split('-').map(Number);
  const d = new Date(annee, mois - 1 + pas, 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/* ---------------------------------------------------------------- API --- */

async function api(methode, chemin, corps) {
  const reponse = await fetch(chemin, {
    method: methode,
    headers: corps ? { 'Content-Type': 'application/json' } : undefined,
    body: corps ? JSON.stringify(corps) : undefined,
  });
  let donnees = {};
  try { donnees = await reponse.json(); } catch { /* réponse vide */ }
  if (!reponse.ok) throw new Error(donnees.erreur || `Erreur ${reponse.status}`);
  return donnees;
}

/** Applique une réponse serveur contenant un mois complet. */
function applique(detail) {
  if (!detail || !detail.mois) return detail;
  etat.detail = detail;
  etat.moisId = detail.mois.id;
  try { localStorage.setItem('comptes.mois', String(etat.moisId)); } catch { /* ignoré */ }
  dessineTout();
  return detail;
}

let minuteurSauvegarde = null;
function signaleSauvegarde(texte = 'Enregistré') {
  const zone = $('#sauvegarde');
  zone.textContent = texte;
  zone.classList.add('visible');
  clearTimeout(minuteurSauvegarde);
  minuteurSauvegarde = setTimeout(() => zone.classList.remove('visible'), 1400);
}

function toast(texte, options = {}) {
  const boite = el('div', { class: 'toast' + (options.erreur ? ' toast--erreur' : '') },
    el('span', { class: 'toast__texte', texte }));
  if (options.action) {
    boite.append(el('button', {
      class: 'bouton', onclick: () => { boite.remove(); options.action.faire(); },
      texte: options.action.libelle,
    }));
  }
  boite.append(el('button', {
    class: 'bouton bouton--fantome', title: 'Fermer', texte: '✕',
    onclick: () => boite.remove(),
  }));
  $('#toasts').append(boite);
  setTimeout(() => boite.remove(), options.duree || 7000);
}

/** Enveloppe une action serveur : applique le résultat, signale les erreurs. */
async function agis(promesse, messageOk) {
  try {
    const resultat = await promesse;
    applique(resultat);
    if (messageOk) signaleSauvegarde(messageOk);
    return resultat;
  } catch (erreur) {
    toast(erreur.message, { erreur: true });
    return null;
  }
}

/* ------------------------------------------------------ Focus conservé --- */

function memoriseFocus() {
  const actif = document.activeElement;
  if (!actif || !actif.dataset || !actif.dataset.cle) return null;
  return {
    cle: actif.dataset.cle,
    debut: typeof actif.selectionStart === 'number' ? actif.selectionStart : null,
  };
}

function restaureFocus(memoire) {
  if (!memoire) return;
  const champ = document.querySelector(`[data-cle="${CSS.escape(memoire.cle)}"]`);
  if (!champ) return;
  champ.focus();
  if (memoire.debut !== null && typeof champ.setSelectionRange === 'function') {
    const position = Math.min(memoire.debut, champ.value.length);
    try { champ.setSelectionRange(position, position); } catch { /* champ non textuel */ }
  }
}

/* ------------------------------------------------------- Rendu général --- */

function dessineTout() {
  const memoire = memoriseFocus();
  dessineSelecteurMois();
  dessineTableauDeBord();
  dessineDepenses();
  dessineRevenus();
  dessineCourses();
  dessineHeures();
  restaureFocus(memoire);
}

function dessineSelecteurMois() {
  const choix = $('#choix-mois');
  const disponibles = etat.detail.mois_disponibles || [etat.detail.mois];
  choix.textContent = '';
  for (const mois of disponibles) {
    choix.append(el('option', { value: mois.id, selected: mois.id === etat.moisId },
      libelleMois(mois.libelle)));
  }
}

const VUES = ['tableau', 'depenses', 'revenus', 'courses', 'heures'];

function montreVue(nom) {
  if (!VUES.includes(nom)) nom = 'tableau';
  etat.vue = nom;
  for (const onglet of $$('.onglet')) {
    onglet.setAttribute('aria-selected', String(onglet.dataset.vue === nom));
  }
  for (const vue of $$('.vue')) vue.hidden = vue.id !== `vue-${nom}`;
  if (nom === 'tableau') dessineGraphiqueCategories();
  if (location.hash.slice(1) !== nom) history.replaceState(null, '', `#${nom}`);
  try { localStorage.setItem('comptes.vue', nom); } catch { /* ignoré */ }
}

window.addEventListener('hashchange', () => montreVue(location.hash.slice(1)));

/* ------------------------------------------------- Vue tableau de bord --- */

function tuile(etiquette, valeur, note, classeNote) {
  return el('div', { class: 'tuile' },
    el('div', { class: 'tuile__etiquette', texte: etiquette }),
    el('div', { class: 'tuile__valeur', texte: valeur }),
    note ? el('div', { class: `tuile__delta ${classeNote || ''}`, texte: note }) : null);
}

function dessineTableauDeBord() {
  const { budget, courses, heures } = etat.detail.recap;

  const restant = budget.restant.reel;
  $('#heros').replaceChildren(
    el('div', { class: 'heros__bloc' },
      el('div', { class: 'heros__etiquette', texte: 'Restant à vivre ce mois' }),
      el('div', {
        class: 'heros__valeur' + (restant < 0 ? ' heros__valeur--negatif' : ''),
        texte: euros(restant),
      }),
      el('div', {
        class: 'heros__note',
        texte: `Prévu : ${euros(budget.restant.estime)} · ` +
               `${restant < 0 ? 'Découvert' : 'Disponible'} au regard des montants réels saisis`,
      })));

  const surplus = budget.surplus.reel;
  $('#tuiles').replaceChildren(
    tuile('Revenus encaissés', euros(budget.revenus.reel),
          `Prévu ${euros(budget.revenus.estime)}`),
    tuile('Dépenses réglées', euros(budget.depenses.reel),
          `Prévu ${euros(budget.depenses.estime)}`),
    tuile('Écart sur les dépenses', signe(surplus),
          surplus >= 0 ? 'Sous le budget prévu' : 'Au-dessus du budget prévu',
          surplus >= 0 ? 'tuile__delta--bon' : 'tuile__delta--mauvais'),
    tuile('Charges fixes', euros(budget.depenses_fixes.reel),
          `Variables ${euros(budget.depenses_variables.reel)}`),
    tuile('Coût net de la garde', euros(budget.garde_nette.reel),
          `Garde ${euros(budget.garde.reel)} − CAF ${euros(budget.caf.reel)}`));

  dessineGraphiqueCategories();
  dessineTableauCategories();

  // Résumé des courses
  const carteCourses = $('#carte-courses-resume');
  carteCourses.replaceChildren(
    el('header', { class: 'carte__entete' },
      el('h2', { texte: 'Budget courses' }),
      el('p', { class: 'carte__sous-titre',
                texte: `${euros(courses.depense)} dépensés sur ${euros(courses.budget_total)}` })),
    jauge('Consommé', courses.depense, courses.budget_total),
    el('div', { class: 'pied-tableau' },
      el('button', {
        class: 'bouton bouton--fantome', texte: 'Détailler les courses →',
        onclick: () => montreVue('courses'),
      })));

  // Résumé des heures
  const carteHeures = $('#carte-heures-resume');
  carteHeures.replaceChildren(
    el('header', { class: 'carte__entete' },
      el('h2', { texte: 'Heures gardées' }),
      el('p', { class: 'carte__sous-titre',
                texte: `${heures.duree} à ${formatNombre.format(heures.taux_horaire)} €/h` })),
    el('div', { class: 'tuile__valeur', texte: euros(heures.net) }),
    el('div', { class: 'tuile__delta',
                texte: `Net · brut ${euros(heures.brut)} − cotisations ${euros(heures.cotisation)}` }),
    el('div', { class: 'pied-tableau' },
      el('button', {
        class: 'bouton bouton--fantome', texte: 'Détailler les heures →',
        onclick: () => montreVue('heures'),
      })));

  // Abonnements en pause
  const cartePause = $('#carte-pause');
  const enPause = budget.en_pause;
  cartePause.replaceChildren(
    el('header', { class: 'carte__entete' },
      el('h2', { texte: 'Lignes en pause' }),
      el('p', { class: 'carte__sous-titre',
                texte: enPause.length
                  ? `${euros(budget.economie_en_pause)} par mois non dépensés`
                  : 'Tout est actif ce mois-ci' })),
    enPause.length
      ? el('ul', { class: 'liste-pause' },
          enPause.slice(0, 6).map(ligne => el('li', {},
            el('span', { texte: ligne.libelle || ligne.categorie }),
            ' — ',
            el('strong', { texte: euros(ligne.estime) }))))
      : null);
}

/* ---------------------------------------------------------- Graphique --- */

/** Échelle terminant sur un chiffre rond, avec des graduations lisibles. */
function graduationsJolies(maxi, cible = 4) {
  if (!(maxi > 0)) return { haut: 100, valeurs: [0, 25, 50, 75, 100] };
  const brut = maxi / cible;
  const puissance = Math.pow(10, Math.floor(Math.log10(brut)));
  const pas = [1, 2, 2.5, 5, 10].map(m => m * puissance).find(p => p >= brut) || 10 * puissance;
  const haut = Math.ceil(maxi / pas) * pas;
  const valeurs = [];
  for (let valeur = 0; valeur <= haut + 1e-9; valeur += pas) {
    valeurs.push(Math.round(valeur * 100) / 100);
  }
  return { haut, valeurs };
}

function cheminBarre(x0, y, longueur, hauteur, rayon) {
  const r = Math.min(rayon, longueur, hauteur / 2);
  if (longueur <= r) return `M${x0},${y} h${longueur} v${hauteur} h${-longueur} z`;
  return `M${x0},${y} h${longueur - r} a${r},${r} 0 0 1 ${r},${r}` +
         ` v${hauteur - 2 * r} a${r},${r} 0 0 1 ${-r},${r} h${-(longueur - r)} z`;
}

function svg(balise, attributs = {}, ...enfants) {
  const noeud = document.createElementNS('http://www.w3.org/2000/svg', balise);
  for (const [nom, valeur] of Object.entries(attributs)) {
    if (valeur === null || valeur === undefined || valeur === false) continue;
    noeud.setAttribute(nom, valeur === true ? '' : String(valeur));
  }
  for (const enfant of enfants.flat()) {
    if (enfant === null || enfant === undefined || enfant === false) continue;
    noeud.append(enfant.nodeType ? enfant : document.createTextNode(String(enfant)));
  }
  return noeud;
}

function tronque(texte, largeurDisponible) {
  const maxi = Math.max(6, Math.floor(largeurDisponible / 6.6));
  return texte.length > maxi ? texte.slice(0, maxi - 1) + '…' : texte;
}

function dessineGraphiqueCategories() {
  const hote = $('#graphique-categories');
  if (!hote || !etat.detail) return;
  const donnees = etat.detail.recap.budget.par_categorie
    .filter(c => c.reel > 0 || c.estime > 0);

  hote.textContent = '';
  if (!donnees.length) {
    hote.append(el('p', { class: 'vide', texte: 'Aucune dépense saisie pour ce mois.' }));
    return;
  }

  hote.append(el('div', { class: 'legende' },
    el('span', { class: 'legende__cle' },
      el('span', { class: 'legende__pastille' }), 'Dépensé'),
    el('span', { class: 'legende__cle' },
      el('span', { class: 'legende__trait' }), 'Prévu')));

  const largeur = Math.max(300, hote.clientWidth || 520);
  const gauche = Math.min(150, Math.max(88, Math.round(largeur * 0.3)));
  const droite = 96;
  const hautBande = 30, epaisseur = 18, hautPlot = 10, basAxe = 28;
  const hauteurTrace = donnees.length * hautBande;
  const hauteur = hautPlot + hauteurTrace + basAxe;
  const echelle = graduationsJolies(Math.max(...donnees.map(d => Math.max(d.reel, d.estime))));
  const largeurUtile = largeur - gauche - droite;
  const x = (v) => gauche + (Math.max(0, v) / echelle.haut) * largeurUtile;

  const racine = svg('svg', {
    viewBox: `0 0 ${largeur} ${hauteur}`, width: largeur, height: hauteur,
    role: 'img', 'aria-label': 'Dépenses réelles et prévues par catégorie',
  });

  // Grille : filets pleins, jamais en pointillés.
  for (const valeur of echelle.valeurs) {
    racine.append(svg('line', {
      x1: x(valeur), x2: x(valeur), y1: hautPlot, y2: hautPlot + hauteurTrace,
      stroke: valeur === 0 ? 'var(--ligne-base)' : 'var(--filet)', 'stroke-width': 1,
    }));
    racine.append(svg('text', {
      x: x(valeur), y: hautPlot + hauteurTrace + 17, 'text-anchor': 'middle',
      fill: 'var(--encre-3)', 'font-size': 11, 'font-family': 'inherit',
    }, formatEuros.format(valeur).replace(/,00/, '')));
  }

  donnees.forEach((categorie, index) => {
    const y = hautPlot + index * hautBande;
    const yBarre = y + (hautBande - epaisseur) / 2;
    const ecart = categorie.estime - categorie.reel;
    const groupe = svg('g', {
      tabindex: 0, role: 'group',
      'aria-label': `${categorie.categorie} : ${euros(categorie.reel)} dépensés, ` +
                    `${euros(categorie.estime)} prévus`,
    });

    groupe.append(svg('text', {
      x: gauche - 10, y: y + hautBande / 2 + 4, 'text-anchor': 'end',
      fill: 'var(--encre-2)', 'font-size': 12, 'font-family': 'inherit',
    }, tronque(categorie.categorie, gauche - 14)));

    if (categorie.reel > 0) {
      groupe.append(svg('path', {
        d: cheminBarre(gauche, yBarre, Math.max(2, x(categorie.reel) - gauche), epaisseur, 4),
        fill: 'var(--serie-1)',
      }));
      // Valeur posée après la marque la plus à droite : elle ne croise jamais
      // le repère du prévu. La marge de droite lui est réservée.
      groupe.append(svg('text', {
        x: Math.max(x(categorie.reel), x(categorie.estime)) + 10,
        y: y + hautBande / 2 + 4, 'text-anchor': 'start',
        fill: 'var(--encre-2)', 'font-size': 11.5, 'font-family': 'inherit',
      }, euros(categorie.reel).replace(/,00/, '')));
    }

    if (categorie.estime > 0) {
      // Repère du prévu : un trait, jamais une seconde barre.
      groupe.append(svg('line', {
        x1: x(categorie.estime), x2: x(categorie.estime),
        y1: yBarre - 3, y2: yBarre + epaisseur + 3,
        stroke: 'var(--encre-2)', 'stroke-width': 2, 'stroke-linecap': 'round',
      }));
    }

    // Cible de survol : toute la bande, bien plus large que la marque.
    const cible = svg('rect', {
      x: 0, y, width: largeur, height: hautBande, fill: 'transparent',
    });
    groupe.append(cible);

    const montre = (evenement) => montreInfobulle(evenement, categorie, ecart);
    groupe.addEventListener('pointerenter', montre);
    groupe.addEventListener('pointermove', montre);
    groupe.addEventListener('focus', () => montreInfobulle(null, categorie, ecart, groupe));
    groupe.addEventListener('pointerleave', cacheInfobulle);
    groupe.addEventListener('blur', cacheInfobulle);
    racine.append(groupe);
  });

  hote.append(racine);
}

function montreInfobulle(evenement, categorie, ecart, ancre) {
  const boite = $('#infobulle');
  boite.replaceChildren(
    el('div', { class: 'infobulle__titre', texte: categorie.categorie }),
    ligneInfobulle('Dépensé', euros(categorie.reel), 'var(--serie-1)'),
    ligneInfobulle('Prévu', euros(categorie.estime), null),
    ligneInfobulle(ecart >= 0 ? 'Reste' : 'Dépassement', euros(Math.abs(ecart)), null));
  boite.hidden = false;
  const rect = ancre ? ancre.getBoundingClientRect() : null;
  const gauche = evenement ? evenement.clientX + 14 : rect.left + 20;
  const haut = evenement ? evenement.clientY + 14 : rect.top;
  const largeur = boite.offsetWidth;
  boite.style.left = `${Math.min(gauche, window.innerWidth - largeur - 12)}px`;
  boite.style.top = `${Math.min(haut, window.innerHeight - boite.offsetHeight - 12)}px`;
}

function ligneInfobulle(nom, valeur, couleur) {
  return el('div', { class: 'infobulle__ligne' },
    el('span', { class: 'infobulle__nom' },
      couleur
        ? el('span', { class: 'legende__pastille', style: `background:${couleur}` })
        : el('span', { class: 'legende__trait' }),
      nom),
    el('span', { class: 'infobulle__valeur', texte: valeur }));
}

function cacheInfobulle() { $('#infobulle').hidden = true; }

function dessineTableauCategories() {
  const donnees = etat.detail.recap.budget.par_categorie;
  const corps = donnees.map(c => el('tr', {},
    el('td', { texte: c.categorie }),
    el('td', { texte: euros(c.estime) }),
    el('td', { texte: euros(c.reel) }),
    el('td', { texte: signe(c.estime - c.reel) })));
  $('#tableau-categories').replaceChildren(
    el('table', {},
      el('thead', {}, el('tr', {},
        el('th', { texte: 'Catégorie' }), el('th', { texte: 'Prévu' }),
        el('th', { texte: 'Dépensé' }), el('th', { texte: 'Écart' }))),
      el('tbody', {}, corps)));
}

function jauge(nom, valeur, budget) {
  const part = budget > 0 ? valeur / budget : 0;
  const pourcent = Math.min(100, Math.max(0, part * 100));
  let modificateur = '', icone = '✓', message = 'Dans le budget';
  if (part > 1) { modificateur = '--critique'; icone = '✕'; message = 'Budget dépassé'; }
  else if (part >= 0.85) { modificateur = '--alerte'; icone = '⚠'; message = 'Budget presque atteint'; }

  return el('div', { class: 'jauge' },
    el('div', { class: 'jauge__entete' },
      el('span', { class: 'jauge__nom', texte: nom }),
      el('span', { class: 'jauge__chiffres', texte: `${euros(valeur)} / ${euros(budget)}` })),
    el('div', {
      class: 'jauge__piste', role: 'meter', 'aria-valuenow': Math.round(valeur),
      'aria-valuemin': '0', 'aria-valuemax': Math.round(budget) || 0,
      'aria-label': `${nom} : ${euros(valeur)} sur ${euros(budget)}`,
    }, el('div', {
      class: `jauge__remplissage jauge__remplissage${modificateur}`,
      style: `width:${pourcent}%`,
    })),
    el('div', { class: `jauge__etat jauge__etat${modificateur}`,
                texte: `${icone} ${message} · reste ${euros(budget - valeur)}` }));
}

/* ------------------------------------------------- Tableaux modifiables --- */

function champTexte(entite, id, champ, valeur, options = {}) {
  return el('input', {
    type: 'text', value: valeur ?? '', class: options.classe || null,
    placeholder: options.placeholder || null,
    list: options.liste || null,
    inputmode: options.inputmode || null,
    'aria-label': options.etiquette || champ,
    'data-cle': `${entite}-${id}-${champ}`,
    'data-entite': entite, 'data-id': id, 'data-champ': champ,
  });
}

function champMontant(entite, id, champ, valeur, etiquette) {
  return champTexte(entite, id, champ, montantSaisi(valeur),
    { classe: 'montant', inputmode: 'decimal', placeholder: '0,00', etiquette });
}

function celluleEcart(ligne) {
  const estime = ligne.actif ? Number(ligne.estime) : 0;
  const ecart = estime - Number(ligne.reel);
  const classe = ecart > 0.004 ? 'ecart--bon' : (ecart < -0.004 ? 'ecart--mauvais' : '');
  return el('span', { class: `ecart ${classe}`, texte: ecart === 0 ? '—' : signe(ecart) });
}

function listeCategories(type) {
  const vues = new Set(etat.detail.lignes
    .filter(l => (type === 'depense' ? l.type === 'depense' : l.type !== 'depense'))
    .map(l => l.categorie).filter(Boolean));
  return Array.from(vues).sort((a, b) => a.localeCompare(b, 'fr'));
}

function selecteur(entite, id, champ, valeur, choix, etiquette) {
  return el('select', {
    'data-cle': `${entite}-${id}-${champ}`, 'aria-label': etiquette || champ,
    'data-entite': entite, 'data-id': id, 'data-champ': champ,
  }, choix.map(([cle, libelle]) =>
    el('option', { value: cle, selected: String(cle) === String(valeur ?? '') }, libelle)));
}

function ligneTableau(ligne, colonnes) {
  const tr = el('tr', {
    class: ligne.actif ? '' : 'en-pause',
    'data-ligne': ligne.id,
  });
  for (const colonne of colonnes) tr.append(colonne(ligne));
  return tr;
}

function boutonSupprimer(entite, id, description) {
  return el('button', {
    class: 'bouton bouton--fantome', texte: '✕',
    title: `Supprimer ${description}`, 'aria-label': `Supprimer ${description}`,
    'data-supprimer': entite, 'data-id': id,
  });
}

/* ------------------------------------------------------- Vue dépenses --- */

function dessineDepenses() {
  const recherche = etat.recherche.trim().toLowerCase();
  const lignes = etat.detail.lignes.filter(l =>
    l.type === 'depense'
    && (etat.filtreNature === 'tout' || l.nature === etat.filtreNature)
    && (!etat.masquerPause || l.actif)
    && (!recherche
        || l.libelle.toLowerCase().includes(recherche)
        || l.categorie.toLowerCase().includes(recherche)));

  const hote = $('#table-depenses');
  hote.textContent = '';
  $('#recherche-depenses').value = etat.recherche;
  $('#masquer-pause').checked = etat.masquerPause;

  if (!lignes.length) {
    hote.append(el('div', { class: 'vide' },
      etat.detail.lignes.some(l => l.type === 'depense')
        ? 'Aucune dépense ne correspond à ce filtre.'
        : 'Aucune dépense pour l’instant. Utilisez « + Ajouter une dépense ».'));
    return;
  }

  const categories = listeCategories('depense');
  hote.append(el('datalist', { id: 'categories-depenses' },
    categories.map(c => el('option', { value: c }))));

  const groupes = new Map();
  for (const ligne of lignes) {
    const cle = ligne.categorie || 'Sans catégorie';
    if (!groupes.has(cle)) groupes.set(cle, []);
    groupes.get(cle).push(ligne);
  }

  for (const [categorie, membres] of groupes) {
    const totalPrevu = membres.reduce((s, l) => s + (l.actif ? Number(l.estime) : 0), 0);
    const totalReel = membres.reduce((s, l) => s + Number(l.reel), 0);

    hote.append(el('section', { class: 'groupe' },
      el('header', { class: 'groupe__entete' },
        el('span', { class: 'groupe__nom', texte: categorie }),
        el('span', { class: 'groupe__total',
                     texte: `${euros(totalReel)} dépensés · ${euros(totalPrevu)} prévus` }),
        el('span', { class: 'pousse' }),
        el('button', {
          class: 'bouton bouton--fantome', texte: '+ Ligne',
          'data-ajouter': 'depense', 'data-categorie': categorie,
        })),
      el('table', { class: 'lignes' },
        el('thead', {}, el('tr', {},
          el('th', { texte: 'Actif' }), el('th', { texte: 'Libellé' }),
          el('th', { texte: 'Catégorie' }), el('th', { texte: 'Nature' }),
          el('th', { class: 'col-nombre', texte: 'Prévu' }),
          el('th', { class: 'col-nombre', texte: 'Réel' }),
          el('th', { class: 'col-nombre', texte: 'Écart' }),
          el('th', { texte: 'Note' }), el('th', { texte: '' }))),
        el('tbody', {}, membres.map(ligne => ligneTableau(ligne, [
          l => el('td', { class: 'col-actif', 'data-etiquette': 'Actif' },
            el('input', {
              type: 'checkbox', class: 'bascule', checked: !!l.actif,
              title: l.actif ? 'Compté dans les totaux' : 'En pause : non compté',
              'aria-label': `Compter « ${l.libelle} » dans les totaux`,
              'data-cle': `ligne-${l.id}-actif`,
              'data-entite': 'ligne', 'data-id': l.id, 'data-champ': 'actif',
            })),
          l => el('td', { class: 'col-libelle', 'data-etiquette': 'Libellé' },
            champTexte('ligne', l.id, 'libelle', l.libelle,
              { placeholder: 'Nom de la dépense', etiquette: 'Libellé' })),
          l => el('td', { 'data-etiquette': 'Catégorie' },
            champTexte('ligne', l.id, 'categorie', l.categorie,
              { liste: 'categories-depenses', placeholder: 'Catégorie', etiquette: 'Catégorie' })),
          l => el('td', { 'data-etiquette': 'Nature' },
            selecteur('ligne', l.id, 'nature', l.nature,
              [['fixe', 'Fixe'], ['variable', 'Variable']], 'Nature')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Prévu' },
            champMontant('ligne', l.id, 'estime', l.estime, 'Montant prévu')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Réel' },
            champMontant('ligne', l.id, 'reel', l.reel, 'Montant réel')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Écart' }, celluleEcart(l)),
          l => el('td', { 'data-etiquette': 'Note' },
            champTexte('ligne', l.id, 'note', l.note,
              { placeholder: '—', etiquette: 'Note' })),
          l => el('td', { class: 'col-suppr' },
            boutonSupprimer('lignes', l.id, `la dépense ${l.libelle || 'sans nom'}`)),
        ]))))));
  }
}

/* -------------------------------------------------------- Vue revenus --- */

function dessineRevenus() {
  const lignes = etat.detail.lignes.filter(l =>
    l.type !== 'depense'
    && (etat.filtreRevenu === 'tout' || l.type === etat.filtreRevenu));

  const hote = $('#table-revenus');
  hote.textContent = '';

  if (!lignes.length) {
    hote.append(el('div', { class: 'vide', texte: 'Aucun revenu enregistré pour ce mois.' }));
    return;
  }

  hote.append(el('datalist', { id: 'categories-revenus' },
    listeCategories('revenu').map(c => el('option', { value: c }))));

  const ordre = [['salaire', 'fixe'], ['salaire', 'variable'], ['aide', 'fixe'], ['aide', 'variable']];
  const noms = { 'salaire-fixe': 'Salaires fixes', 'salaire-variable': 'Salaires variables',
                 'aide-fixe': 'Aides fixes', 'aide-variable': 'Aides variables' };

  for (const [type, nature] of ordre) {
    const membres = lignes.filter(l => l.type === type && l.nature === nature);
    if (!membres.length) continue;
    const totalPrevu = membres.reduce((s, l) => s + (l.actif ? Number(l.estime) : 0), 0);
    const totalReel = membres.reduce((s, l) => s + Number(l.reel), 0);

    hote.append(el('section', { class: 'groupe' },
      el('header', { class: 'groupe__entete' },
        el('span', { class: 'groupe__nom', texte: noms[`${type}-${nature}`] }),
        el('span', { class: 'groupe__total',
                     texte: `${euros(totalReel)} encaissés · ${euros(totalPrevu)} prévus` }),
        el('span', { class: 'pousse' }),
        el('button', {
          class: 'bouton bouton--fantome', texte: '+ Ligne',
          'data-ajouter': type, 'data-nature': nature,
        })),
      el('table', { class: 'lignes' },
        el('thead', {}, el('tr', {},
          el('th', { texte: 'Libellé' }), el('th', { texte: 'Type' }),
          el('th', { texte: 'Nature' }),
          el('th', { class: 'col-nombre', texte: 'Prévu' }),
          el('th', { class: 'col-nombre', texte: 'Réel' }),
          el('th', { class: 'col-nombre', texte: 'Écart' }),
          el('th', { texte: 'Lien' }), el('th', { texte: '' }))),
        el('tbody', {}, membres.map(ligne => ligneTableau(ligne, [
          l => el('td', { class: 'col-libelle', 'data-etiquette': 'Libellé' },
            champTexte('ligne', l.id, 'libelle', l.libelle,
              { placeholder: 'Source du revenu', etiquette: 'Libellé' })),
          l => el('td', { 'data-etiquette': 'Type' },
            selecteur('ligne', l.id, 'type', l.type,
              [['salaire', 'Salaire'], ['aide', 'Aide']], 'Type')),
          l => el('td', { 'data-etiquette': 'Nature' },
            selecteur('ligne', l.id, 'nature', l.nature,
              [['fixe', 'Fixe'], ['variable', 'Variable']], 'Nature')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Prévu' },
            champMontant('ligne', l.id, 'estime', l.estime, 'Montant prévu')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Réel' },
            champMontant('ligne', l.id, 'reel', l.reel, 'Montant réel')),
          l => el('td', { class: 'col-nombre', 'data-etiquette': 'Écart' }, celluleEcart(l)),
          l => el('td', { 'data-etiquette': 'Lien' },
            selecteur('ligne', l.id, 'lien', l.lien || '',
              Object.entries(LIENS), 'Total automatique relié à cette ligne')),
          l => el('td', { class: 'col-suppr' },
            boutonSupprimer('lignes', l.id, `le revenu ${l.libelle || 'sans nom'}`)),
        ]))))));
  }
}

/* -------------------------------------------------------- Vue courses --- */

function dessineCourses() {
  const { courses } = etat.detail.recap;
  $('#budget-courses').value = montantSaisi(etat.detail.mois.budget_courses);

  $('#resume-courses').replaceChildren(
    el('div', { class: 'resume-bandeau' },
      tuile('Dépensé', euros(courses.depense), `sur ${euros(courses.budget_total)} prévus`),
      tuile('Restant', euros(courses.restant),
            courses.restant >= 0 ? 'Encore disponible' : 'Dépassement',
            courses.restant >= 0 ? 'tuile__delta--bon' : 'tuile__delta--mauvais'),
      tuile('Semaines suivies', String(courses.semaines.length),
            `Budget cumulé ${euros(courses.budget_semaines)}`)),
    el('div', { class: 'carte' }, jauge('Budget du mois', courses.depense, courses.budget_total)));

  const hote = $('#semaines-courses');
  hote.textContent = '';
  hote.append(el('datalist', { id: 'postes-courses' },
    POSTES_COURANTS.map(p => el('option', { value: p }))));
  hote.append(el('datalist', { id: 'achats-courses' },
    ACHATS_COURANTS.map(a => el('option', { value: a }))));

  for (const semaine of courses.semaines) {
    const achats = etat.detail.achats.filter(a => a.semaine === semaine.numero);

    const corps = achats.length
      ? el('table', { class: 'lignes lignes--achats' },
          el('thead', {}, el('tr', {},
            el('th', { texte: 'Poste' }), el('th', { texte: 'Achat' }),
            el('th', { class: 'col-nombre', texte: 'Montant' }), el('th', { texte: '' }))),
          el('tbody', {}, achats.map(achat => el('tr', {}, [
            el('td', { 'data-etiquette': 'Poste' },
              champTexte('achat', achat.id, 'poste', achat.poste,
                { liste: 'postes-courses', placeholder: 'Marché…', etiquette: 'Poste' })),
            el('td', { class: 'col-libelle', 'data-etiquette': 'Achat' },
              champTexte('achat', achat.id, 'libelle', achat.libelle,
                { liste: 'achats-courses', placeholder: 'Article', etiquette: 'Achat' })),
            el('td', { class: 'col-nombre', 'data-etiquette': 'Montant' },
              champMontant('achat', achat.id, 'montant', achat.montant, 'Montant')),
            el('td', { class: 'col-suppr' },
              boutonSupprimer('achats', achat.id, `l’achat ${achat.libelle || 'sans nom'}`)),
          ]))))
      : el('div', { class: 'vide', texte: 'Rien pour cette semaine.' });

    hote.append(el('article', { class: 'carte' },
      el('header', { class: 'semaine__entete' },
        el('span', { class: 'semaine__titre', texte: `Semaine ${semaine.numero}` }),
        el('span', { class: 'pousse' }),
        el('label', { class: 'champ-inline' }, 'Budget',
          el('input', {
            type: 'text', inputmode: 'decimal', class: 'montant',
            value: montantSaisi(semaine.budget),
            'aria-label': `Budget de la semaine ${semaine.numero}`,
            'data-cle': `semaine-${semaine.numero}-budget`,
            'data-entite': 'semaine', 'data-id': semaine.numero, 'data-champ': 'budget',
          }))),
      jauge('Dépensé', semaine.depense, semaine.budget),
      el('div', { style: 'height:10px' }),
      corps,
      el('div', { class: 'puces' },
        el('button', {
          class: 'bouton bouton--fantome', texte: '+ Ajouter un achat',
          'data-ajouter-achat': semaine.numero,
        }),
        el('details', { class: 'suggestions' },
          el('summary', { texte: 'Ajout rapide' }),
          el('div', { class: 'puces' },
            ACHATS_COURANTS.map(nom => el('button', {
              class: 'puce', texte: nom,
              'data-ajouter-achat': semaine.numero, 'data-libelle': nom, 'data-poste': 'Marché',
            })))))));
  }
}

/* --------------------------------------------------------- Vue heures --- */

function dessineHeures() {
  const { heures } = etat.detail.recap;
  $('#taux-horaire').value = montantSaisi(etat.detail.mois.taux_horaire);
  $('#taux-cotisation').value = montantSaisi(etat.detail.mois.taux_cotisation);

  $('#resume-heures').replaceChildren(
    el('div', { class: 'resume-bandeau' },
      tuile('Heures gardées', heures.duree, `${heures.par_semaine.length} semaine(s) renseignée(s)`),
      tuile('Salaire brut', euros(heures.brut),
            `${heures.duree} × ${formatNombre.format(heures.taux_horaire)} €`),
      tuile('Cotisations', euros(heures.cotisation),
            `${formatNombre.format(heures.taux_cotisation)} % du brut`),
      tuile('Salaire net', euros(heures.net), 'Brut moins cotisations')));

  const parSemaine = new Map();
  for (const creneau of etat.detail.creneaux) {
    if (!parSemaine.has(creneau.semaine)) parSemaine.set(creneau.semaine, []);
    parSemaine.get(creneau.semaine).push(creneau);
  }

  const hote = $('#semaines-heures');
  hote.textContent = '';
  hote.classList.add('semaines--larges');

  for (const [numero, creneaux] of Array.from(parSemaine).sort((a, b) => a[0] - b[0])) {
    const minutes = creneaux.reduce((s, c) => s + c.minutes, 0);
    hote.append(el('article', { class: 'carte' },
      el('header', { class: 'semaine__entete' },
        el('span', { class: 'semaine__titre', texte: `Semaine ${numero}` }),
        el('span', { class: 'pousse' }),
        el('span', { class: 'groupe__total',
                     texte: minutes ? `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, '0')}` : '—' })),
      el('table', { class: 'lignes heures' },
        el('thead', {}, el('tr', {},
          el('th', { texte: 'Jour' }),
          el('th', { texte: 'Matin' }), el('th', { texte: '' }),
          el('th', { class: 'separateur', texte: 'Après-midi' }), el('th', { texte: '' }),
          el('th', { class: 'col-nombre', texte: 'Durée' }))),
        el('tbody', {}, creneaux.sort((a, b) => a.jour - b.jour).map(creneau => el('tr', {}, [
          el('td', { class: 'jour', texte: JOURS[creneau.jour] }),
          celluleHeure(creneau, 'matin_debut', `${JOURS[creneau.jour]} matin, début`),
          celluleHeure(creneau, 'matin_fin', `${JOURS[creneau.jour]} matin, fin`),
          celluleHeure(creneau, 'aprem_debut', `${JOURS[creneau.jour]} après-midi, début`, true),
          celluleHeure(creneau, 'aprem_fin', `${JOURS[creneau.jour]} après-midi, fin`),
          el('td', { class: 'duree', texte: creneau.duree || '—' }),
        ]))))));
  }
}

function celluleHeure(creneau, champ, etiquette, separateur) {
  return el('td', { class: separateur ? 'separateur' : null, 'data-etiquette': etiquette },
    el('input', {
      type: 'text', inputmode: 'numeric', value: creneau[champ] || '', placeholder: '--:--',
      'aria-label': etiquette,
      'data-cle': `creneau-${creneau.id}-${champ}`,
      'data-entite': 'creneau', 'data-id': creneau.id, 'data-champ': champ,
    }));
}

/* ------------------------------------------------------- Interactions --- */

const CHEMINS = {
  ligne: (id) => `/api/lignes/${id}`,
  achat: (id) => `/api/achats/${id}`,
  creneau: (id) => `/api/creneaux/${id}`,
  semaine: (id) => `/api/mois/${etat.moisId}/semaines/${id}`,
};

document.addEventListener('change', async (evenement) => {
  const cible = evenement.target;

  if (cible.id === 'choix-mois') return chargeMois(Number(cible.value));
  if (cible.id === 'masquer-pause') { etat.masquerPause = cible.checked; return dessineDepenses(); }
  if (cible.id === 'fichier-import') return importeFichier(cible.files[0]);

  if (['budget-courses', 'taux-horaire', 'taux-cotisation'].includes(cible.id)) {
    const champ = { 'budget-courses': 'budget_courses', 'taux-horaire': 'taux_horaire',
                    'taux-cotisation': 'taux_cotisation' }[cible.id];
    return agis(api('PATCH', `/api/mois/${etat.moisId}`, { [champ]: cible.value }), 'Enregistré');
  }

  const { entite, id, champ } = cible.dataset;
  if (!entite || !champ) return;
  const valeur = cible.type === 'checkbox' ? cible.checked : cible.value;
  await agis(api('PATCH', CHEMINS[entite](id), { [champ]: valeur }), 'Enregistré');
});

/* Retour immédiat sur l'écart pendant la frappe, avant l'enregistrement. */
document.addEventListener('input', (evenement) => {
  const cible = evenement.target;
  if (cible.dataset.entite !== 'ligne') return;
  if (!['estime', 'reel'].includes(cible.dataset.champ)) return;
  const tr = cible.closest('tr');
  const cellule = tr && tr.querySelector('.ecart');
  if (!cellule) return;
  const lit = (nom) => {
    const champ = tr.querySelector(`[data-champ="${nom}"]`);
    return Number(String(champ ? champ.value : '0').replace(/\s/g, '').replace(',', '.')) || 0;
  };
  const bascule = tr.querySelector('[data-champ="actif"]');
  const ecart = (!bascule || bascule.checked ? lit('estime') : 0) - lit('reel');
  cellule.textContent = ecart === 0 ? '—' : signe(ecart);
  cellule.className = 'ecart ' + (ecart > 0.004 ? 'ecart--bon' : (ecart < -0.004 ? 'ecart--mauvais' : ''));
});

document.addEventListener('click', async (evenement) => {
  const cible = evenement.target.closest('button, [data-vue]');
  if (!cible) return;

  if (cible.dataset.vue) return montreVue(cible.dataset.vue);

  if (cible.dataset.filtreNature) {
    etat.filtreNature = cible.dataset.filtreNature;
    $$('[data-filtre-nature]').forEach(b => b.classList.toggle('actif', b === cible));
    return dessineDepenses();
  }
  if (cible.dataset.filtreRevenu) {
    etat.filtreRevenu = cible.dataset.filtreRevenu;
    $$('[data-filtre-revenu]').forEach(b => b.classList.toggle('actif', b === cible));
    return dessineRevenus();
  }

  if (cible.dataset.ajouter) return ajouteLigne(cible);
  if (cible.dataset.ajouterAchat) return ajouteAchat(cible);
  if (cible.dataset.supprimer) return supprime(cible);
  if (cible.dataset.report) return reporte(cible.dataset.report);
  if (cible.dataset.action) return actionMenu(cible.dataset.action);

  if (cible.id === 'btn-nouveau-mois') return nouveauMois();
  if (cible.id === 'btn-mois-precedent') return changeMoisRelatif(-1);
  if (cible.id === 'btn-mois-suivant') return changeMoisRelatif(1);
  if (cible.id === 'btn-ajouter-semaine') {
    return agis(api('POST', `/api/mois/${etat.moisId}/semaines`), 'Semaine ajoutée');
  }
  if (cible.id === 'btn-retirer-semaine') {
    const semaines = etat.detail.semaines;
    const derniere = semaines[semaines.length - 1];
    if (!derniere) return;
    if (!confirm(`Supprimer la semaine ${derniere.numero} et tout ce qu'elle contient ?`)) return;
    return agis(api('DELETE', `/api/mois/${etat.moisId}/semaines/${derniere.numero}`),
                'Semaine supprimée');
  }
});

$('#recherche-depenses').addEventListener('input', (evenement) => {
  etat.recherche = evenement.target.value;
  dessineDepenses();
});

/* Entrée valide la saisie ; Échap annule la modification en cours. */
document.addEventListener('keydown', (evenement) => {
  if (!evenement.target.dataset || !evenement.target.dataset.champ) return;
  if (evenement.key === 'Enter') { evenement.preventDefault(); evenement.target.blur(); }
  if (evenement.key === 'Escape') { dessineTout(); }
});

/* ------------------------------------------------------------- Actions --- */

async function ajouteLigne(bouton) {
  const type = bouton.dataset.ajouter;
  const corps = {
    type,
    nature: bouton.dataset.nature || (type === 'depense' ? etat.filtreNature : 'variable'),
    categorie: bouton.dataset.categorie
      || (type === 'depense' ? '' : (type === 'aide' ? 'Aide' : 'Salaire')),
  };
  if (corps.nature === 'tout') corps.nature = 'variable';

  const resultat = await agis(api('POST', `/api/mois/${etat.moisId}/lignes`, corps), 'Ligne ajoutée');
  if (!resultat) return;
  montreVue(type === 'depense' ? 'depenses' : 'revenus');
  const champ = document.querySelector(`[data-cle="ligne-${resultat.nouvel_id}-libelle"]`);
  if (champ) { champ.focus(); champ.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
}

async function ajouteAchat(bouton) {
  const resultat = await agis(api('POST', `/api/mois/${etat.moisId}/achats`, {
    semaine: Number(bouton.dataset.ajouterAchat),
    libelle: bouton.dataset.libelle || '',
    poste: bouton.dataset.poste || '',
  }), 'Achat ajouté');
  if (!resultat) return;
  const cle = bouton.dataset.libelle
    ? `achat-${resultat.nouvel_id}-montant` : `achat-${resultat.nouvel_id}-libelle`;
  const champ = document.querySelector(`[data-cle="${cle}"]`);
  if (champ) champ.focus();
}

async function supprime(bouton) {
  const entite = bouton.dataset.supprimer;
  const id = Number(bouton.dataset.id);
  const source = entite === 'lignes'
    ? etat.detail.lignes.find(l => l.id === id)
    : etat.detail.achats.find(a => a.id === id);

  const resultat = await agis(api('DELETE', `/api/${entite}/${id}`));
  if (!resultat || !source) return;

  const copie = { ...source };
  delete copie.id; delete copie.mois_id;
  toast('Ligne supprimée.', {
    action: {
      libelle: 'Annuler',
      faire: () => agis(
        api('POST', `/api/mois/${etat.moisId}/${entite === 'lignes' ? 'lignes' : 'achats'}`, copie),
        'Ligne rétablie'),
    },
  });
}

async function reporte(cible) {
  const resultat = await agis(api('POST', `/api/mois/${etat.moisId}/report/${cible}`));
  if (resultat) {
    toast(cible === 'courses'
      ? 'Total des courses reporté dans la ligne de dépense reliée.'
      : 'Salaire net reporté dans la ligne de revenu reliée.');
  }
}

async function nouveauMois() {
  const propose = decaleMois(etat.detail.mois.libelle, 1);
  const saisi = prompt(
    'Quel mois créer ? (format AAAA-MM)\n\n'
    + 'Les lignes récurrentes du mois affiché sont recopiées, '
    + 'avec les montants réels remis à zéro.', propose);
  if (!saisi) return;
  await agis(api('POST', '/api/mois',
    { libelle: saisi.trim(), copier_de: etat.moisId }), 'Mois créé');
}

async function changeMoisRelatif(pas) {
  const cible = decaleMois(etat.detail.mois.libelle, pas);
  const existant = (etat.detail.mois_disponibles || []).find(m => m.libelle === cible);
  if (existant) return chargeMois(existant.id);
  if (!confirm(`${libelleMois(cible)} n'existe pas encore. Le créer à partir du mois affiché ?`)) return;
  await agis(api('POST', '/api/mois', { libelle: cible, copier_de: etat.moisId }), 'Mois créé');
}

async function actionMenu(action) {
  $$('.menu[open]').forEach(m => m.removeAttribute('open'));

  if (action === 'export-csv') {
    window.location.href = `/api/mois/${etat.moisId}/export.csv`;
    return;
  }
  if (action === 'export-json') {
    const donnees = await api('GET', '/api/export.json');
    const lien = el('a', {
      href: URL.createObjectURL(new Blob([JSON.stringify(donnees, null, 2)],
        { type: 'application/json' })),
      download: `comptes-sauvegarde-${new Date().toISOString().slice(0, 10)}.json`,
    });
    lien.click();
    URL.revokeObjectURL(lien.href);
    return;
  }
  if (action === 'import-json') return $('#fichier-import').click();
  if (action === 'theme') return changeTheme();
  if (action === 'supprimer-mois') {
    if (!confirm(`Supprimer définitivement ${libelleMois(etat.detail.mois.libelle)} `
                 + 'et toutes ses données ?')) return;
    const restant = await api('DELETE', `/api/mois/${etat.moisId}`);
    if (restant.mois_actif_id) return chargeMois(restant.mois_actif_id);
    await agis(api('POST', '/api/mois', {}), 'Nouveau mois créé');
  }
}

async function importeFichier(fichier) {
  if (!fichier) return;
  try {
    const donnees = JSON.parse(await fichier.text());
    const resultat = await api('POST', '/api/import', donnees);
    toast(resultat.importes
      ? `${resultat.importes} mois restauré(s). Les mois déjà présents ont été conservés.`
      : 'Aucun mois nouveau à restaurer.');
    if (resultat.mois_actif_id) await chargeMois(resultat.mois_actif_id);
  } catch (erreur) {
    toast(`Fichier illisible : ${erreur.message}`, { erreur: true });
  } finally {
    $('#fichier-import').value = '';
  }
}

function changeTheme() {
  const suite = { auto: 'light', light: 'dark', dark: 'auto' };
  const actuel = document.documentElement.dataset.theme || 'auto';
  appliqueTheme(suite[actuel]);
}

function appliqueTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $('#etat-theme').textContent = { auto: 'auto', light: 'clair', dark: 'sombre' }[theme];
  try { localStorage.setItem('comptes.theme', theme); } catch { /* ignoré */ }
  if (etat.detail) dessineGraphiqueCategories();
}

/* ------------------------------------------------------------ Démarrage --- */

async function chargeMois(moisId) {
  try {
    applique(await api('GET', `/api/mois/${moisId}`));
  } catch (erreur) {
    toast(erreur.message, { erreur: true });
  }
}

let minuteurRedimension = null;
window.addEventListener('resize', () => {
  clearTimeout(minuteurRedimension);
  minuteurRedimension = setTimeout(() => {
    if (etat.vue === 'tableau') dessineGraphiqueCategories();
  }, 180);
});

document.addEventListener('click', (evenement) => {
  if (!evenement.target.closest('.menu')) {
    $$('.menu[open]').forEach(m => m.removeAttribute('open'));
  }
});

(async function demarre() {
  let theme = 'auto', vue = 'tableau', moisMemorise = null;
  try {
    theme = localStorage.getItem('comptes.theme') || 'auto';
    vue = localStorage.getItem('comptes.vue') || 'tableau';
    moisMemorise = Number(localStorage.getItem('comptes.mois')) || null;
  } catch { /* stockage indisponible */ }
  appliqueTheme(theme);

  try {
    const initial = await api('GET', '/api/etat');
    const disponibles = initial.mois.map(m => m.id);
    const choisi = disponibles.includes(moisMemorise) ? moisMemorise : initial.mois_actif_id;
    if (!choisi) {
      applique(await api('POST', '/api/mois', {}));
    } else {
      applique(await api('GET', `/api/mois/${choisi}`));
    }
    montreVue(location.hash.slice(1) || vue);
  } catch (erreur) {
    toast(`Impossible de charger les données : ${erreur.message}`, { erreur: true, duree: 20000 });
  }
})();
