// Shared palette for the leitum demo video.
// Terminal surface is a flat GitHub-dark tone; the brand accent is the logo indigo.
export const theme = {
  accent: "#8B93FF",
  bg: "#0D1117", // page backdrop behind the terminal window
  termBg: "#0F131A", // terminal body
  chrome: "#161B22", // title bar
  border: "rgba(230,237,243,0.08)",
  fg: "#E6EDF3", // default terminal text
  dim: "#7D8590", // muted / hints
  green: "#3FB950", // success output (OK — N models)
  cyan: "#56D4DD", // questionary "?" prompt mark
  yellow: "#D29922", // warnings
  selectBg: "rgba(139,147,255,0.13)", // highlighted select row
  lights: { red: "#FF5F57", yellow: "#FEBC2E", green: "#28C840" },
} as const;
