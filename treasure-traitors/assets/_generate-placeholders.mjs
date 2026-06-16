// Generates placeholder sprite files (SVG) for islands and ships.
// Run from this folder:  node _generate-placeholders.mjs
// These are stand-ins — replace the files in islands/ and ships/ with real art.
import fs from 'node:fs';
import path from 'node:path';

const here = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const islandsDir = path.join(here, 'islands');
const shipsDir = path.join(here, 'ships');
fs.mkdirSync(islandsDir, { recursive: true });
fs.mkdirSync(shipsDir, { recursive: true });

// ---- islands: sandy disc + palms + a feature emoji (transparent bg) --------
const ISLANDS = {
  'skull-rock': '💀', 'rum-bay': '🍾', 'gold-cove': '🏛️', 'cannon-cay': '💣',
  'shark-reef': '🦈', 'monkey-isle': '🐒', 'shipwreck-point': '⚓', 'treasure-atoll': '🗿',
};
// 512x512 square, transparent, island centered with clear bottom padding
// (the game draws the treasure count + name label just below the art).
function islandSVG(emoji) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs><radialGradient id="s" cx="50%" cy="40%" r="70%">
    <stop offset="0%" stop-color="#f9ecc4"/><stop offset="70%" stop-color="#eccf8e"/><stop offset="100%" stop-color="#d9b877"/>
  </radialGradient></defs>
  <ellipse cx="256" cy="332" rx="188" ry="34" fill="#000" opacity="0.18"/>
  <ellipse cx="256" cy="312" rx="180" ry="94" fill="#b89b6a"/>
  <ellipse cx="256" cy="288" rx="166" ry="88" fill="url(#s)" stroke="#c9a063" stroke-width="6"/>
  <text x="150" y="250" font-size="104" text-anchor="middle">🌴</text>
  <text x="362" y="232" font-size="86" text-anchor="middle">🌴</text>
  <text x="256" y="302" font-size="150" text-anchor="middle">${emoji}</text>
</svg>`;
}
for (const [id, emoji] of Object.entries(ISLANDS)) {
  fs.writeFileSync(path.join(islandsDir, id + '.svg'), islandSVG(emoji), 'utf8');
}

// ---- ships: little pirate vessel tinted per color (transparent bg) ----------
const SHIPS = { red: '#e63946', blue: '#1d75d0', green: '#2a9d3a', yellow: '#f4b400', purple: '#8e44ad', orange: '#e8730c' };
function shipSVG(color) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -34 60 64">
  <path d="M-22 6 L22 6 L16 20 L-16 20 Z" fill="#7a4a22" stroke="#5b3415" stroke-width="1.5"/>
  <rect x="-22" y="1.5" width="44" height="6" rx="3" fill="#9a6a3a"/>
  <rect x="-1.2" y="-26" width="2.6" height="32" fill="#5b3b1a"/>
  <path d="M2 -24 L2 2 L22 -2 Q15 -12 2 -24 Z" fill="${color}"/>
  <path d="M-2 -22 L-2 1 L-18 -2 Q-11 -11 -2 -22 Z" fill="${color}" opacity="0.82"/>
  <path d="M2 -27 L13 -25 L2 -22 Z" fill="#15171a"/>
</svg>`;
}
for (const [name, color] of Object.entries(SHIPS)) {
  fs.writeFileSync(path.join(shipsDir, name + '.svg'), shipSVG(color), 'utf8');
}

console.log('Wrote', Object.keys(ISLANDS).length, 'island +', Object.keys(SHIPS).length, 'ship placeholder sprites.');
