#!/usr/bin/env python3
"""Polish Description fields in the master metadata CSV (British English, stock style)."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / 'Raja Stock Clips 3 Clips Metadata.csv'

MELIBE_FEED = (
    'A Melibe nudibranch, Melibe viridis, feeding with its hooded oral veil, '
    'sweeping the benthos for prey, Komodo National Park, Indonesia, Pacific Ocean'
)
MELIBE_SHRIMP = (
    'A Melibe nudibranch, Melibe viridis, feeding with its hooded oral veil '
    'on a skeleton shrimp, Caprella sp., Komodo National Park, Indonesia, Pacific Ocean'
)
GREY_REEF_RUNNERS = (
    'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of '
    'rainbow runners, Elagatis bipinnulata, rubbing against it, with blue and yellow '
    'fusiliers, Caesio teres, in the background, Komodo National Park, Indonesia, Pacific Ocean'
)
GREY_REEF_RUNNERS_DIVE = (
    'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of '
    'rainbow runners, Elagatis bipinnulata, rubbing against it; the shark dives down '
    'as the runners disperse, Komodo National Park, Indonesia, Pacific Ocean'
)
OCTOPUS_TENT = (
    'A common reef octopus, Octopus cyanea, hunting in coral rubble using a tent '
    'or parachute feeding technique, while small groupers and goatfish wait nearby '
    'for potential prey to be flushed out, Komodo National Park, Indonesia, Pacific Ocean'
)
OCTOPUS_RUBBLE = (
    'A common reef octopus, Octopus cyanea, hunting in coral rubble while small '
    'groupers and goatfish wait nearby for potential prey to be flushed out, '
    'Komodo National Park, Indonesia, Pacific Ocean'
)
MORAY_CARDINAL = (
    'A honeycomb moray, Gymnothorax favagineus, looks out from an overhang, '
    'surrounded by a school of ringtail cardinalfish, Ostorhinchus aureus, and other '
    'cardinalfish, with a lionfish above, Komodo National Park, Indonesia, Pacific Ocean'
)
MORAY_CARDINAL_LIT = (
    'A honeycomb moray, Gymnothorax favagineus, lit from the left, looks out from '
    'an overhang, surrounded by a school of ringtail cardinalfish, Ostorhinchus aureus, '
    'and other cardinalfish, Komodo National Park, Indonesia, Pacific Ocean'
)

EXACT: dict[str, str] = {
    'Wider view of a yellow thorny seahorse, Hippocampus histrix, perched on seagrass, Komodo National Park, Indonesia, Pacific Ocean':
        'Wide view of a yellow thorny seahorse, Hippocampus histrix, perched on seagrass, Komodo National Park, Indonesia, Pacific Ocean',
    'Close up of a yellow thorny seahorse, Hippocampus histrix, perched on seagrass, Komodo National Park, Indonesia, Pacific Ocean':
        'Close-up of a yellow thorny seahorse, Hippocampus histrix, perched on seagrass, Komodo National Park, Indonesia, Pacific Ocean',
    'A smiling local woman shows off her brightly colour sarongs, Bonto village, Sangeang Island, Sumbawa, Indonesia, No Model Release':
        'A smiling local woman shows off her brightly coloured sarongs, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Pan left to right of two women standing in front of local homes with goats and chickens, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release':
        'Pan from left to right across two women standing in front of local homes with goats and chickens, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A man walks under a drying line filled with colourful sorongs, Bonto village, Sangeang Island, Sumbawa, Indonesia. No MR':
        'A man walks beneath a drying line hung with colourful sarongs, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Local man walks away from his small boat across the beach to the village, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'A local man walks away from his small boat across the beach towards the village, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Village man pushing his small wooden boat to sea, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'A village man pushes his small wooden boat out to sea, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Two young girls playing in the sea, Bontoh village, Sangeang Island, Sumbawa, Indonesia. No MR':
        'Two young girls playing in the sea, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A local boatbuilder with a cigarette in his mouth walks down a ladder from a boat he is building, Sangeang Island, Sumbawa, Indonesia. No MR':
        'A local boatbuilder with a cigarette in his mouth walks down a ladder from a boat under construction, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Shooting the sun rays diffusing in shallow blue water, Komodo National Park, Indonesia, Pacific Ocean':
        'Sun rays diffusing through shallow blue water, Komodo National Park, Indonesia, Pacific Ocean',
    'Sunset over the waters of Komodo National Park with a speedboat crossing in front of a traditional phinisi boat in the foreground, Komodo National Park, Indonesia, Pacific Ocean':
        'Sunset over the waters of Komodo National Park, with a speedboat crossing in front of a traditional phinisi boat, Komodo National Park, Indonesia, Pacific Ocean',
    'Camera pushing forward over a variety of healthy Acropora sp., corals including table and stag horn varieties. Leather coral and soft corals cover the reef with damsel fish and chromis in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Camera pushing forward over a variety of healthy Acropora sp. corals, including table and staghorn forms; leather corals and soft corals cover the reef, with damselfish and chromis in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'Camera pushing forward over a variety of healthy Acropora sp., corals including table and stag horn varieties. Leather coral and soft corals cover the reef with damsel fish, anthers and chromis in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Camera pushing forward over a variety of healthy Acropora sp. corals, including table and staghorn forms; leather corals and soft corals cover the reef, with damselfish, anthias and chromis in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'Slow motion of camera pushing toward stag horn corals and Xenia corals with a resident group of damselfish swimming in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Slow-motion push towards staghorn and Xenia corals with a resident group of damselfish in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'Slow motion forward push over healthy hard and soft corals in beautiful blue water with a variety of damselfish and surgeonfish in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Slow-motion forward push over healthy hard and soft corals in clear blue water, with damselfish and surgeonfish in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'Purple-tipped Costasiella sp3., also known as rouged cheeks sheep, or Ikea/Swedish sea slug sitting on a stalk of sea grass, Komodo National Park, Indonesia, Pacific Ocean':
        'Purple-tipped Costasiella nudibranch (Shaun the Sheep slug) on a seagrass blade, Komodo National Park, Indonesia, Pacific Ocean',
    'Left to right pan of traditional sarongs hanging on a line in the wind, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'Pan from left to right across traditional sarongs hanging on a line in the wind, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Moorish idols, Zanius cornutus, and anthias swim around red barrel sponges, Xestospongia muta, Komodo National Park, Indonesia, Pacific Ocean':
        'Moorish idols, Zanclus cornutus, and anthias swim around red barrel sponges, Xestospongia muta, Komodo National Park, Indonesia, Pacific Ocean',
    'Smoking local man interacts with his daughter, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'A local man smoking interacts with his daughter, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Close up of a carpenter standing atop a boat being built, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'Close-up of a carpenter standing atop a boat under construction, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A carpenter stands atop a local boat being built, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'A carpenter stands atop a local boat under construction, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A local man sitting in front of his wooden house smiles at the camera, Bontoh village, Sangeang Island, Sumbawa, Indonesia. No model release':
        'A local man sitting in front of his wooden house smiles at the camera, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A young girl happily playing in the sea, Bontoh village, Sangeang Island, Sumbawa, Indonesia. No MR':
        'A young girl playing happily in the sea, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Landscape of the brown islands of Komodo National Park, panning the camera from left to right, Komodo Island, Indonesia, Pacific Ocean':
        'Landscape of the arid islands of Komodo National Park, panning from left to right, Komodo Island, Indonesia, Pacific Ocean',
    'Eretmochelys imbricata, foraging on the reef in Raja Ampat, Indonesia, Pacific Ocean':
        'A hawksbill turtle, Eretmochelys imbricata, foraging on the reef, Raja Ampat, Indonesia, Pacific Ocean',
    'A pair of goats walk along the beach in front of a colourful sarongs on a laundry line, Bontoh village, Sangeang Island, Sumbawa, Indonesia':
        'A pair of goats walks along the beach in front of colourful sarongs on a laundry line, Bontoh village, Sangeang Island, Sumbawa, Indonesia',
    'A black goat rest atop wooden boards, Bontoh village, Sangeang island, Sumbawa, Indonesia':
        'A black goat rests atop wooden boards, Bontoh village, Sangeang Island, Sumbawa, Indonesia',
    'Moving toward a giant sweetlips, Plectorhinchus albovittatus, with a trigger fish and an angelfish in the background, Komodo National Park, Indonesia, Pacific Ocean':
        'Push towards a giant sweetlips, Plectorhinchus albovittatus, with a triggerfish and an angelfish in the background, Komodo National Park, Indonesia, Pacific Ocean',
    'A Napoleon wrasse, Cheilinus undulatus, swims along a reef toward a school of Yellowmask surgeonfish, Acanthurus mata, Komodo National Park, Indonesia, Pacific Ocean':
        'A Napoleon wrasse, Cheilinus undulatus, swims along a reef towards a school of elongate surgeonfish, Acanthurus mata, Komodo National Park, Indonesia, Pacific Ocean',
    'Following a school of blackfin or chevron barracuda, Sphyraena genie, in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Following a school of blackfin or chevron barracuda, Sphyraena qenie, in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'Close up of colourful sarongs hanging on a line flapping in the wind, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'Close-up of colourful sarongs hanging on a line flapping in the wind, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'Slow motion of camera pushing forward and up an over a branching hard coral, Acropora sp, with anthias, damselfish and other tropical fish swimming in the water column, Komodo National Park, Indonesia, Pacific Ocean':
        'Slow-motion push forward and up over branching hard coral, Acropora sp., with anthias, damselfish and other tropical fish in the water column, Komodo National Park, Indonesia, Pacific Ocean',
    'The silhouetted outline of an underwater cave opening looking from inside of the cave out toward the blue water, Sangeang Island, Sumbawa, Indonesia, Pacific Ocean':
        'Silhouetted outline of an underwater cave opening, viewed from inside the cave looking out towards blue water, Sangeang Island, Sumbawa, Indonesia, Pacific Ocean',
    'A traditional wooden boat builder descends a ladder in Bonto village, Sangeang Island, Sumbawa, Indonesia. No MR':
        'A traditional wooden boat builder descends a ladder in Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'The hull of a wooden fishing boat being built, Bontoh village, Sangeang island, Sumbawa, Indonesia, No Model Release':
        'The hull of a wooden fishing boat under construction, Bontoh village, Sangeang Island, Sumbawa, Indonesia, No Model Release',
    'A whale shark, Rhincodon typus, enters the frame in front of a bagan, a traditional Indonesian drop net fishing boat, Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'A whale shark, Rhincodon typus, enters the frame in front of a bagan, a traditional Indonesian drop net fishing boat, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'A whale shark, Rhincodon typus, enters from the right with left side of the shark showing its spots to inspect the fishing nets under a bagan, a traditional net fishing boat in Cendrawasih Bay, Papua, Indonesia, Pacific Ocean':
        'A whale shark, Rhincodon typus, enters from the right, its left flank showing its spot pattern as it inspects fishing nets beneath a bagan, a traditional drop net fishing boat, Cenderawasih Bay, Papua, Indonesia, Pacific Ocean',
    'Close up of a whale shark, Rhincodon typus, rises up to the surface for feeding, Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'Close-up of a whale shark, Rhincodon typus, rising to the surface to feed, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'Looking down on a whale shark, Rhincodon typus, swimming away from the camera , Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'Looking down on a whale shark, Rhincodon typus, swimming away from the camera, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'The front left side of a whale shark, Rhincodon typus, as it swims in the blue Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'The front left flank of a whale shark, Rhincodon typus, swimming in blue water, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'Whale shark, Rhincodon typus, approaches the camera and turns toward the fishing nets to feed, Cendrawasih Bay, Papua, Indonesia, Pacific Ocean':
        'A whale shark, Rhincodon typus, approaches the camera and turns towards the fishing nets to feed, Cenderawasih Bay, Papua, Indonesia, Pacific Ocean',
    'Two whale sharks, Rhincodon typus, eat small bait fish thrown by fishermen off of a bagan, a traditional Indonesian drop net fishing boat, Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'Two whale sharks, Rhincodon typus, feed on small bait fish thrown by fishermen from a bagan, a traditional Indonesian drop net fishing boat, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'A whale shark, Rhincodon typus, swims past the camera with right side of the shark showing its spots, Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'A whale shark, Rhincodon typus, swims past the camera with its right flank showing its spot pattern, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
    'A whale shark, Rhincodon typus, vertically feeding under a bagan, a traditional Indonesian drop net fishing boat, Cendrawasih Bay, Papua Province, Indonesia, Pacific Ocean':
        'A whale shark, Rhincodon typus, feeding vertically beneath a bagan, a traditional Indonesian drop net fishing boat, Cenderawasih Bay, Papua Province, Indonesia, Pacific Ocean',
}

EXACT[
    'A Melibe nudibranch, Melibe viridis, using its unique hooded mouth for “hood feeding” as it uses the cirri inside the mouth to sweep for benthic organisms to eat, Komodo National Park, Indonesia, Pacific Ocean'
] = MELIBE_FEED
EXACT[
    'A Melibe nudibranch, Melibe viridis, using its unique hooded mouth for “hood feeding” as it uses the cirri inside the mouth to eat a skeleton shrimp, Caprella sp.,  Komodo National Park, Indonesia, Pacific Ocean'
] = MELIBE_SHRIMP

OCTOPUS_TENT_OLD = 'A common reef octopus, Octopus cyanea, hunting for food using tent or parachute fishing technique in coral rubble while small groupers and goatfish watch waiting for potential prey to be flushed out, Komodo National Park, Indonesia, Pacific Ocean'
OCTOPUS_RUBBLE_OLD = 'A common reef octopus, Octopus cyanea, hunting for food in coral rubble while small groupers and goatfish watch waiting for potential prey to be flushed out, Komodo National Park, Indonesia, Pacific Ocean'
EXACT[OCTOPUS_TENT_OLD] = OCTOPUS_TENT
EXACT[OCTOPUS_RUBBLE_OLD] = OCTOPUS_RUBBLE

MORAY_OLD = 'A honeycomb moray, Gymnothorax favagineus, looks out from an overhang surrounded by a school of ring-tailed cardinal fish, Ostorhinchus aureus, and other cardinal species, and a lion fish above, Komodo National Park, Indonesia, Pacific Ocean'
EXACT[MORAY_OLD] = MORAY_CARDINAL
EXACT['A honeycomb moray, Gymnothorax favagineus, lit from the left, looks out from an overhang surrounded by a school of ring-tailed cardinal fish, Ostorhinchus aureus, and other cardinal species, Komodo National Park, Indonesia, Pacific Ocean'] = MORAY_CARDINAL_LIT
EXACT['Camera pushes toward a honeycomb moray, Gymnothorax favagineus, looking out from an overhang surrounded by a school of ring-tailed cardinal fish, Ostorhinchus aureus, and other cardinal species, Komodo National Park, Indonesia, Pacific Ocean'] = (
    'Camera pushes towards a honeycomb moray, Gymnothorax favagineus, looking out from an overhang, '
    'surrounded by a school of ringtail cardinalfish, Ostorhinchus aureus, and other cardinalfish, '
    'Komodo National Park, Indonesia, Pacific Ocean'
)

GREY_OLD = 'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of rainbow runners, Elagatis bipinnulata, who rub against the shark to remove parasites from their skin, with blue and yellow fusiliers, Caesio teres, in the background, the shark dives down after the rainbow runners annoy it, Komodo National Park, Indonesia, Pacific Ocean'
GREY_OLD2 = 'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of rainbow runners, Elagatis bipinnulata, who rub against the shark to remove parasites from their skin, with blue and yellow fusiliers, Caesio teres, in the background, Komodo National Park, Indonesia, Pacific Ocean'
GREY_OLD3 = 'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of rainbow runners, Elagatis bipinnulata, who rub against the shark to remove parasites from their skin, Komodo National Park, Indonesia, Pacific Ocean'
EXACT[GREY_OLD] = GREY_REEF_RUNNERS_DIVE
EXACT[GREY_OLD2] = GREY_REEF_RUNNERS
EXACT[GREY_OLD3] = (
    'A grey reef shark, Carcharhinus amblyrhynchos, surrounded by a school of rainbow runners, '
    'Elagatis bipinnulata, rubbing against it, Komodo National Park, Indonesia, Pacific Ocean'
)

NABIRE: dict[str, str] = {
    'Delivery Motorbike Driver Entering Frame View from behind, fish market of Nabire, Central Papua, Indonesia (no MR)':
        'Delivery motorbike driver entering frame, viewed from behind, Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'Indonesian wooden fishing vessel, Nabire, Central Papua, Indonesia':
        'Indonesian wooden fishing vessel, Nabire, Central Papua, Indonesia',
    'Tuna on a Stand, early in the morning in a fish Market, Nabire, Central Papua, Indonesia':
        'Tuna on display early in the morning, Nabire fish market, Central Papua, Indonesia',
    'Fish Market Vendor Cutting Tuna Early in the Morning in the Fish Market, Nabire, Central Papua, Indonesia (no MR)':
        'Fish market vendor cutting tuna early in the morning, Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'Fish Market Vendor Cutting Tuna Early in the Morning in the Fish Market, Nabire, West Papua, Indonesia (no MR)':
        'Fish market vendor cutting tuna early in the morning, Nabire fish market, West Papua, Indonesia (No Model Release)',
    'People and Vendors In Nabire Fish Market, Central Papua, Indonesia (no MR)':
        'People and vendors in Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'Panning up from live Chickens held by a vendor in the market of Nabire, Central Papua, Indonesia (no MR)':
        'Pan up from live chickens held by a vendor, Nabire market, Central Papua, Indonesia (No Model Release)',
    'Two vendors in the market at Nabire, Central Papua, Indonesia (no MR)':
        'Two vendors in Nabire market, Central Papua, Indonesia (No Model Release)',
    'People and Vendors in the Fresh Market in Nabire, Central Papua, Indonesia (no MR)':
        'People and vendors in the fresh market in Nabire, Central Papua, Indonesia (No Model Release)',
    'Morning Vendors Selling Live Chickens in Nabire Market, Central Papua, Indonesia (no MR)':
        'Morning vendors selling live chickens in Nabire market, Central Papua, Indonesia (No Model Release)',
    'Vendors Selling Fish in the Fish Market in Nabire, Central Papua, Indonesia (no MR)':
        'Vendors selling fish in Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'Vendors Offloading Delivery at the Fish Market in Nabire, Central Papua, Indonesia  (no MR)':
        'Vendors offloading a delivery at Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'Small fish on a stand for sale in Nabire fresh market, Nabire, Central Papua, Indonesia (no MR)':
        'Small fish on a stand for sale in Nabire fresh market, Central Papua, Indonesia (No Model Release)',
    'Early Morning Vendors Selling Fish in Nabire Fish Market, Central Papua, Indonesia (no MR)':
        'Early morning vendors selling fish in Nabire fish market, Central Papua, Indonesia (No Model Release)',
    'People Selling and Buying Vegetables in a Fresh Market in Nabire, Central Papua, Indonesia (no MR)':
        'People selling and buying vegetables in a fresh market in Nabire, Central Papua, Indonesia (No Model Release)',
    'Vendors selling durians in Nabire Market, Central Papua, Indonesia (no MR)':
        'Vendors selling durians in Nabire market, Central Papua, Indonesia (No Model Release)',
    'Vendors and durians in Nabire Market, Central Papua, Indonesia (no MR)':
        'Vendors and durians in Nabire market, Central Papua, Indonesia (No Model Release)',
    'Red Chillies in Nabire Fresh Market, Central Papua, Indonesia (no MR)':
        'Red chillies in Nabire fresh market, Central Papua, Indonesia (No Model Release)',
    'Man Checking Coconut in Nabire market, Central Papua, Indonesia (no MR)':
        'Man inspecting coconuts in Nabire market, Central Papua, Indonesia (No Model Release)',
    'People Smiling at the camera in Nabire Market, Central Papua, Indonesia (no MR)':
        'People smiling at the camera in Nabire market, Central Papua, Indonesia (No Model Release)',
}
EXACT.update(NABIRE)

# Lowercase Nabire fish vendor variants
EXACT[
    'Fish market vendor cutting tuna early in the morning in the fish market, Nabire, Central Papua, Indonesia (no MR)'
] = 'Fish market vendor cutting tuna early in the morning, Nabire fish market, Central Papua, Indonesia (No Model Release)'


def read_csv(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    if raw[:3] == b'\xef\xbb\xbf':
        text = raw.decode('utf-8-sig')
    else:
        text = raw.decode('utf-8', errors='replace')
    lines = text.splitlines()
    delimiter = '\t' if lines and lines[0].count('\t') > lines[0].count(',') else ','
    return list(csv.reader(lines, delimiter=delimiter))


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def polish_description(text: str) -> str:
    if not text or not text.strip():
        return text

    original = text.strip()
    if original in EXACT:
        return EXACT[original]

    d = original

    # Strip stray characters
    d = re.sub(r'\s+ay\s*$', '', d, flags=re.I)

    # Model release normalisation
    d = re.sub(r'\s*\(no MR\)\s*', ' (No Model Release)', d, flags=re.I)
    d = re.sub(r'\.?\s*No MR\.?\s*$', ', No Model Release', d, flags=re.I)
    d = re.sub(r'No model release', 'No Model Release', d, flags=re.I)

    # Duplicate trailing location blocks
    d = re.sub(
        r'(Cend(?:er)?rawasih Bay, [^,]+, Indonesia, Pacific Ocean)\s+\1',
        r'\1',
        d,
        flags=re.I,
    )

    # Spacing and punctuation
    d = re.sub(r',([A-Za-z])', r', \1', d)
    d = re.sub(r'\s+,', ',', d)
    d = re.sub(r'\s+', ' ', d)
    d = re.sub(r'\s+,', ',', d)
    d = re.sub(r',\s*,', ',', d)
    d = re.sub(r' \.', '.', d)

    # Repeated words
    d = re.sub(r'\bacross across\b', 'across', d, flags=re.I)
    d = re.sub(r'\band and\b', 'and', d, flags=re.I)

    replacements = [
        (r'\bClose up\b', 'Close-up'),
        (r'\bclose up\b', 'close-up'),
        (r'\bwhite tip reef shark\b', 'whitetip reef shark'),
        (r'\blion fish\b', 'lionfish'),
        (r'\bbutterfly fish\b', 'butterflyfish'),
        (r'\btrigger fish\b', 'triggerfish'),
        (r'\bdamsel fish\b', 'damselfish'),
        (r'\bsea grass\b', 'seagrass'),
        (r'\bstag horn\b', 'staghorn'),
        (r'\banemone fish\b', 'anemonefish'),
        (r'\bring-tailed cardinal fish\b', 'ringtail cardinalfish'),
        (r'\bcardinal species\b', 'cardinalfish'),
        (r'\bSphyraena genie\b', 'Sphyraena qenie'),
        (r'\bSolenostomus paegnius\b', 'Solenostomus paenia'),
        (r'\bfusilliers\b', 'fusiliers'),
        (r'\bfusillier\b', 'fusilier'),
        (r'\boff of\b', 'off'),
        (r'\btoward\b', 'towards'),
        (r'\bcolorful\b', 'colourful'),
        (r'\bcolor\b', 'colour'),
        (r'\bSangeang island\b', 'Sangeang Island'),
        (r'\bBonto village\b', 'Bontoh village'),
        (r'\bcurrent swept\b', 'current-swept'),
        (r'\bPan left to right\b', 'Pan from left to right'),
        (r'\bpanning left to right\b', 'panning from left to right'),
        (r'\bPanning left to right\b', 'Panning from left to right'),
        (r'\bfield of acropora\b', 'field of Acropora'),
        (r'\bhealthy acropora\b', 'healthy Acropora'),
        (r'\bAcropora sp,\b', 'Acropora sp.,'),
        (r'\bleptolepis,Cendrawasih\b', 'leptolepis, Cenderawasih'),
        (r'\bleptolepis,Cendrawasih\b', 'leptolepis, Cenderawasih'),
        (r'\bCendrawasih Bay\b', 'Cenderawasih Bay'),
        (r'\bIndo Pacific Giant Sponges\b', 'Indo-Pacific giant barrel sponges'),
        (r'\bSlow motion\b', 'Slow-motion'),
        (r'\bslow motion\b', 'slow-motion'),
        (r',with ', ', with '),
        (r'shark,Triaenodon', 'shark, Triaenodon'),
        (r'\. Komodo National Park', ', Komodo National Park'),
        (r'close to the bottom\. Cenderawasih', 'close to the bottom, Cenderawasih'),
        (r'splits past the camera', 'parts around the camera'),
        (r'A school of yellow stripe scad swim\b', 'A school of yellowstripe scad swims'),
        (r'A school of yellow stripe scad, Selaroides leptolepis, swimming\b',
         'A school of yellowstripe scad, Selaroides leptolepis, swimming'),
        (r'Swimming through a school of yellow stripe scad\b',
         'Swimming through a school of yellowstripe scad'),
        (r'A whale shark, Rhincodon typus, swims into the frame from the top and exits from the bottom as seen from above\b',
         'A whale shark, Rhincodon typus, enters the frame from above and exits below, viewed from above'),
        (r'A whale shark, Rhincodon typus, vertically feeding\b',
         'A whale shark, Rhincodon typus, feeding vertically'),
        (r'Camera pans up from the fins along the back\b',
         'Camera pans up along the dorsal surface'),
        (r'A whale shark, Rhincodon typus,  feeds vertically\b',
         'A whale shark, Rhincodon typus, feeds vertically'),
        (r'A whale shark, Rhincodon typus, sucking at a net\b',
         'A whale shark, Rhincodon typus, suction-feeding at a net'),
        (r'camera showcasing the spots\b', 'camera highlighting the spot pattern'),
        (r'beautful\b', 'beautiful'),
        (r'\bsea breams\b', 'sea bream'),
        (r', hiding behind corals,', ', hides behind corals,'),
        (r'\bA school of circular spadefish or batfish, Platax orbicularis, swim\b',
         'A school of circular spadefish or batfish, Platax orbicularis, swims'),
        (r'\bParrotfish \(Scarus tricolor\), sea bream \(Monotaxis heterodon\), chromis and ribbon sweetlips \(Plectorhinchus polytaenia\) on a coral reef in Komodo\b',
         'Parrotfish (Scarus tricolor), sea bream (Monotaxis heterodon), chromis and ribbon sweetlips (Plectorhinchus polytaenia) on a coral reef, Komodo'),
    ]

    for pattern, repl in replacements:
        d = re.sub(pattern, repl, d, flags=re.I if pattern.islower() else 0)

    # Sentence-case editorial Nabire leftovers still in title case
    if re.search(r'\b(Fish Market|Early Morning|People Selling)\b', d):
        lowered = d[0].lower() + d[1:] if d else d
        d = lowered.replace('fish market', 'fish market')

    return d.strip()


def main() -> int:
    dry_run = '--dry-run' in sys.argv
    rows = read_csv(MASTER)
    if not rows:
        print('Empty CSV')
        return 1

    header = rows[0]
    try:
        desc_idx = header.index('Description')
    except ValueError:
        print('Description column not found')
        return 1

    changed = 0
    for row in rows[1:]:
        if len(row) <= desc_idx:
            continue
        old = row[desc_idx]
        new = polish_description(old)
        if new != old:
            row[desc_idx] = new
            changed += 1

    print(f'Polished {changed} of {len(rows) - 1} descriptions')
    if dry_run:
        return 0

    write_csv(MASTER, rows)
    print(f'Wrote {MASTER}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
