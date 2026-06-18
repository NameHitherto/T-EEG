import type { SeedVChannel } from "@/types/seed-v";

/**
 * Top-down scalp map of the EEG electrode layout.
 *
 * Backend channel coords are polar: `x` = angle (deg, 0°=anterior), `y` =
 * normalized radius from the vertex. We convert to cartesian with anterior
 * at the top (nose up) and plot each electrode, labeling the 10-20 sites.
 */

const VIEWBOX = 100;
const CENTER = VIEWBOX / 2;
const SCALP_RADIUS = 42; // leaves room for labels inside the viewBox

function toCartesian(ch: SeedVChannel) {
  const theta = (ch.x * Math.PI) / 180;
  const r = ch.y * SCALP_RADIUS;
  return {
    cx: CENTER + r * Math.sin(theta),
    cy: CENTER - r * Math.cos(theta),
  };
}

export function ChannelTopomap({ channels }: { readonly channels: readonly SeedVChannel[] }) {
  return (
    <svg viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`} className="mx-auto h-auto w-full max-w-[280px]" role="img">
      <title>SEED-V 62-channel EEG electrode layout (10-20 system)</title>
      {/* scalp outline */}
      <circle cx={CENTER} cy={CENTER} r={SCALP_RADIUS} className="fill-muted/30 stroke-border" strokeWidth={0.8} />
      {/* nose indicator (anterior) */}
      <path d={`M ${CENTER - 4} 6 L ${CENTER} 1 L ${CENTER + 4} 6 Z`} className="fill-muted-foreground/60" />
      {/* crosshair through vertex */}
      <line
        x1={CENTER}
        y1={CENTER - SCALP_RADIUS}
        x2={CENTER}
        y2={CENTER + SCALP_RADIUS}
        className="stroke-border"
        strokeWidth={0.4}
        strokeDasharray="1 2"
      />
      <line
        x1={CENTER - SCALP_RADIUS}
        y1={CENTER}
        x2={CENTER + SCALP_RADIUS}
        y2={CENTER}
        className="stroke-border"
        strokeWidth={0.4}
        strokeDasharray="1 2"
      />

      {channels.map((ch) => {
        const { cx, cy } = toCartesian(ch);
        return (
          <g key={ch.name}>
            <circle cx={cx} cy={cy} r={1.8} className="fill-primary" />
          </g>
        );
      })}
      {channels.map((ch) => {
        const { cx, cy } = toCartesian(ch);
        return (
          <text
            key={`${ch.name}-label`}
            x={cx}
            y={cy - 2.4}
            textAnchor="middle"
            className="fill-muted-foreground"
            fontSize={2.6}
            fontWeight={500}
          >
            {ch.name}
          </text>
        );
      })}
    </svg>
  );
}
