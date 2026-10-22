const light = [225, 243, 232];
const dark = [12, 130, 92];
const ink = [19, 32, 57];
const rgb = (channels: number[]) => `rgb(${channels.join(', ')})`;
const luminance = (channels: number[]) => channels.map(channel => {
  const value = channel / 255;
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);

export const scoreGradient = `linear-gradient(to right, ${rgb(light)}, ${rgb(dark)})`;

export function scoreColors(value: number | null) {
  if (value === null || value <= 60) return undefined;
  const position = Math.min(1, (value - 60) / 40);
  const background = light.map((channel, index) => Math.round(channel + (dark[index] - channel) * position));
  const brightness = luminance(background);
  const whiteContrast = 1.05 / (brightness + 0.05);
  const inkContrast = (brightness + 0.05) / (luminance(ink) + 0.05);
  return { backgroundColor: rgb(background), color: whiteContrast > inkContrast ? '#fff' : rgb(ink) };
}
