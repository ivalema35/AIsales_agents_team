// Validated categorical/sequential palette (dataviz skill, references/palette.md) --
// fixed hue order, never cycled/reassigned. Shared by every chart that needs a
// categorical series color (ChannelChart, CandleChart) so "leads discovered" or
// "channel EMAIL" is always the same blue everywhere, not a redrawn palette per chart.
export const SERIES = {
  blue: "#2a78d6",    // slot 1 -- leads discovered / channel EMAIL
  orange: "#eb6834",  // slot 2 -- outreach sent / channel WHATSAPP
  aqua: "#1baf7a",    // slot 3 -- replies received
};
export const INK = { primary: "#0b0b0b", secondary: "#52514e", muted: "#898781", grid: "#e1e0d9" };
