const fs = require('fs');
const path = require('path');
const { execFile, execFileSync } = require('child_process');
const { promisify } = require('util');

const execFileAsync = promisify(execFile);

const outputDir = path.join(__dirname, 'videos');
const GITHUB_OWNER = 'IPFStock';
const GITHUB_REPO = 'ip-assets-01';
const GITHUB_BRANCH = 'main';
const GITHUB_RAW_BASE = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}`;

function findNumbersFile() {
  return fs
    .readdirSync(__dirname)
    .find((file) => file.toLowerCase().endsWith('.numbers') && /metadata|stock|clips|davinci/i.test(file));
}

function exportNumbersToCsv(numbersFileName) {
  const numbersPath = path.join(__dirname, numbersFileName);
  const csvPath = path.join(__dirname, numbersFileName.replace(/\.numbers$/i, '.csv'));
  const { execFileSync } = require('child_process');

  const script = `
    set numbersFile to POSIX file ${JSON.stringify(numbersPath)}
    set csvFile to POSIX file ${JSON.stringify(csvPath)}
    tell application "Numbers"
      set theDoc to open numbersFile
      export theDoc to csvFile as CSV
      close theDoc saving no
    end tell
  `;

  execFileSync('osascript', ['-e', script], { stdio: 'pipe' });
  console.log(`Exported ${numbersFileName} → ${path.basename(csvPath)}`);
  return csvPath;
}

function ingestCliFlags() {
  const args = process.argv.slice(2);
  return {
    useCsvOnly: args.includes('--use-csv-only') || args.includes('--csv-only'),
    forceExport: args.includes('--force-export') || args.includes('--refresh'),
    skipProbe: args.includes('--skip-probe'),
    help: args.includes('--help') || args.includes('-h'),
  };
}

function findCsvFile() {
  const flags = ingestCliFlags();

  if (flags.help) {
    console.log(`
Indo Pacific Stock — ingest

  node ingest.js              Export Numbers → CSV (default), then sync GitHub → videos/
  node ingest.js --refresh    Same as default (always re-export from Numbers)
  node ingest.js --use-csv-only   Skip Numbers export; use existing CSV on disk only
  node ingest.js --skip-probe     Skip ffprobe MP4 duration enrichment

Requires: macOS with Numbers installed for spreadsheet export.
Optional: ffmpeg/ffprobe (brew install ffmpeg) probes clip length from GitHub MP4s.
`);
    process.exit(0);
  }

  const preferred = path.join(__dirname, 'davinci_export.csv');
  if (!flags.forceExport && flags.useCsvOnly && fs.existsSync(preferred)) {
    return preferred;
  }

  const numbersFile = findNumbersFile();
  const csvFromNumbers = numbersFile
    ? path.join(__dirname, numbersFile.replace(/\.numbers$/i, '.csv'))
    : null;

  if (numbersFile) {
    const csvExists = csvFromNumbers && fs.existsSync(csvFromNumbers);
    if (!flags.useCsvOnly) {
      console.log(`Exporting fresh CSV from ${numbersFile}…`);
      try {
        return exportNumbersToCsv(numbersFile);
      } catch (err) {
        console.error(`Numbers export failed: ${err.message}`);
        console.error('Ensure Numbers is installed, the spreadsheet is saved, and Terminal has permission to control Numbers.');
        if (csvExists) {
          console.warn(`Falling back to existing CSV (${path.basename(csvFromNumbers)}).`);
          return csvFromNumbers;
        }
        throw err;
      }
    }

    if (flags.useCsvOnly && csvExists) {
      console.log(`Using existing CSV (--use-csv-only): ${path.basename(csvFromNumbers)}`);
      return csvFromNumbers;
    }
  }

  if (fs.existsSync(preferred)) return preferred;

  const csvFiles = fs
    .readdirSync(__dirname)
    .filter((file) => file.toLowerCase().endsWith('.csv'))
    .sort();

  if (csvFiles.length === 0) return null;
  if (csvFiles.length === 1) return path.join(__dirname, csvFiles[0]);

  const named = csvFiles.find((file) => /metadata|davinci|stock|clips/i.test(file));
  return path.join(__dirname, named || csvFiles[0]);
}

function readCsvText(filePath) {
  const buffer = fs.readFileSync(filePath);

  if (buffer.length >= 2 && buffer[0] === 0xff && buffer[1] === 0xfe) {
    return buffer.toString('utf16le').replace(/^\uFEFF/, '');
  }

  return buffer.toString('utf8').replace(/^\uFEFF/, '');
}

function parseCsvRow(line) {
  const result = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += ch;
    }
  }

  result.push(current.trim());
  return result.map((value) => value.replace(/^"|"$/g, '').trim());
}

function parseCsvRecords(csvText) {
  const records = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < csvText.length; i++) {
    const ch = csvText[i];
    const next = csvText[i + 1];

    if (ch === '"') {
      if (inQuotes && next === '"') {
        field += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      row.push(field.trim());
      field = '';
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && next === '\n') i += 1;
      row.push(field.trim());
      if (row.some((cell) => cell.length > 0)) records.push(row);
      row = [];
      field = '';
    } else {
      field += ch;
    }
  }

  if (field.length || row.length) {
    row.push(field.trim());
    if (row.some((cell) => cell.length > 0)) records.push(row);
  }

  return records.map((record) =>
    record.map((value) => value.replace(/^"|"$/g, '').trim())
  );
}

function headerIndex(headers, candidates) {
  for (const candidate of candidates) {
    const idx = headers.findIndex((h) =>
      typeof candidate === 'string' ? h === candidate : candidate.test(h)
    );
    if (idx !== -1) return idx;
  }
  return -1;
}

function commentToTitle(comment) {
  return comment
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim();
}

function parseRegion(locationStr) {
  if (!locationStr) return 'Raja Ampat';
  const value = locationStr.toLowerCase();
  if (value.includes('komodo')) return 'Komodo';
  if (value.includes('lembeh')) return 'Lembeh Strait';
  if (value.includes('raja ampat')) return 'Raja Ampat';
  if (value.includes('flores')) return 'Flores';
  if (value.includes('bali')) return 'Bali';
  return locationStr.split(',')[0].trim();
}

const BROAD_TAXA = {
  PELAGIC: 'Pelagic & Open Ocean Schooling Fish',
  BENTHIC_SCHOOLING: 'Benthic Reef Aggregations & Schooling Fish',
  SMALL_CRYPTIC: 'Small Fish Life & Cryptic Bottom-Dwellers',
  APEX_PREDATORS: 'Apex Marine Predators & Elasmobranchii',
  MEGFAUNA: 'Marine Megafauna, Reptiles & Ocean Mammals',
  CEPHALOPODS: 'Cephalopods',
  MOLLUSKS: 'Mollusks',
  HABITATS: 'Marine Habitats, Sponges & Corals',
  REEF_FISH: 'Reef Associated Fish',
  PIPEFISH: 'Pipefish/Seahorses',
  CRUSTACEANS: 'Crustaceans and Misc Macro Life',
  WORMS_ECHINODERMS: 'Worms and Echinoderms',
  TERRESTRIAL_MAMMALS: 'Terrestrial Mammals, Marsupials & Megafauna',
  TERRESTRIAL_REPTILES: 'Terrestrial Reptiles & Herpetofauna',
  AVIAN: 'Avian Bird Species',
  COASTAL_AERIAL: 'Coastal Landscapes Drone Aerials',
  CULTURAL: 'Indo-Pacific Cultural Documentations & Editorial Scenes',
};

const TAXON_BY_LATIN = {
  'eretmochelys imbricata': {
    category: BROAD_TAXA.MEGFAUNA,
    species: 'Hawksbill Turtle',
    family: 'Cheloniidae (Sea Turtles)',
    latinName: 'Eretmochelys imbricata',
  },
  'chelonia mydas': {
    category: BROAD_TAXA.MEGFAUNA,
    species: 'Green Turtle',
    family: 'Cheloniidae (Sea Turtles)',
    latinName: 'Chelonia mydas',
  },
  'plectorhinchus polytaenia': {
    category: BROAD_TAXA.BENTHIC_SCHOOLING,
    species: 'Ribboned Sweetlips',
    family: 'Haemulidae (Sweetlips)',
    latinName: 'Plectorhinchus polytaenia',
  },
  'parapriacanthus ransonneti': {
    category: BROAD_TAXA.BENTHIC_SCHOOLING,
    species: 'Golden Sweepers',
    family: 'Pempheridae (Sweepers)',
    latinName: 'Parapriacanthus ransonneti',
  },
  'zanclus cornutus': {
    category: BROAD_TAXA.REEF_FISH,
    species: 'Moorish Idol',
    family: 'Zanclidae (Moorish Idols)',
    latinName: 'Zanclus cornutus',
  },
  'triaenodon obesus': {
    category: BROAD_TAXA.APEX_PREDATORS,
    species: 'Whitetip Reef Shark',
    family: 'Carcharhinidae (Requiem Sharks)',
    latinName: 'Triaenodon obesus',
  },
};

const TAXON_PATTERN_RULES = [
  {
    pattern: /hawksbill|eretmochelys/i,
    taxon: TAXON_BY_LATIN['eretmochelys imbricata'],
  },
  {
    pattern: /green.?turtle|chelonia\s+mydas/i,
    taxon: TAXON_BY_LATIN['chelonia mydas'],
  },
  {
    pattern: /(?<![a-z])turtle|greenturtle/i,
    taxon: TAXON_BY_LATIN['chelonia mydas'],
  },
  {
    pattern: /manta/i,
    taxon: {
      category: BROAD_TAXA.APEX_PREDATORS,
      species: 'Manta Ray',
      family: 'Mobulidae (Manta Rays)',
      latinName: 'Mobula birostris',
    },
  },
  {
    pattern: /dolphin|whale|dugong/i,
    taxon: {
      category: BROAD_TAXA.MEGFAUNA,
      species: 'Dolphins',
      family: 'Delphinidae (Dolphins)',
      latinName: 'Delphinidae sp.',
    },
  },
  {
    pattern: /moorish.?idol|zanclus|zanius/i,
    taxon: TAXON_BY_LATIN['zanclus cornutus'],
  },
  {
    pattern: /white.?tip|triaenodon|reef.?shark|shark|hammerhead/i,
    taxon: TAXON_BY_LATIN['triaenodon obesus'],
  },
  {
    pattern: /sweetlips|plectorhinchus|ribbon.?sweetlips/i,
    taxon: TAXON_BY_LATIN['plectorhinchus polytaenia'],
  },
  {
    pattern: /sweeper|parapriacanthus|golden.?sweeper/i,
    taxon: TAXON_BY_LATIN['parapriacanthus ransonneti'],
  },
  {
    pattern: /anthias|damselfish|pomacentrid|school/i,
    taxon: {
      category: BROAD_TAXA.BENTHIC_SCHOOLING,
      species: 'Anthias',
      family: 'Pomacentridae (Damselfish)',
      latinName: 'Pseudanthias sp.',
    },
  },
  {
    pattern: /goby|gobiidae|blenny|dartfish/i,
    taxon: {
      category: BROAD_TAXA.SMALL_CRYPTIC,
      species: 'Goby',
      family: 'Gobiidae (Gobies)',
      latinName: 'Gobiidae sp.',
    },
  },
  {
    pattern: /wrasse|labrid/i,
    taxon: {
      category: BROAD_TAXA.REEF_FISH,
      species: 'Wrasse',
      family: 'Labridae (Wrasses)',
      latinName: 'Labridae sp.',
    },
  },
  {
    pattern: /pipefish|seahorse|syngnath/i,
    taxon: {
      category: BROAD_TAXA.PIPEFISH,
      species: 'Seahorse',
      family: 'Syngnathidae (Pipefish & Seahorses)',
      latinName: 'Syngnathidae sp.',
    },
  },
  {
    pattern: /octopus|cephalopod|cuttlefish|squid/i,
    taxon: {
      category: BROAD_TAXA.CEPHALOPODS,
      species: 'Octopus',
      family: 'Octopodidae (Octopuses)',
      latinName: 'Octopus sp.',
    },
  },
  {
    pattern: /nudibranch|mollusk|mollusc|clam|snail|cowrie/i,
    taxon: {
      category: BROAD_TAXA.MOLLUSKS,
      species: 'Mollusk',
      family: 'Mollusca',
      latinName: 'Mollusca sp.',
    },
  },
  {
    pattern: /shrimp|crab|crustacean|lobster|mantis.?shrimp/i,
    taxon: {
      category: BROAD_TAXA.CRUSTACEANS,
      species: 'Crustacean',
      family: 'Crustacea',
      latinName: 'Crustacea sp.',
    },
  },
  {
    pattern: /starfish|sea star|brittle star|feather star|crinoid|sea cucumber|holothur|sea urchin|urchin|echinoderm/i,
    taxon: {
      category: BROAD_TAXA.WORMS_ECHINODERMS,
      species: 'Echinoderm',
      family: 'Echinodermata',
      latinName: 'Echinodermata sp.',
    },
  },
  {
    pattern: /polychaete|nereis|fireworm|flatworm|ribbon worm|bristle.?worm|tube.?worm|(?<![a-z])worm/i,
    taxon: {
      category: BROAD_TAXA.WORMS_ECHINODERMS,
      species: 'Marine Worm',
      family: 'Annelida (Polychaetes)',
      latinName: 'Polychaeta sp.',
    },
  },
  {
    pattern: /pelagic|open.?ocean|tuna|barracuda|jacks? schooling/i,
    taxon: {
      category: BROAD_TAXA.PELAGIC,
      species: 'Pelagic Fish',
      family: '',
      latinName: '',
    },
  },
  {
    pattern: /terrestrial mammal|marsupial|kangaroo|wallaby|koala|orangutan|primate|proboscis monkey|macaque|monkey|babirusa|anoa|cuscus|tree.?kangaroo|wild boar|sulawesi bear|civet|tapir|elephant/i,
    taxon: {
      category: BROAD_TAXA.TERRESTRIAL_MAMMALS,
      species: 'Terrestrial Mammal',
      family: 'Mammalia',
      latinName: 'Mammalia sp.',
    },
  },
  {
    pattern: /komodo dragon|varanus komodoensis/i,
    taxon: {
      category: BROAD_TAXA.TERRESTRIAL_REPTILES,
      species: 'Komodo Dragon',
      family: 'Varanidae (Monitor Lizards)',
      latinName: 'Varanus komodoensis',
    },
  },
  {
    pattern: /python|cobra|king cobra|herpetofauna|terrestrial reptile|monitor lizard|land.?snake|skink|terrestrial gecko/i,
    taxon: {
      category: BROAD_TAXA.TERRESTRIAL_REPTILES,
      species: 'Terrestrial Reptile',
      family: 'Reptilia',
      latinName: 'Reptilia sp.',
    },
  },
  {
    pattern: /avian|bird of prey|hornbill|parrot|kingfisher|\btern\b|seabird|cockatoo|\bheron\b|\begret\b|pelican|eagle|osprey|frigatebird|(?<![a-z])bird/i,
    taxon: {
      category: BROAD_TAXA.AVIAN,
      species: 'Bird',
      family: 'Aves',
      latinName: 'Aves sp.',
    },
  },
  {
    pattern: /sunset|sunray|landscape|scenery|phinisi|speedboat|panning the camera|islands of komodo|drone|aerial/i,
    taxon: {
      category: BROAD_TAXA.COASTAL_AERIAL,
      species: 'Seascape',
      family: '',
      latinName: '',
    },
  },
  {
    pattern: /healthy soft corals|barrel sponge|reef habitat|coral head|coral garden|sponge/i,
    taxon: {
      category: BROAD_TAXA.HABITATS,
      species: 'Coral Reef Habitat',
      family: '',
      latinName: '',
    },
  },
  {
    pattern: /culture|village|tradition|ceremony|fisherman|editorial|documentary scene/i,
    taxon: {
      category: BROAD_TAXA.CULTURAL,
      species: 'Cultural Scene',
      family: '',
      latinName: '',
    },
  },
];

function normalizeSceneCategory(csvCategory) {
  const value = (csvCategory || 'Underwater').trim();
  if (/landscape/i.test(value)) return 'Landscape';
  if (/culture/i.test(value)) return 'Culture';
  if (/aerial/i.test(value)) return 'Aerial';
  if (/marine life/i.test(value)) return 'Underwater';
  return value;
}

function extractLatinBinomials(text) {
  if (!text) return [];
  const matches = text.match(/\b([A-Z][a-z]+)\s+([a-z]+)\b/g) || [];
  return matches.map((match) => match.toLowerCase());
}

function resolveTaxonomy({ description, comments, shootCategory, title }) {
  const sceneCategory = normalizeSceneCategory(shootCategory);
  const haystack = `${description || ''} ${comments || ''} ${title || ''}`.toLowerCase();

  for (const latin of extractLatinBinomials(description)) {
    if (TAXON_BY_LATIN[latin]) {
      return { ...TAXON_BY_LATIN[latin], sceneCategory };
    }
  }

  for (const [latin, taxon] of Object.entries(TAXON_BY_LATIN)) {
    if (haystack.includes(latin)) {
      return { ...taxon, sceneCategory };
    }
  }

  for (const rule of TAXON_PATTERN_RULES) {
    if (rule.pattern.test(haystack)) {
      return { ...rule.taxon, sceneCategory };
    }
  }

  if (/landscape/i.test(shootCategory)) {
    return {
      category: BROAD_TAXA.COASTAL_AERIAL,
      species: 'Seascape',
      family: '',
      latinName: '',
      sceneCategory,
    };
  }

  if (/culture/i.test(shootCategory)) {
    return {
      category: BROAD_TAXA.CULTURAL,
      species: 'Cultural Scene',
      family: '',
      latinName: '',
      sceneCategory,
    };
  }

  if (/aerial/i.test(shootCategory)) {
    return {
      category: BROAD_TAXA.COASTAL_AERIAL,
      species: 'Aerial View',
      family: '',
      latinName: '',
      sceneCategory,
    };
  }

  return {
    category: BROAD_TAXA.REEF_FISH,
    species: 'Marine Life',
    family: '',
    latinName: '',
    sceneCategory,
  };
}

function inferTaxonomyFromSlug(slug, title) {
  return resolveTaxonomy({
    description: '',
    comments: slug.replace(/-/g, ' '),
    shootCategory: 'Underwater',
    title,
  });
}

function inferFormat(resolution, cameraFormat, codec) {
  if (resolution.includes('7680')) return '8K RED RAW';
  if (resolution.includes('6144')) return '6K RED RAW';
  if (resolution.includes('5120')) return '5K RED RAW';
  if (resolution.includes('4096') || resolution.includes('3840')) return '4K';
  if (cameraFormat) return `${cameraFormat} RED RAW`;
  if (codec) return `${codec.toUpperCase()} RAW`;
  return '8K RED RAW';
}

function inferMaxResolutionLabel(resolution) {
  if (!resolution) return 'HD';
  const match = resolution.match(/(\d+)\s*[x×]\s*(\d+)/i);
  const width = match
    ? Math.max(parseInt(match[1], 10), parseInt(match[2], 10))
    : parseInt(resolution, 10) || 0;

  if (width >= 7680) return '8K';
  if (width >= 6144) return '6K';
  if (width >= 5120) return '5K';
  if (width >= 4096) return '4K';
  if (width >= 3840) return '4K';
  if (width >= 1920) return 'HD';
  return width ? `${width}P` : 'HD';
}

function inferCodecLabel(codec) {
  if (!codec) return 'RAW';
  const value = codec.toLowerCase();
  if (value.includes('r3d') || value.includes('redcode')) return 'R3D';
  if (value.includes('prores')) return 'ProRes';
  return codec.toUpperCase();
}

function inferNativeFormatBadge(resolution, codec) {
  return `${inferMaxResolutionLabel(resolution)} ${inferCodecLabel(codec)}`;
}

const KEYWORD_STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'from', 'with', 'as', 'its', 'of', 'for',
  'is', 'by', 'through', 'over', 'into', 'under', 'during', 'this', 'that', 'are', 'was', 'be',
  'been', 'using', 'native', 'inside', 'running', 'captured', 'premium', 'high', 'fidelity',
  'archival', 'sequence', 'documenting', 'technical', 'profile', 'framework', 'format', 'aspect',
  'ratio', 'sensor', 'natural', 'history', 'rights', 'managed', 'stock', 'footage', 'indopacific',
  'video', 'clip', 'run', 'ingest', 'after', 'updating', 'your', 'davinci', 'csv', 'full',
  'metadata', 'swims', 'swim', 'swimming', 'captured', 'natively',
]);

function normalizeKeywordPhrase(value) {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

function stripLeadingArticle(phrase) {
  return phrase.replace(/^(a|an|the)\s+/i, '').trim();
}

function extractKeywords(meta) {
  const keywords = new Set();
  const spec = meta.technicalSpecs || {};

  const add = (value) => {
    if (!value || typeof value !== 'string') return;
    const phrase = normalizeKeywordPhrase(stripLeadingArticle(value.replace(/[^\w\s.-]/g, ' ')));
    if (phrase.length > 2 && !KEYWORD_STOP_WORDS.has(phrase)) keywords.add(phrase);
  };

  const addToken = (value) => {
    if (!value || typeof value !== 'string') return;
    value
      .toLowerCase()
      .replace(/[^\w\s.-]/g, ' ')
      .split(/\s+/)
      .forEach((word) => {
        if (/^\d+$/.test(word)) return;
        if (word.length > 2 && !KEYWORD_STOP_WORDS.has(word)) keywords.add(word);
      });
  };

  const addSlugParts = (value) => {
    if (!value || typeof value !== 'string') return;
    value.toLowerCase().split(/[-_\s]+/).forEach((word) => {
      if (word.length > 2 && !KEYWORD_STOP_WORDS.has(word)) keywords.add(word);
    });
  };

  [meta.region, meta.species, meta.category, meta.format, meta.nativeFormatBadge, meta.camera]
    .forEach((value) => {
      add(value);
      addToken(value);
    });

  addToken(meta.behavior);
  addSlugParts(meta.comments);
  addSlugParts(meta.title);
  addToken(spec.codec);
  addToken(spec.cameraFormat);
  addToken(spec.cameraType);

  const resLabel = inferMaxResolutionLabel(spec.resolution || meta.format || '');
  if (resLabel) add(resLabel.toLowerCase());

  const codecLabel = inferCodecLabel(spec.codec || '');
  if (codecLabel) add(codecLabel.toLowerCase());

  if (spec.fps) {
    const fpsValue = parseFloat(spec.fps);
    if (!Number.isNaN(fpsValue)) keywords.add(`${fpsValue} fps`);
  }

  const description = meta.description || '';
  (description.match(/\b[A-Z][a-z]+(?:\s+[a-z]+)+\b/g) || []).forEach((name) => add(name));

  description.split(/[,;]/).forEach((chunk) => {
    const phrase = normalizeKeywordPhrase(stripLeadingArticle(chunk.replace(/[^\w\s-]/g, ' ')));
    if (phrase.length > 2 && phrase.split(' ').length <= 6) add(phrase);
  });

  addToken(description);

  if (meta.comments) {
    add(normalizeKeywordPhrase(meta.comments.replace(/[-_]+/g, ' ')));
  }

  return [...new Set(
    Array.from(keywords)
      .map((keyword) => keyword.replace(/\.$/, ''))
      .filter((keyword) => keyword.length > 2 && !/^\d+$/.test(keyword))
  )]
    .sort((a, b) => a.localeCompare(b))
    .slice(0, 32);
}

function sourceToMp4FileName(originalFileName) {
  const base = originalFileName.replace(/\.[^/.]+$/, '').trim();
  const reelBase = base.replace(/_\d+$/, '');
  return `${reelBase}.mp4`;
}

function mp4BaseName(fileName) {
  return fileName.replace(/\.mp4$/i, '').toLowerCase();
}

function slugFromMp4(fileName) {
  return mp4BaseName(fileName).replace(/_/g, '-');
}

function titleFromMp4(fileName) {
  return mp4BaseName(fileName)
    .replace(/-/g, ' ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function resolveFfprobePath() {
  const candidates = [
    process.env.FFPROBE_PATH,
    'ffprobe',
    '/opt/homebrew/bin/ffprobe',
    '/usr/local/bin/ffprobe',
  ].filter(Boolean);

  for (const candidate of candidates) {
    try {
      execFileSync(candidate, ['-version'], { stdio: 'pipe', timeout: 5000 });
      return candidate;
    } catch (_) {
      // try next candidate
    }
  }

  return null;
}

function parseFpsValue(fps) {
  if (!fps) return 24;
  const value = String(fps).trim();
  const fraction = value.match(/^(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)$/);
  if (fraction) {
    const numerator = parseFloat(fraction[1]);
    const denominator = parseFloat(fraction[2]);
    if (denominator > 0) return numerator / denominator;
  }
  const numeric = parseFloat(value);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : 24;
}

function formatDurationFromFrames(totalFrames, fps = 24) {
  if (!Number.isFinite(totalFrames) || totalFrames <= 0) return '';

  const frameRate = parseFpsValue(fps);
  const frameCount = Math.max(0, Math.round(totalFrames));
  const frameMod = Math.max(1, Math.round(frameRate));
  const frames = frameCount % frameMod;
  const totalSecondsInt = Math.floor(frameCount / frameRate);
  const pad = (value) => String(value).padStart(2, '0');
  const hours = Math.floor(totalSecondsInt / 3600);
  const minutes = Math.floor((totalSecondsInt % 3600) / 60);
  const seconds = totalSecondsInt % 60;

  return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}:${pad(frames)}`;
}

function formatDurationFromSeconds(totalSeconds, fps = 24) {
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) return '';
  const frameRate = parseFpsValue(fps);
  return formatDurationFromFrames(Math.max(0, Math.round(totalSeconds * frameRate)), frameRate);
}

const TIMECODE_PATTERN = /^(\d+):(\d{1,2}):(\d{1,2}):(\d{1,3})$/;

function parseTimecodeFrames(tc, fps = 24) {
  const match = String(tc).trim().match(TIMECODE_PATTERN);
  if (!match) return null;

  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  const seconds = Number(match[3]);
  const frames = Number(match[4]);
  const frameRate = parseFpsValue(fps);

  return Math.round((hours * 3600 + minutes * 60 + seconds) * frameRate + frames);
}

function isTimecodeRange(duration) {
  return /\s-\s/.test(String(duration || ''));
}

function durationNeedsNormalization(duration) {
  if (!duration) return false;
  const value = String(duration);
  if (isTimecodeRange(value)) return true;
  return /\.\d/.test(value);
}

function normalizeCsvDuration(rawDuration, fps) {
  if (!rawDuration) return '';

  const value = String(rawDuration).trim();
  if (isTimecodeRange(value)) {
    const parts = value.split(/\s-\s/).map((part) => part.trim());
    if (parts.length !== 2) return value;

    const startFrames = parseTimecodeFrames(parts[0], fps);
    const endFrames = parseTimecodeFrames(parts[1], fps);
    if (startFrames == null || endFrames == null) return value;

    const frameRate = parseFpsValue(fps);
    const frameDiff = Math.max(0, endFrames - startFrames);
    return formatDurationFromFrames(frameDiff, frameRate);
  }

  const totalFrames = parseTimecodeFrames(value, fps);
  if (totalFrames != null) {
    return formatDurationFromFrames(totalFrames, fps);
  }

  return value;
}

async function probeMp4Duration(ffprobePath, mediaUrl) {
  const { stdout } = await execFileAsync(
    ffprobePath,
    [
      '-v',
      'error',
      '-show_entries',
      'format=duration',
      '-of',
      'default=noprint_wrappers=1:nokey=1',
      mediaUrl,
    ],
    { timeout: 45000, maxBuffer: 1024 * 1024 }
  );

  const seconds = parseFloat(String(stdout).trim());
  return Number.isFinite(seconds) && seconds > 0 ? seconds : null;
}

function normalizeCatalogDurations(catalog) {
  let normalized = 0;
  catalog.forEach((data) => {
    const spec = data.technicalSpecs || {};
    if (!durationNeedsNormalization(spec.duration)) return;
    const next = normalizeCsvDuration(spec.duration, spec.fps);
    if (next && next !== spec.duration) {
      spec.duration = next;
      spec.durationSource = 'timecode-range';
      normalized += 1;
    }
  });
  if (normalized) {
    console.log(`Normalized ${normalized} timecode-range durations.`);
  }
  return normalized;
}

async function enrichCatalogDurations(catalog) {
  normalizeCatalogDurations(catalog);

  const ffprobePath = resolveFfprobePath();
  if (!ffprobePath) {
    console.warn('ffprobe not found — skipping MP4 duration probe.');
    console.warn('Install ffmpeg to bake clip lengths into JSON: brew install ffmpeg');
    return { probed: 0, skipped: catalog.size, failed: 0 };
  }

  const needsProbe = [];
  catalog.forEach((data) => {
    const spec = data.technicalSpecs || {};
    if (spec.duration && !durationNeedsNormalization(spec.duration)) return;
    const fileName = spec.fileName;
    if (!fileName) return;
    needsProbe.push({
      data,
      url: `${GITHUB_RAW_BASE}/${fileName}`,
      label: spec.slug || fileName,
    });
  });

  if (needsProbe.length === 0) {
    console.log('All clips already have duration metadata.');
    return { probed: 0, skipped: catalog.size, failed: 0 };
  }

  console.log(`Probing ${needsProbe.length} MP4 durations via ffprobe…`);
  const concurrency = 6;
  let probed = 0;
  let failed = 0;

  for (let index = 0; index < needsProbe.length; index += concurrency) {
    const batch = needsProbe.slice(index, index + concurrency);
    await Promise.all(
      batch.map(async ({ data, url, label }) => {
        try {
          const seconds = await probeMp4Duration(ffprobePath, url);
          if (!seconds) {
            failed += 1;
            console.warn(`  No duration returned for ${label}`);
            return;
          }

          const fps = parseFpsValue(data.technicalSpecs?.fps);
          const duration = formatDurationFromSeconds(seconds, fps);
          if (!data.technicalSpecs) data.technicalSpecs = {};
          data.technicalSpecs.duration = duration;
          data.technicalSpecs.durationSeconds = Math.round(seconds * 1000) / 1000;
          data.technicalSpecs.durationSource = 'ffprobe';
          probed += 1;
        } catch (err) {
          failed += 1;
          console.warn(`  ffprobe failed for ${label}: ${err.message}`);
        }
      })
    );

    if (probed > 0 && (probed % 20 === 0 || index + concurrency >= needsProbe.length)) {
      console.log(`  Probed ${Math.min(index + concurrency, needsProbe.length)}/${needsProbe.length}… (${probed} durations captured)`);
    }
  }

  console.log(`Duration probe complete: ${probed} enriched, ${failed} failed, ${catalog.size - needsProbe.length} already had duration.`);
  return { probed, skipped: catalog.size - needsProbe.length, failed };
}

function normalizeLicenseType(raw) {
  if (!raw) return 'commercial';
  const value = String(raw).toLowerCase().trim();
  if (/editorial/.test(value)) return 'editorial';
  return 'commercial';
}

function normalizePricingTier(raw) {
  if (!raw) return 'standard';
  const value = String(raw).toLowerCase().trim();
  if (/premium/.test(value)) return 'premium';
  return 'standard';
}

async function fetchGithubMp4Files() {
  const url = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/?ref=${GITHUB_BRANCH}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`GitHub API returned ${response.status}`);
  }

  const entries = await response.json();
  return entries
    .filter((entry) => entry.type === 'file' && /\.mp4$/i.test(entry.name))
    .map((entry) => entry.name)
    .sort();
}

function parseCsvRows(csvFilePath) {
  const csvData = readCsvText(csvFilePath);
  const records = parseCsvRecords(csvData);
  if (records.length < 2) return { csvByMp4: new Map(), renameCommands: [] };

  const headers = records[0].map((h) => h.replace(/["']/g, '').trim());

  const idxName = headerIndex(headers, ['File Name', 'Clip Name']);
  const idxRes = headerIndex(headers, ['Resolution']);
  const idxCodec = headerIndex(headers, ['Video Codec', 'Codec']);
  const idxDate = headerIndex(headers, ['Date Recorded', /Date Modified/i, /Date/i]);
  const idxBitDepth = headerIndex(headers, ['Bit Depth']);
  const idxCamType = headerIndex(headers, [/Camera Type/i, /Camera Model/i]);
  const idxCamFormat = headerIndex(headers, ['Camera Format']);
  const idxFPS = headerIndex(headers, ['Camera FPS', 'Shot Frame Rate', 'FPS']);
  const idxRatio = headerIndex(headers, ['Aspect Ratio Notes', 'Aspect Ratio']);
  const idxComments = headerIndex(headers, ['Comments']);
  const idxDescription = headerIndex(headers, ['Description', 'Descriptions']);
  const idxLocation = headerIndex(headers, ['Location']);
  const idxCategory = headerIndex(headers, ['Category']);
  const idxDuration = headerIndex(headers, ['Duration TC', 'Duration', 'Clip Duration', /Timecode/i]);
  const idxLicense = headerIndex(headers, ['License', 'License Type', /Editorial/i]);
  const idxTier = headerIndex(headers, ['Tier', 'Pricing Tier', 'Price Tier']);

  const csvByMp4 = new Map();
  const renameCommands = [];

  for (let i = 1; i < records.length; i++) {
    const row = records[i];
    if (row.length < 2) continue;

    const clean = (idx) => (idx !== -1 && row[idx] ? row[idx].replace(/["']/g, '').trim() : '');

    const originalFileName = clean(idxName);
    if (!originalFileName || !/\.(r3d|mp4|mov)$/i.test(originalFileName)) continue;

    const rawCameraCode = originalFileName.replace(/\.[^/.]+$/, '').trim();
    const rawSubjectNote = clean(idxComments);
    const descriptionText = clean(idxDescription);
    const region = parseRegion(clean(idxLocation));
    const mp4FileName = sourceToMp4FileName(originalFileName);

    if (!rawSubjectNote) {
      console.warn(`Warning: Missing 'Comments' for ${originalFileName}. Using archive slug.`);
    }

    const subjectSlug = rawSubjectNote
      ? rawSubjectNote.toLowerCase().replace(/[\s_]+/g, '-')
      : 'archive';
    const cameraSlug = rawCameraCode.toLowerCase().replace(/[\s_]+/g, '-');
    const finalCleanSlug = `${subjectSlug}-${cameraSlug}`;

    const resolution = clean(idxRes);
    const codec = clean(idxCodec);
    const dateStr = clean(idxDate);
    const bitDepth = clean(idxBitDepth);
    const cameraType = clean(idxCamType) || 'RED V-Raptor 8K';
    const cameraFormat = clean(idxCamFormat);
    const fps = clean(idxFPS);
    const aspectRatio = clean(idxRatio);
    const duration = normalizeCsvDuration(clean(idxDuration), fps);
    const licenseType = normalizeLicenseType(clean(idxLicense));
    const pricingTier = normalizePricingTier(clean(idxTier));
    const shootCategory = clean(idxCategory) || 'Underwater';
    const taxon = resolveTaxonomy({
      description: descriptionText,
      comments: rawSubjectNote,
      shootCategory,
      title: rawSubjectNote ? commentToTitle(rawSubjectNote) : titleFromMp4(mp4FileName),
    });
    const format = inferFormat(resolution, cameraFormat, codec);
    const nativeFormatBadge = inferNativeFormatBadge(resolution, codec);
    const title = rawSubjectNote
      ? commentToTitle(rawSubjectNote)
      : titleFromMp4(mp4FileName);

    const description = descriptionText ||
      `Premium, high-fidelity archival sequence of ${rawSubjectNote ? commentToTitle(rawSubjectNote).toLowerCase() : 'marine life'} captured natively using a ${cameraType} sensor. Technical profile: ${resolution}, running ${fps} FPS at ${bitDepth}-bit inside a native ${aspectRatio || 'cinematic'} aspect ratio format framework.`;

    const keywordMeta = {
      title,
      category: taxon.category,
      region,
      species: taxon.species,
      format,
      nativeFormatBadge,
      camera: cameraType,
      behavior: `Natural history sequence documenting ${rawSubjectNote ? commentToTitle(rawSubjectNote).toLowerCase() : 'marine wildlife'}.`,
      description,
      comments: rawSubjectNote,
      technicalSpecs: {
        resolution,
        codec,
        fps,
        cameraFormat,
        cameraType,
        family: taxon.family,
        latinName: taxon.latinName,
      },
    };

    const jsonMetadataObject = {
      title,
      category: taxon.category,
      region,
      species: taxon.species,
      format,
      nativeFormatBadge,
      licenseType,
      pricingTier,
      availableSizes: ['8K RED RAW', '4K ProRes 422 HQ', '1080p Master'],
      camera: cameraType,
      behavior: keywordMeta.behavior,
      videoUrl: `${GITHUB_RAW_BASE}/${mp4FileName}`,
      description,
      keywords: extractKeywords(keywordMeta),
      technicalSpecs: {
        fileName: mp4FileName,
        slug: finalCleanSlug,
        originalCameraCode: originalFileName,
        resolution,
        codec,
        date: dateStr,
        bitDepth,
        cameraType,
        cameraFormat,
        fps,
        aspectRatio,
        duration,
        sceneCategory: taxon.sceneCategory,
        family: taxon.family,
        latinName: taxon.latinName,
      },
      syncSource: 'csv',
    };

    csvByMp4.set(mp4FileName.toLowerCase(), {
      slug: finalCleanSlug,
      data: jsonMetadataObject,
    });

    renameCommands.push(
      `# ${title}`,
      `mv "${mp4FileName}" "${finalCleanSlug}.mp4" 2>/dev/null || mv "${rawCameraCode}.mp4" "${mp4FileName}" 2>/dev/null || true`
    );
  }

  return { csvByMp4, renameCommands };
}

function mergeCsvMaps(targetMap, sourceMap) {
  sourceMap.forEach((entry, mp4Key) => {
    const existing = targetMap.get(mp4Key);
    if (!existing) {
      targetMap.set(mp4Key, entry);
      return;
    }

    const existingSpec = existing.data.technicalSpecs || {};
    const incomingSpec = entry.data.technicalSpecs || {};
    const mergedSpec = { ...existingSpec };

    Object.keys(incomingSpec).forEach((key) => {
      if (!mergedSpec[key] && incomingSpec[key]) {
        mergedSpec[key] = incomingSpec[key];
      }
    });

    const merged = {
      slug: existing.slug || entry.slug,
      data: {
        ...existing.data,
        title: existing.data.title || entry.data.title,
        description: existing.data.description || entry.data.description,
        licenseType: existing.data.licenseType || entry.data.licenseType || 'commercial',
        pricingTier: existing.data.pricingTier || entry.data.pricingTier || 'standard',
        technicalSpecs: mergedSpec,
        syncSource: existing.data.syncSource === 'csv' || entry.data.syncSource === 'csv'
          ? 'csv'
          : existing.data.syncSource,
      },
    };

    targetMap.set(mp4Key, merged);
  });
}

function findAllMetadataCsvFiles(primaryCsvPath) {
  const discovered = fs
    .readdirSync(__dirname)
    .filter((file) => {
      const lower = file.toLowerCase();
      return (
        lower.endsWith('.csv') &&
        /metadata|davinci|stock|clips|ipf_stock_footage/i.test(lower) &&
        !/export\d/i.test(lower) &&
        !/22 clips/i.test(lower) &&
        !/\.backup\./i.test(lower) &&
        !/^stub-/i.test(lower)
      );
    })
    .map((file) => path.join(__dirname, file));

  const ordered = [];
  const seen = new Set();

  [primaryCsvPath, ...discovered.sort()].forEach((filePath) => {
    if (!filePath || seen.has(filePath) || !fs.existsSync(filePath)) return;
    seen.add(filePath);
    ordered.push(filePath);
  });

  return ordered;
}

function buildStubFromMp4(mp4FileName) {
  const slug = slugFromMp4(mp4FileName);
  const title = titleFromMp4(mp4FileName);
  const taxon = inferTaxonomyFromSlug(slug, title);
  const description = `${title} — rights-managed stock footage from Indo Pacific Stock. Run ingest after updating your DaVinci CSV for full metadata.`;
  const stubMeta = {
    title,
    category: taxon.category,
    region: 'Raja Ampat',
    species: taxon.species,
    format: '8K RED RAW',
    nativeFormatBadge: 'RAW',
    camera: 'RED V-Raptor 8K',
    behavior: 'Natural history sequence.',
    description,
    comments: mp4BaseName(mp4FileName),
    technicalSpecs: {
      fileName: mp4FileName,
      slug,
      sceneCategory: taxon.sceneCategory,
      family: taxon.family,
      latinName: taxon.latinName,
    },
  };

  return {
    slug,
    data: {
      title,
      category: taxon.category,
      region: stubMeta.region,
      species: taxon.species,
      format: stubMeta.format,
      nativeFormatBadge: stubMeta.nativeFormatBadge,
      availableSizes: ['8K RED RAW', '4K ProRes 422 HQ', '1080p Master'],
      camera: stubMeta.camera,
      behavior: stubMeta.behavior,
      videoUrl: `${GITHUB_RAW_BASE}/${mp4FileName}`,
      description,
      keywords: extractKeywords(stubMeta),
      licenseType: 'commercial',
      pricingTier: 'standard',
      technicalSpecs: stubMeta.technicalSpecs,
      syncSource: 'github',
    },
  };
}

function pruneStaleJson(activeSlugs) {
  const active = new Set(activeSlugs);
  const existing = fs.readdirSync(outputDir).filter((file) => file.endsWith('.json') && file !== 'manifest.json');

  existing.forEach((file) => {
    const slug = file.replace(/\.json$/, '');
    if (!active.has(slug)) {
      fs.unlinkSync(path.join(outputDir, file));
      console.log(`Removed stale catalog entry: ${file}`);
    }
  });
}

async function main() {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const csvFilePath = findCsvFile();
  let csvByMp4 = new Map();
  let renameCommands = [];

  if (csvFilePath) {
    const csvFiles = findAllMetadataCsvFiles(csvFilePath);
    csvFiles.forEach((filePath, index) => {
      console.log(`Using CSV${csvFiles.length > 1 ? ` (${index + 1}/${csvFiles.length})` : ''}: ${path.basename(filePath)}`);
      const parsed = parseCsvRows(filePath);
      mergeCsvMaps(csvByMp4, parsed.csvByMp4);
      if (index === 0) renameCommands = parsed.renameCommands;
    });
  } else {
    console.warn('No CSV found — syncing GitHub MP4s with stub metadata only.');
    console.warn('Add a DaVinci export CSV for full titles, resolution, and format badges.');
  }

  console.log('Fetching MP4 list from GitHub…');
  const githubMp4Files = await fetchGithubMp4Files();
  const catalog = new Map();

  githubMp4Files.forEach((mp4FileName) => {
    const csvEntry = csvByMp4.get(mp4FileName.toLowerCase());

    if (csvEntry) {
      catalog.set(csvEntry.slug, csvEntry.data);
      return;
    }

    const stub = buildStubFromMp4(mp4FileName);
    catalog.set(stub.slug, stub.data);
    console.log(`GitHub-only clip (stub metadata): ${mp4FileName} → ${stub.slug}.json`);
  });

  csvByMp4.forEach((entry, mp4Key) => {
    const onGithub = githubMp4Files.some((name) => name.toLowerCase() === mp4Key);
    if (!onGithub) {
      console.warn(`CSV clip not on GitHub yet: ${entry.data.technicalSpecs.fileName}`);
    }
  });

  const flags = ingestCliFlags();
  normalizeCatalogDurations(catalog);
  if (!flags.skipProbe) {
    await enrichCatalogDurations(catalog);
  } else {
    console.log('Skipping ffprobe duration enrichment (--skip-probe).');
  }

  const manifest = Array.from(catalog.entries())
    .sort((a, b) => a[1].title.localeCompare(b[1].title))
    .map(([slug]) => slug);

  manifest.forEach((slug) => {
    fs.writeFileSync(
      path.join(outputDir, `${slug}.json`),
      JSON.stringify(catalog.get(slug), null, 2),
      'utf8'
    );
  });

  pruneStaleJson(manifest);

  fs.writeFileSync(path.join(outputDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');

  fs.writeFileSync(
    path.join(__dirname, 'rename_videos.sh'),
    `#!/bin/bash\n# Run from folder containing exported MP4 files\n${renameCommands.join('\n')}\necho "Rename pass complete."\n`,
    'utf8'
  );
  fs.chmodSync(path.join(__dirname, 'rename_videos.sh'), 0o755);

  const durationCount = Array.from(catalog.values()).filter((item) => item.technicalSpecs?.duration).length;
  console.log(`\nSync complete! ${manifest.length} clips in catalog (${githubMp4Files.length} on GitHub).`);
  console.log(`  CSV metadata: ${Array.from(catalog.values()).filter((item) => item.syncSource === 'csv').length}`);
  console.log(`  GitHub stubs: ${Array.from(catalog.values()).filter((item) => item.syncSource === 'github').length}`);
  console.log(`  With duration: ${durationCount}`);
  console.log('Updated videos/manifest.json');
}

main().catch((err) => {
  console.error('Sync failed:', err.message);
  process.exit(1);
});
