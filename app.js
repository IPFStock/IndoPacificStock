'use strict';

const ARCHIVE_BATCH_SIZE = 24;

/**
 * Multi-tier taxonomic filter engine with cascading dependency chain.
 */
class TaxonomicFilterEngine {
  constructor(selectElements, onChange) {
    this.onChange = onChange;
    this.assets = [];
    this.chain = [
      {
        field: 'category',
        label: 'Broad Category',
        select: selectElements.taxaCategory,
        read: (asset) => asset.category || '',
      },
      {
        field: 'family',
        label: 'Family',
        select: selectElements.taxaFamily,
        read: (asset) => asset.technicalSpecs?.family || '',
      },
      {
        field: 'species',
        label: 'Common Name',
        select: selectElements.taxaCommon,
        read: (asset) => asset.species || '',
      },
      {
        field: 'latinName',
        label: 'Latin Name',
        select: selectElements.taxaLatin,
        read: (asset) => asset.technicalSpecs?.latinName || '',
      },
    ];

    this.values = Object.fromEntries(this.chain.map(({ field }) => [field, 'Any']));

    this.chain.forEach((_, index) => {
      this.chain[index].select.addEventListener('change', () => this.handleChange(index));
    });
  }

  setAssets(assets) {
    this.assets = Array.isArray(assets) ? assets : [];
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

      if (field === 'category') return card.dataset.category === selected;
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
    this.filterSceneCategory = config.filterSceneCategory;
    this.filterRegion = config.filterRegion;
    this.filterFormat = config.filterFormat;
    this.filterTier = config.filterTier;
    this.grid = config.grid;
    this.resultsCount = config.resultsCount;
    this.loadMoreBtn = config.loadMoreBtn;
    this.cardSearchText = config.cardSearchText;
    this.zoneShowcase = config.zoneShowcase;

    this.collectionPortal = null;
    this.activeCollectionFilter = null;

    this.taxonomy = new TaxonomicFilterEngine(config.taxonomicSelects, () => this.filterArchive());

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
      this.filterSceneCategory,
      this.filterRegion,
      this.filterFormat,
      this.filterTier,
      ...this.taxonomy.chain.map((item) => item.select),
    ];
    inputs.forEach((el) => {
      el.addEventListener('change', clearCollectionHighlight);
      el.addEventListener('input', clearCollectionHighlight);
    });
  }

  initTaxonomyFromCatalog() {
    const assets = [...this.getAssetCatalog().values()];
    this.taxonomy.setAssets(assets);
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

  cardMatchesFilters(card) {
    const query = this.searchInput.value.trim().toLowerCase();
    const sceneCategory = this.filterSceneCategory.value;
    const region = this.filterRegion.value;
    const format = this.filterFormat.value;
    const tier = this.filterTier ? this.filterTier.value : 'All';

    const textMatch = !query || this.cardSearchText(card).includes(query);
    const sceneMatch = this.matchesDropdown(sceneCategory, card.dataset.sceneCategory || 'Underwater');
    const regionMatch = this.matchesDropdown(region, card.dataset.region);
    const formatMatch = this.matchesDropdown(format, card.dataset.format);
    const tierMatch = tier === 'All' || card.dataset.pricingTier === tier;
    const taxonMatch = this.taxonomy.matchesCard(card);
    const collectionMatch = this.matchesCollectionFilter(card);

    return textMatch && sceneMatch && regionMatch && formatMatch && tierMatch && taxonMatch && collectionMatch;
  }

  getFilteredCards() {
    return this.getCards().filter((card) => this.cardMatchesFilters(card));
  }

  applyCollectionFilter(filter) {
    this.activeCollectionFilter = filter;
    this.searchInput.value = '';
    this.filterSceneCategory.value = 'All';
    this.filterRegion.value = 'All';
    this.filterFormat.value = 'All';
    if (this.filterTier) this.filterTier.value = 'All';
    this.taxonomy.reset();

    if (filter.region) {
      this.filterRegion.value = filter.region;
    }

    if (filter.category) {
      this.taxonomy.setCategory(filter.category);
    }

    if (filter.sceneCategory) {
      this.filterSceneCategory.value = filter.sceneCategory;
    }

    this.filterArchive({ scrollToGrid: true });
  }

  updateResultsCount(total, shown) {
    const displayShown = shown ?? this.paginator.displayedCount;
    this.resultsCount.textContent = total === 0
      ? 'Showing 0 clips'
      : `Showing ${displayShown} of ${total} clip${total !== 1 ? 's' : ''}`;
  }

  filterArchive(options = {}) {
    const filtered = this.getFilteredCards();
    const allCards = this.getCards();

    allCards.forEach((card) => {
      const match = filtered.includes(card);
      card.classList.toggle('filtered-out', !match);
    });

    this.paginator.resetAndRender();

    if (options.scrollToGrid && this.zoneShowcase) {
      this.zoneShowcase.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    this.searchInput.addEventListener('input', () => this.filterArchive());
    this.filterSceneCategory.addEventListener('change', () => this.filterArchive());
    this.filterRegion.addEventListener('change', () => this.filterArchive());
    this.filterFormat.addEventListener('change', () => this.filterArchive());
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
};
