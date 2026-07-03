// Fonts are loaded once at module scope (the Remotion-recommended pattern).
// JetBrains Mono drives the terminal; Urbanist SemiBold is the brand wordmark.
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";
import { loadFont as loadUrbanist } from "@remotion/google-fonts/Urbanist";

const mono = loadMono("normal", { weights: ["400", "500", "700"], subsets: ["latin"] });
const brand = loadUrbanist("normal", { weights: ["600"], subsets: ["latin"] });

export const MONO = mono.fontFamily;
export const BRAND = brand.fontFamily;
