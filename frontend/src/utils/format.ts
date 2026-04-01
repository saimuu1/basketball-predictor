/**
 * Strips the mascot/nickname from an ESPN full team name so only the
 * school/city name is shown. e.g. "Duke Blue Devils" → "Duke",
 * "St. John's Red Storm" → "St. John's", "San Diego State Aztecs" → "San Diego State".
 *
 * Strategy: try to match and strip the longest-known mascot suffix first.
 * Falls back to dropping everything after the first word for unknown names.
 */
const MASCOTS: string[] = [
  // multi-word mascots must come before their component words
  'blue devils', 'red storm', 'horned frogs', 'crimson tide', 'tar heels',
  'golden eagles', 'golden gophers', 'golden flashes', 'golden grizzlies',
  'golden bears', 'golden hurricane', 'golden panthers', 'golden tigers',
  'green wave', 'scarlet knights', 'flying dutchmen', 'running rebels',
  'mountain hawks', 'big green', 'red raiders', 'red foxes',
  'orange crush', 'blue hens', 'blue hawks', 'blue demons', 'blue tigers',
  'brown bears', 'black bears', 'black knights', 'ram eagles',
  'sea hawks', 'river hawks', 'sky hawks', 'war eagles',
  'mean green', 'mid-majors', 'wolf pack', 'sun devils', 'road runners',
  'fighting irish', 'fighting illini', 'fighting hawks',
  'fighting camels', 'fighting saints',
  'aggies', 'aztecs', 'badgers', 'bears', 'beavers', 'bengals',
  'blue jays', 'bobcats', 'bonnies', 'braves', 'broncos', 'broncs',
  'bruins', 'buccaneers', 'buckeyes', 'buffaloes', 'bulldogs', 'bulls',
  'camels', 'cardinals', 'cavaliers', 'chippewas', 'colonels',
  'colonials', 'comets', 'commodores', 'cougs', 'cougars', 'cowboys',
  'crabtrees', 'crows', 'crusaders', 'cyclones', 'ducks', 'eagles',
  'engineers', 'falcons', 'firebirds', 'flames', 'flyers', 'friars',
  'gauchos', 'gaels', 'gators', 'govs', 'greyhounds', 'grizzlies',
  'hawkeyes', 'hawks', 'heels', 'hokies', 'hoyas', 'huskies',
  'ice breakers', 'jayhawks', 'jaguars', 'jaspers', 'jets',
  'keydets', 'kings', 'knights', 'lakers', 'leopards', 'lions',
  'lobos', 'longhorns', 'lynx', 'mastodons', 'matadors', 'mavericks',
  'minutemen', 'monarchs', 'monks', 'musketeers', 'mustangs',
  'nanooks', 'nittany lions', 'oaks', 'orangemen', 'orange',
  'owls', 'panthers', 'patriots', 'peacocks', 'penguins', 'pilots',
  'pirates', 'pioneers', 'privateers', 'purple aces', 'quakers',
  'racers', 'rams', 'razorbacks', 'rebels', 'retrievers', 'rockets',
  'seahawks', 'seminoles', 'settlers', 'sharks', 'shockers',
  'sioux', 'spartans', 'spiders', 'statesmen', 'steelhawks', 'stingers',
  'sun bears', 'terps', 'terrapins', 'terriers', 'tigers', 'titans',
  'tornados', 'toreros', 'trojans', 'utes', 'vikes', 'vikings',
  'violets', 'volunteers', 'vols', 'vulcans', 'wave', 'warhawks',
  'warriors', 'wildcats', 'wolf pack', 'wolves', 'wolverines',
  'yellow jackets', 'zips',
  // single-word mascots that are also common last words
  'boilermakers', 'cardinals', 'crimson',
];

// Sort longest-first so multi-word mascots are tried before single words
const SORTED_MASCOTS = MASCOTS.slice().sort((a, b) => b.length - a.length);

export function shortName(fullName: string): string {
  if (!fullName) return fullName;
  const lower = fullName.toLowerCase();
  for (const mascot of SORTED_MASCOTS) {
    if (lower.endsWith(mascot)) {
      const trimmed = fullName.slice(0, fullName.length - mascot.length).trim();
      if (trimmed) return trimmed;
    }
  }
  // Unknown mascot: strip everything after the first word
  return fullName.split(' ')[0];
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

export function formatPercent(prob: number): string {
  return `${Math.round(prob * 100)}%`;
}

export function confidenceLabel(confidence: number): {
  label: string;
  color: string;
} {
  if (confidence >= 0.65) return { label: 'High Confidence', color: 'text-emerald-600' };
  if (confidence >= 0.35) return { label: 'Moderate', color: 'text-amber-500' };
  return { label: 'Toss-up', color: 'text-rose-500' };
}

export function formatFactorValue(value: number): string {
  if (Math.abs(value) < 0.01) return '—';
  if (Math.abs(value) < 1 && Math.abs(value) > 0) return value.toFixed(3);
  return value > 0 ? `+${value.toFixed(1)}` : value.toFixed(1);
}
