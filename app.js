'use strict';

const ARCHIVE_BATCH_SIZE = 24;

const SCENE_FILTER_PROFILES = {
  underwater: { sceneCategory: 'Underwater' },
  'aerial-landscape': {
    sceneCategories: ['Aerial', 'Landscape'],
    categories: ['Coastal Landscapes Drone Aerials'],
  },
  'cultural-editorial': {
    sceneCategories: ['Culture'],
    categories: ['Indo-Pacific Cultural Documentations & Editorial Scenes'],
  },
  'terrestrial-wildlife': {
    categories: [
      'Terrestrial Mammals, Marsupials & Megafauna',
      'Terrestrial Reptiles & Herpetofauna',
      'Avian Bird Species',
    ],
  },
};

const SEARCH_STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
  'by', 'from', 'into', 'over', 'under', 'between', 'through', 'during', 'before',
  'after', 'above', 'below', 'near', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
  'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'as',
]);

function singularizeSearchToken(token) {
  if (token.length <= 3) return token;
  if (token.endsWith('ies') && token.length > 4) return `${token.slice(0, -3)}y`;
  if (token.endsWith('es') && token.length > 4) return token.slice(0, -2);
  if (token.endsWith('s') && !token.endsWith('ss')) return token.slice(0, -1);
  return token;
}

function searchTokenVariants(token) {
  const variants = new Set([token]);
  const singular = singularizeSearchToken(token);
  variants.add(singular);
  if (!token.endsWith('s')) variants.add(`${token}s`);
  if (singular !== token && !singular.endsWith('s')) variants.add(`${singular}s`);
  return [...variants];
}

function searchTokenMatchesText(text, token) {
  return searchTokenVariants(token).some((variant) => {
    if (variant.length <= 2) return text.split(/\s+/).includes(variant);
    return text.includes(variant);
  });
}

function damerauLevenshtein(a, b) {
  const alen = a.length;
  const blen = b.length;
  if (alen === 0) return blen;
  if (blen === 0) return alen;

  const maxDist = alen + blen;
  const da = Object.create(null);
  const d = Array.from({ length: alen + 2 }, () => Array(blen + 2).fill(0));

  d[0][0] = maxDist;
  for (let i = 0; i <= alen; i += 1) {
    d[i + 1][0] = maxDist;
    d[i + 1][1] = i;
  }
  for (let j = 0; j <= blen; j += 1) {
    d[0][j + 1] = maxDist;
    d[1][j + 1] = j;
  }

  for (let i = 1; i <= alen; i += 1) {
    let db = 0;
    for (let j = 1; j <= blen; j += 1) {
      const i1 = da[b[j - 1]] || 0;
      const j1 = db;
      let cost = 1;
      if (a[i - 1] === b[j - 1]) {
        cost = 0;
        db = j;
      }
      d[i + 1][j + 1] = Math.min(
        d[i][j + 1] + 1,
        d[i + 1][j] + 1,
        d[i][j] + cost,
        d[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1),
      );
    }
    da[a[i - 1]] = i;
  }

  return d[alen + 1][blen + 1];
}

function maxFuzzyEditDistance(tokenLength) {
  if (tokenLength <= 4) return 1;
  if (tokenLength <= 8) return 2;
  return 2;
}

function tokenLooksLikeVocabularyTerm(token, vocabulary) {
  return searchTokenVariants(token).some((variant) => vocabulary.has(variant));
}

function findFuzzyVocabularyMatches(token, vocabulary) {
  if (!token || token.length < 3 || !vocabulary || vocabulary.size === 0) return [];

  const maxDistance = maxFuzzyEditDistance(token.length);
  const matches = [];

  vocabulary.forEach((term) => {
    if (Math.abs(term.length - token.length) > maxDistance) return;
    if (token.length <= 6 && term[0] !== token[0]) return;

    const distance = damerauLevenshtein(token, term);
    if (distance === 0 || distance > maxDistance) return;

    matches.push({ term, distance });
  });

  matches.sort((a, b) => a.distance - b.distance || a.term.length - b.term.length);
  return matches.map((entry) => entry.term);
}

function suggestFuzzyCorrection(token, vocabulary) {
  if (!token || token.length < 3 || !vocabulary || vocabulary.size === 0) return null;
  if (tokenLooksLikeVocabularyTerm(token, vocabulary)) return null;

  const matches = findFuzzyVocabularyMatches(token, vocabulary);
  return matches[0] || null;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function buildCorrectedQueryDisplay(query, corrections) {
  let result = query;
  corrections.forEach(({ from, to }) => {
    const pattern = new RegExp(`(^|[^a-z0-9])(${escapeRegExp(from)})(?=[^a-z0-9]|$)`, 'gi');
    result = result.replace(pattern, (_, prefix, match) => `${prefix}${match === match.toUpperCase() ? to.toUpperCase() : to}`);
  });
  return result;
}

const SEARCH_PARTIAL_MIN_LEN = 3;

function cleanSearchToken(token) {
  return token.replace(/^[^a-z0-9]+|[^a-z0-9]+$/gi, '').toLowerCase();
}

function significantSearchTokens(query) {
  const hasTrailingSpace = /\s$/.test(query);
  const parts = String(query || '').toLowerCase().split(/\s+/);
  let tokens = parts
    .map(cleanSearchToken)
    .filter((token) => token.length > 0 && !SEARCH_STOP_WORDS.has(token));

  // While typing a multi-word phrase, don't require the in-progress last word yet.
  if (!hasTrailingSpace && tokens.length > 1) {
    const lastRaw = cleanSearchToken(parts[parts.length - 1] || '');
    const lastToken = tokens[tokens.length - 1];

    if (lastRaw === lastToken && lastToken.length < SEARCH_PARTIAL_MIN_LEN) {
      tokens = tokens.slice(0, -1);
    }
  }

  return tokens;
}

function matchesSearchQuery(haystack, query, tokensOverride) {
  const text = String(haystack || '').toLowerCase();
  const raw = String(query || '');
  const normalized = raw.trim().toLowerCase();
  if (!normalized) return true;

  const quoted = normalized.match(/^"(.+)"$/);
  if (quoted) {
    return text.includes(quoted[1].trim());
  }

  if (text.includes(normalized)) return true;

  const tokens = Array.isArray(tokensOverride) && tokensOverride.length > 0
    ? tokensOverride
    : significantSearchTokens(raw);
  if (tokens.length === 0) return true;

  return tokens.every((token) => searchTokenMatchesText(text, token));
}

function buildSearchVocabulary(assets) {
  const terms = new Set();

  assets.forEach((asset) => {
    collectAssetVocabulary(asset).forEach((term) => terms.add(term));

    String(asset.slug || '')
      .split('-')
      .map(cleanSearchToken)
      .filter((part) => part.length >= 3 && !SEARCH_STOP_WORDS.has(part))
      .forEach((part) => terms.add(part));

    String(asset.region || '')
      .split(/[,/&]+/)
      .map(cleanSearchToken)
      .filter((part) => part.length >= 3 && !SEARCH_STOP_WORDS.has(part))
      .forEach((part) => terms.add(part));
  });

  Object.values(BROAD_CATEGORY_TAXONOMY_TERMS)
    .flat()
    .map(cleanSearchToken)
    .filter((term) => term.length >= 3)
    .forEach((term) => terms.add(term));

  return terms;
}

const CATEGORY_TERM_BLOCKLIST = new Set([
  'indonesia', 'pacific', 'ocean', 'national', 'park', 'underwater', 'marine',
  'footage', 'sequence', 'documenting', 'history', 'natural', 'stock', 'clip',
  'video', 'camera', 'native', 'format', 'rights', 'managed',
]);

const BROAD_CATEGORY_TAXONOMY_TERMS = {
  'Pelagic & Open Ocean Schooling Fish': ['pelagic', 'open ocean', 'schooling fish', 'blue water', 'barracuda'],
  'Benthic Reef Aggregations & Schooling Fish': ['benthic', 'schooling', 'sweetlips', 'ribbon', 'sweeper', 'golden', 'fusilier', 'batfish', 'aggregation'],
  'Small Fish Life & Cryptic Bottom-Dwellers': ['goby', 'blenny', 'cryptic', 'bottom-dweller'],
  'Apex Marine Predators & Elasmobranchii': ['shark', 'whitetip', 'manta', 'elasmobranch', 'triaenodon', 'predator'],
  'Marine Megafauna, Reptiles & Ocean Mammals': ['turtle', 'hawksbill', 'chelonia', 'eretmochelys', 'dolphin', 'whale', 'megafauna', 'reptile'],
  'Cephalopods': ['octopus', 'cephalopod', 'squid', 'cuttlefish'],
  'Mollusks': ['mollusk', 'nudibranch', 'clam', 'snail'],
  'Marine Habitats, Sponges & Corals': [
    'coral', 'corals', 'sponge', 'sponges', 'acropora', 'gorgonian', 'seafan',
    'barrel sponge', 'table coral', 'soft coral', 'hard coral', 'reef habitat',
  ],
  'Reef Associated Fish': ['reef fish', 'moorish idol', 'zanclus', 'angelfish', 'anthias', 'butterflyfish', 'damselfish', 'wrasse'],
  'Pipefish/Seahorses': ['pipefish', 'seahorse', 'syngnathidae'],
  'Crustaceans and Misc Macro Life': ['shrimp', 'crab', 'crustacean', 'macro'],
  'Worms and Echinoderms': ['worm', 'polychaete', 'starfish', 'urchin', 'echinoderm', 'sea cucumber', 'brittle star', 'feather star'],
  'Terrestrial Mammals, Marsupials & Megafauna': ['kangaroo', 'wallaby', 'marsupial', 'orangutan', 'babirusa', 'terrestrial mammal'],
  'Terrestrial Reptiles & Herpetofauna': ['komodo dragon', 'varanus', 'python', 'cobra', 'snake', 'herpetofauna', 'monitor lizard'],
  'Avian Bird Species': ['bird', 'avian', 'eagle', 'hornbill', 'parrot', 'kingfisher', 'seabird', 'cockatoo', 'heron', 'pelican'],
  'Coastal Landscapes Drone Aerials': ['aerial', 'drone', 'landscape', 'coastal', 'scenery', 'sunset', 'sunray', 'seascape'],
  'Indo-Pacific Cultural Documentations & Editorial Scenes': ['culture', 'cultural', 'village', 'editorial'],
};

function extractSignificantTerms(text) {
  const terms = new Set();
  String(text || '')
    .toLowerCase()
    .replace(/[^\w\s-]/g, ' ')
    .split(/\s+/)
    .map(cleanSearchToken)
    .filter((token) => token.length >= 3 && !SEARCH_STOP_WORDS.has(token) && !CATEGORY_TERM_BLOCKLIST.has(token))
    .forEach((token) => terms.add(token));
  return terms;
}

function tokenizeCategoryLabel(category) {
  return extractSignificantTerms(String(category || '').replace(/&/g, ' ').replace(/,/g, ' '));
}

function collectAssetVocabulary(asset) {
  const terms = new Set();
  const spec = asset.technicalSpecs || {};
  const fields = [
    asset.title,
    asset.description,
    asset.species,
    spec.family,
    spec.latinName,
  ];

  fields.filter(Boolean).forEach((text) => {
    extractSignificantTerms(text).forEach((term) => terms.add(term));
  });

  if (Array.isArray(asset.keywords)) {
    asset.keywords.forEach((keyword) => {
      const phrase = String(keyword).trim().toLowerCase();
      if (!phrase || phrase.length < 3) return;
      if (!SEARCH_STOP_WORDS.has(phrase) && !CATEGORY_TERM_BLOCKLIST.has(phrase)) {
        terms.add(phrase);
      }
      extractSignificantTerms(phrase).forEach((term) => terms.add(term));
    });
  }

  return terms;
}

function buildCategoryTermIndex(assets) {
  const index = {};
  const globalTermCounts = new Map();
  const categoryTermCounts = {};

  const addTerm = (category, term, { force = false } = {}) => {
    if (!category || !term) return;
    const normalized = String(term).trim().toLowerCase();
    if (normalized.length < 3) return;
    if (!force && (SEARCH_STOP_WORDS.has(normalized) || CATEGORY_TERM_BLOCKLIST.has(normalized))) return;
    if (!index[category]) index[category] = new Set();
    index[category].add(normalized);
  };

  const assetTerms = assets.map((asset) => ({
    category: asset.category || '',
    terms: collectAssetVocabulary(asset),
  }));

  assetTerms.forEach(({ terms }) => {
    terms.forEach((term) => {
      globalTermCounts.set(term, (globalTermCounts.get(term) || 0) + 1);
    });
  });

  assetTerms.forEach(({ category, terms }) => {
    if (!category) return;
    if (!categoryTermCounts[category]) categoryTermCounts[category] = new Map();
    terms.forEach((term) => {
      categoryTermCounts[category].set(
        term,
        (categoryTermCounts[category].get(term) || 0) + 1,
      );
    });
  });

  const totalAssets = assets.length;
  const maxUbiquitous = Math.max(3, Math.ceil(totalAssets * 0.22));

  Object.entries(categoryTermCounts).forEach(([category, termCounts]) => {
    termCounts.forEach((inCategoryCount, term) => {
      const globalCount = globalTermCounts.get(term) || 0;
      const outsideCount = globalCount - inCategoryCount;
      const categoryShare = inCategoryCount / globalCount;
      const distinctive = inCategoryCount >= 1
        && globalCount <= maxUbiquitous
        && (outsideCount === 0 || categoryShare >= 0.55);

      if (distinctive) addTerm(category, term);
    });

    tokenizeCategoryLabel(category).forEach((term) => addTerm(category, term, { force: true }));
  });

  Object.entries(BROAD_CATEGORY_TAXONOMY_TERMS).forEach(([category, extras]) => {
    extras.forEach((term) => addTerm(category, term, { force: true }));
  });

  return index;
}

function matchesBroadCategory(card, selectedCategory, getCardSearchText, categoryTermIndex) {
  if (!selectedCategory || selectedCategory === 'Any') return true;
  if (card.dataset.category === selectedCategory) return true;

  const terms = categoryTermIndex?.[selectedCategory];
  if (!terms || terms.size === 0) {
    return card.dataset.category === selectedCategory;
  }

  const haystack = typeof getCardSearchText === 'function'
    ? getCardSearchText(card)
    : '';

  return [...terms].some((term) => searchTokenMatchesText(haystack, term));
}

/**
 * Multi-tier taxonomic filter engine with cascading dependency chain.
 */
class TaxonomicFilterEngine {
  constructor(selectElements, onChange, options = {}) {
    this.onChange = onChange;
    this.getCardSearchText = options.getCardSearchText || null;
    this.assets = [];
    this.categoryTermIndex = {};
    this.chain = [
      {
        field: 'category',
        label: 'Broad Category',
        select: selectElements.taxaCategory,
        read: (asset) => asset.category || '',
      },
    ];

    this.values = Object.fromEntries(this.chain.map(({ field }) => [field, 'Any']));

    this.chain.forEach((_, index) => {
      this.chain[index].select.addEventListener('change', () => this.handleChange(index));
    });
  }

  setAssets(assets) {
    this.assets = Array.isArray(assets) ? assets : [];
    this.categoryTermIndex = buildCategoryTermIndex(this.assets);
    this.syncAllDropdowns(0);
  }

  getPool(beforeLevel) {
    return this.assets.filter((asset) => {
      for (let i = 0; i < beforeLevel; i += 1) {
        const { field, read } = this.chain[i];
        const selected = this.values[field];
        if (selected === 'Any') continue;
        const value = read(asset);
        if (!value || value !== selected) return false;
      }
      return true;
    });
  }

  collectOptions(levelIndex) {
    const { read } = this.chain[levelIndex];
    const pool = this.getPool(levelIndex);
    const options = new Set();

    pool.forEach((asset) => {
      const value = read(asset);
      if (value) options.add(value);
    });

    return [...options].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  }

  renderDropdown(levelIndex) {
    const { field, label, select } = this.chain[levelIndex];
    const options = this.collectOptions(levelIndex);
    const current = this.values[field];
    const placeholder = `${label}: Any`;

    select.innerHTML = '';
    const defaultOption = document.createElement('option');
    defaultOption.value = 'Any';
    defaultOption.textContent = placeholder;
    select.appendChild(defaultOption);

    options.forEach((value) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });

    if (current !== 'Any' && !options.includes(current)) {
      this.values[field] = 'Any';
      select.value = 'Any';
    } else {
      select.value = current;
    }

    select.disabled = options.length === 0 && levelIndex > 0;
  }

  syncAllDropdowns(fromLevel = 0) {
    for (let i = fromLevel; i < this.chain.length; i += 1) {
      this.renderDropdown(i);
    }
  }

  handleChange(changedIndex) {
    const { field, select } = this.chain[changedIndex];
    this.values[field] = select.value;

    for (let i = changedIndex + 1; i < this.chain.length; i += 1) {
      const downstream = this.chain[i].field;
      this.values[downstream] = 'Any';
      this.chain[i].select.value = 'Any';
    }

    this.syncAllDropdowns(changedIndex + 1);
    this.onChange();
  }

  reset() {
    this.chain.forEach(({ field, select }) => {
      this.values[field] = 'Any';
      select.value = 'Any';
    });
    this.syncAllDropdowns(0);
  }

  setCategory(value) {
    const select = this.chain[0].select;
    this.values.category = value || 'Any';
    select.value = this.values.category;
    for (let i = 1; i < this.chain.length; i += 1) {
      const downstream = this.chain[i].field;
      this.values[downstream] = 'Any';
      this.chain[i].select.value = 'Any';
    }
    this.syncAllDropdowns(1);
  }

  matchesCard(card) {
    return this.chain.every(({ field }) => {
      const selected = this.values[field];
      if (selected === 'Any') return true;

      if (field === 'category') {
        return matchesBroadCategory(
          card,
          selected,
          this.getCardSearchText,
          this.categoryTermIndex,
        );
      }
      if (field === 'species') return card.dataset.species === selected;
      if (field === 'family') return card.dataset.family === selected;
      if (field === 'latinName') return card.dataset.latinName === selected;
      return true;
    });
  }
}

class ArchiveGridPaginator {
  constructor({ grid, loadMoreBtn, batchSize, getFilteredCards, onRenderComplete, onCardsAppended }) {
    this.grid = grid;
    this.loadMoreBtn = loadMoreBtn;
    this.batchSize = batchSize;
    this.getFilteredCards = getFilteredCards;
    this.onRenderComplete = onRenderComplete;
    this.onCardsAppended = onCardsAppended;
    this.displayedCount = 0;

    this.loadMoreBtn.addEventListener('click', () => this.loadMore());
  }

  showEmptyState() {
    const empty = document.createElement('div');
    empty.className = 'empty-state';
    empty.innerHTML = '<strong>No clips found</strong>Try a different search term or adjust your filters.';
    this.grid.appendChild(empty);
  }

  resetAndRender() {
    const filtered = this.getFilteredCards();
    const scrollY = window.scrollY;
    this.displayedCount = 0;
    this.grid.innerHTML = '';
    this.grid.removeAttribute('aria-busy');

    if (filtered.length === 0) {
      this.showEmptyState();
      this.updateLoadMore(0);
      if (typeof this.onRenderComplete === 'function') {
        this.onRenderComplete(0, 0);
      }
      return;
    }

    this.appendBatch(filtered);
    this.updateLoadMore(filtered.length);
    window.scrollTo(0, scrollY);

    if (typeof this.onRenderComplete === 'function') {
      this.onRenderComplete(filtered.length, this.displayedCount);
    }
  }

  loadMore() {
    const filtered = this.getFilteredCards();
    const prevHeight = document.documentElement.scrollHeight;
    this.appendBatch(filtered);
    this.updateLoadMore(filtered.length);

    if (typeof this.onRenderComplete === 'function') {
      this.onRenderComplete(filtered.length, this.displayedCount);
    }

    const heightDelta = document.documentElement.scrollHeight - prevHeight;
    if (heightDelta > 0) {
      window.scrollBy({ top: Math.min(heightDelta * 0.15, 120), behavior: 'smooth' });
    }
  }

  appendBatch(filtered) {
    const slice = filtered.slice(this.displayedCount, this.displayedCount + this.batchSize);
    const fragment = document.createDocumentFragment();
    slice.forEach((card) => fragment.appendChild(card));
    this.grid.appendChild(fragment);
    this.displayedCount += slice.length;

    if (typeof this.onCardsAppended === 'function') {
      this.onCardsAppended(slice);
    }
  }

  updateLoadMore(totalFiltered) {
    const remaining = totalFiltered - this.displayedCount;
    if (totalFiltered === 0) {
      this.loadMoreBtn.hidden = true;
      this.loadMoreBtn.disabled = true;
      return;
    }

    this.loadMoreBtn.hidden = false;
    this.loadMoreBtn.disabled = remaining <= 0;
    this.loadMoreBtn.textContent = remaining > 0
      ? `[ Load More Cinematic Assets ] (${remaining} remaining)`
      : '[ All Premier Assets Loaded ]';
  }
}

class CollectionPortal {
  constructor({ rail, onSelect }) {
    this.tiles = [...rail.querySelectorAll('.collection-tile')];
    this.onSelect = onSelect;

    this.tiles.forEach((tile) => {
      tile.addEventListener('click', () => {
        const raw = tile.getAttribute('data-collection-filter');
        let filter = {};
        try {
          filter = JSON.parse(raw);
        } catch (err) {
          console.warn('Invalid collection filter', err);
        }
        this.setActiveTile(tile);
        this.onSelect(filter);
      });
    });
  }

  setActiveTile(activeTile) {
    this.tiles.forEach((tile) => {
      tile.classList.toggle('is-active', tile === activeTile);
    });
  }

  clearActiveTiles() {
    this.tiles.forEach((tile) => tile.classList.remove('is-active'));
  }
}

class CatalogFilterController {
  constructor(config) {
    this.getCards = config.getCards;
    this.getAssetCatalog = config.getAssetCatalog;
    this.searchInput = config.searchInput;
    this.filterRegion = config.filterRegion;
    this.filterScene = config.filterScene;
    this.filterTier = config.filterTier;
    this.grid = config.grid;
    this.resultsCount = config.resultsCount;
    this.loadMoreBtn = config.loadMoreBtn;
    this.cardSearchText = config.cardSearchText;
    this.zoneShowcase = config.zoneShowcase;
    this.zoneCollections = config.zoneCollections;

    this.collectionPortal = null;
    this.activeCollectionFilter = null;
    this.searchVocabulary = new Set();
    this._searchResolutionCache = { query: '', resolution: null };

    this.taxonomy = new TaxonomicFilterEngine(
      config.taxonomicSelects,
      () => this.filterArchive(),
      { getCardSearchText: config.cardSearchText },
    );

    this.paginator = new ArchiveGridPaginator({
      grid: this.grid,
      loadMoreBtn: this.loadMoreBtn,
      batchSize: config.batchSize || ARCHIVE_BATCH_SIZE,
      getFilteredCards: () => this.getFilteredCards(),
      onRenderComplete: (total, shown) => this.updateResultsCount(total, shown),
      onCardsAppended: config.onCardsAppended,
    });
  }

  initCollectionPortal(rail) {
    this.collectionPortal = new CollectionPortal({
      rail,
      onSelect: (filter) => this.applyCollectionFilter(filter),
    });

    const clearCollectionHighlight = () => {
      this.activeCollectionFilter = null;
      this.collectionPortal.clearActiveTiles();
    };

    const inputs = [
      this.searchInput,
      this.filterRegion,
      this.filterScene,
      this.filterTier,
      ...this.taxonomy.chain.map((item) => item.select),
    ].filter(Boolean);
    inputs.forEach((el) => {
      el.addEventListener('change', clearCollectionHighlight);
      el.addEventListener('input', clearCollectionHighlight);
    });
  }

  initTaxonomyFromCatalog() {
    const assets = [...this.getAssetCatalog().values()];
    this.taxonomy.setAssets(assets);
    this.searchVocabulary = buildSearchVocabulary(assets);
    this._searchResolutionCache = { query: '', resolution: null };
  }

  getSearchResolution() {
    const query = this.searchInput.value.trim();
    if (this._searchResolutionCache.query === query) {
      return this._searchResolutionCache.resolution;
    }

    const resolution = this.computeSearchResolution(query);
    this._searchResolutionCache = { query, resolution };
    return resolution;
  }

  computeSearchResolution(query) {
    const normalized = String(query || '').trim();
    if (!normalized) {
      return { mode: 'none', tokens: [], corrections: [], displayQuery: '' };
    }

    const rawTokens = significantSearchTokens(normalized);
    if (rawTokens.length === 0) {
      return { mode: 'none', tokens: [], corrections: [], displayQuery: normalized };
    }

    const tokenMatchesAnyCard = (tokens) => this.getCards().some((card) => (
      matchesSearchQuery(this.cardSearchText(card), normalized, tokens)
    ));

    if (tokenMatchesAnyCard(rawTokens)) {
      return { mode: 'exact', tokens: rawTokens, corrections: [], displayQuery: normalized };
    }

    if (!this.searchVocabulary || this.searchVocabulary.size === 0) {
      return { mode: 'none', tokens: rawTokens, corrections: [], displayQuery: normalized };
    }

    const corrections = [];
    const fuzzyTokens = rawTokens.map((token) => {
      const corrected = suggestFuzzyCorrection(token, this.searchVocabulary);
      if (corrected && corrected !== token) {
        corrections.push({ from: token, to: corrected });
        return corrected;
      }
      return token;
    });

    if (corrections.length === 0 || !tokenMatchesAnyCard(fuzzyTokens)) {
      return { mode: 'none', tokens: rawTokens, corrections: [], displayQuery: normalized };
    }

    return {
      mode: 'fuzzy',
      tokens: fuzzyTokens,
      corrections,
      displayQuery: buildCorrectedQueryDisplay(normalized, corrections),
    };
  }

  matchesDropdown(selected, value) {
    return selected === 'All' || selected === value;
  }

  matchesCollectionFilter(card) {
    const filter = this.activeCollectionFilter;
    if (!filter) return true;

    const checks = [];
    if (filter.sceneCategory) {
      checks.push(card.dataset.sceneCategory === filter.sceneCategory);
    }
    if (filter.sceneCategories) {
      checks.push(filter.sceneCategories.includes(card.dataset.sceneCategory || ''));
    }
    if (filter.category) {
      checks.push(card.dataset.category === filter.category);
    }
    if (filter.categories) {
      checks.push(filter.categories.includes(card.dataset.category || ''));
    }
    if (filter.region) {
      checks.push(card.dataset.region === filter.region);
    }

    return checks.length === 0 || checks.some(Boolean);
  }

  matchesSceneFilter(card) {
    if (!this.filterScene) return true;

    const scene = this.filterScene.value;
    if (scene === 'All') return true;

    const profile = SCENE_FILTER_PROFILES[scene];
    if (!profile) return true;

    const checks = [];
    if (profile.sceneCategory) {
      checks.push(card.dataset.sceneCategory === profile.sceneCategory);
    }
    if (profile.sceneCategories) {
      checks.push(profile.sceneCategories.includes(card.dataset.sceneCategory || ''));
    }
    if (profile.categories) {
      checks.push(profile.categories.includes(card.dataset.category || ''));
    }

    return checks.length === 0 || checks.some(Boolean);
  }

  matchesMacroFilters(card) {
    const region = this.filterRegion.value;
    const tier = this.filterTier ? this.filterTier.value : 'All';

    const regionMatch = this.matchesDropdown(region, card.dataset.region);
    const tierMatch = tier === 'All' || card.dataset.pricingTier === tier;
    const taxonMatch = this.taxonomy.matchesCard(card);
    const collectionMatch = this.matchesCollectionFilter(card);
    const sceneMatch = this.matchesSceneFilter(card);

    return regionMatch && tierMatch && taxonMatch && collectionMatch && sceneMatch;
  }

  cardMatchesFilters(card) {
    const query = this.searchInput.value.trim();
    const filtersMatch = this.matchesMacroFilters(card);

    if (!query) return filtersMatch;

    const resolution = this.getSearchResolution();
    if (resolution.mode === 'none') return false;

    return matchesSearchQuery(this.cardSearchText(card), query, resolution.tokens) && filtersMatch;
  }

  getFilteredCards() {
    return this.getCards().filter((card) => this.cardMatchesFilters(card));
  }

  applyCollectionFilter(filter) {
    this.activeCollectionFilter = filter;
    this.searchInput.value = '';
    this.updateSearchChrome();
    this.filterRegion.value = 'All';
    if (this.filterScene) this.filterScene.value = 'All';
    if (this.filterTier) this.filterTier.value = 'All';
    this.taxonomy.reset();

    if (filter.region) {
      this.filterRegion.value = filter.region;
    }

    if (filter.category) {
      this.taxonomy.setCategory(filter.category);
    }

    this.filterArchive({ scrollToGrid: true });
  }

  updateSearchChrome() {
    const hasQuery = Boolean(this.searchInput.value.trim());
    document.body.classList.toggle('is-search-active', hasQuery);

    if (this.zoneCollections) {
      this.zoneCollections.classList.toggle('is-hidden-during-search', hasQuery);
    }
  }

  scrollToResults() {
    const anchor = this.resultsCount || this.zoneShowcase;
    if (!anchor) return;

    const headerOffset = Number.parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--header-h')
    ) || 64;

    const top = anchor.getBoundingClientRect().top + window.scrollY - headerOffset - 12;
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  }

  updateResultsCount(total, shown) {
    const displayShown = shown ?? this.paginator.displayedCount;
    const query = this.searchInput.value.trim();
    const resolution = query ? this.getSearchResolution() : null;

    let text = total === 0
      ? 'Showing 0 clips'
      : `Showing ${displayShown} of ${total} clip${total !== 1 ? 's' : ''}`;

    if (resolution?.mode === 'fuzzy' && total > 0) {
      text += ` — results for “${resolution.displayQuery}”`;
    }

    this.resultsCount.textContent = text;
  }

  filterArchive(options = {}) {
    const filtered = this.getFilteredCards();
    const allCards = this.getCards();

    allCards.forEach((card) => {
      const match = filtered.includes(card);
      card.classList.toggle('filtered-out', !match);
    });

    this.paginator.resetAndRender();

    if (options.scrollToGrid) {
      requestAnimationFrame(() => this.scrollToResults());
    }
  }

  mountCatalog(cards) {
    this.grid.setAttribute('aria-busy', 'true');
    this.grid.innerHTML = '';
    cards.forEach((card) => {
      card.classList.remove('filtered-out');
    });
    this.paginator.displayedCount = 0;
    this.filterArchive();
    this.grid.removeAttribute('aria-busy');
  }

  bindLegacyFilters() {
    this.searchInput.addEventListener('input', () => {
      this.updateSearchChrome();
      this.filterArchive();
    });

    this.searchInput.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();

      this.updateSearchChrome();
      this.filterArchive({ scrollToGrid: Boolean(this.searchInput.value.trim()) });
      this.searchInput.blur();
    });

    this.filterRegion.addEventListener('change', () => this.filterArchive());
    if (this.filterScene) {
      this.filterScene.addEventListener('change', () => this.filterArchive());
    }
    if (this.filterTier) {
      this.filterTier.addEventListener('change', () => this.filterArchive());
    }
  }
}

window.IPFStockFilters = {
  TaxonomicFilterEngine,
  CatalogFilterController,
  CollectionPortal,
  ArchiveGridPaginator,
  ARCHIVE_BATCH_SIZE,
  matchesSearchQuery,
  matchesBroadCategory,
  buildCategoryTermIndex,
  buildSearchVocabulary,
  suggestFuzzyCorrection,
  BROAD_CATEGORY_TAXONOMY_TERMS,
  SCENE_FILTER_PROFILES,
};
