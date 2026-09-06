import { useState } from 'react';
import type { DrivingStyle } from '../game/types';
import type { CareerSetup } from '../game/careerEngine';
import { NATIONALITIES } from '../data/nationalities';
import { makeSeed } from '../game/random';

const STYLE_CARDS: {
  id: DrivingStyle;
  name: string;
  blurb: string;
  pros: string[];
  cons: string[];
}[] = [
  {
    id: 'speed',
    name: 'Speed',
    blurb: 'Natural raw pace.',
    pros: ['Qualifying', 'Overtaking', 'Spectacular days'],
    cons: ['Crashes more', 'Less consistent']
  },
  {
    id: 'technical',
    name: 'Technical',
    blurb: 'Precise and analytical.',
    pros: ['Car development', 'Tyre management', 'Great in bad cars'],
    cons: ['Slow to find raw pace']
  },
  {
    id: 'physical',
    name: 'Physical',
    blurb: 'Aggressive and resilient.',
    pros: ['Starts', 'Wheel-to-wheel', 'Difficult conditions'],
    cons: ['Weaker on Saturdays']
  }
];

export function SetupScreen({ onStart }: { onStart: (setup: CareerSetup) => void }) {
  const [name, setName] = useState('');
  const [number, setNumber] = useState(27);
  const [nationality, setNationality] = useState('GB');
  const [style, setStyle] = useState<DrivingStyle>('speed');
  const [seed, setSeed] = useState(makeSeed());

  const trimmed = name.trim();
  const valid = trimmed.length > 0 && number >= 2 && number <= 99;

  return (
    <div className="setup">
      <header className="setup-head">
        <h1>Who Are You?</h1>
        <p>Sixteen years old. One dream: Formula 1.</p>
        <div className="rule" />
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (valid) onStart({ name: trimmed, number, nationality, style, seed: seed.trim() || makeSeed() });
        }}
      >
        <div className="field-row">
          <div className="field">
            <label htmlFor="name">Name</label>
            <input
              id="name"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your driver's name"
              maxLength={28}
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="number">Number</label>
            <input
              id="number"
              className="input"
              type="number"
              min={2}
              max={99}
              value={number}
              onChange={(e) => setNumber(Number(e.target.value))}
            />
          </div>
        </div>
        {/* #1 is reserved: the reigning World Champion earns the right to it. */}
        <p className="hint" style={{ marginTop: -12, marginBottom: 20 }}>
          2&ndash;99. Number 1 belongs to the reigning World Champion &mdash; win it and you can run it.
        </p>

        <div className="field">
          <label htmlFor="nat">Nationality</label>
          <select
            id="nat"
            className="select"
            value={nationality}
            onChange={(e) => setNationality(e.target.value)}
          >
            {[...NATIONALITIES]
              .sort((a, b) => a.name.localeCompare(b.name))
              .map((n) => (
                <option key={n.code} value={n.code}>
                  {n.flag} {n.name}
                </option>
              ))}
          </select>
        </div>

        <div className="field">
          <label>Driving style</label>
          <div className="styles">
            {STYLE_CARDS.map((card) => (
              <button
                key={card.id}
                type="button"
                className={`style-card${style === card.id ? ' is-active' : ''}`}
                onClick={() => setStyle(card.id)}
                aria-pressed={style === card.id}
              >
                <h3>{card.name}</h3>
                <ul>
                  {card.pros.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                  {card.cons.map((c) => (
                    <li className="con" key={c}>
                      {c}
                    </li>
                  ))}
                </ul>
              </button>
            ))}
          </div>
        </div>

        <div className="field">
          <label htmlFor="seed">Career seed</label>
          <div className="field-row">
            <input
              id="seed"
              className="input"
              value={seed}
              onChange={(e) => setSeed(e.target.value.toUpperCase())}
              maxLength={16}
            />
            <button type="button" className="btn" onClick={() => setSeed(makeSeed())}>
              Reroll
            </button>
          </div>
          <p className="hint">
            The whole universe comes from this &mdash; your hidden potential, how the teams develop, who your
            rivals are. Share a seed to race the same world as someone else.
          </p>
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={!valid}>
          Start your career
        </button>
      </form>
    </div>
  );
}
