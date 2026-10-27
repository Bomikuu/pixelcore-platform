const radiusValues = {
  none: "0px",
  small: "4px",
  medium: "8px",
  large: "12px",
  pill: "999px",
};
const borderValues = { none: "0px", thin: "1px", medium: "2px" };
const shadowValues = {
  none: "0 0 transparent",
  subtle: "0 8px 24px -18px rgb(16 42 42 / 0.28)",
  medium: "0 16px 38px -22px rgb(16 42 42 / 0.38)",
};
const contentWidths = {
  compact: "72rem",
  standard: "84rem",
  wide: "100rem",
  full: "100%",
};

const lightSurfaces = {
  "--card": "0 0% 100%",
  "--card-foreground": "174 35% 12%",
  "--popover": "0 0% 100%",
  "--popover-foreground": "174 35% 12%",
  "--secondary": "165 26% 91%",
  "--secondary-foreground": "174 35% 12%",
  "--muted": "42 18% 92%",
  "--accent": "38 92% 58%",
  "--accent-foreground": "174 35% 12%",
  "--border": "164 13% 84%",
  "--input": "164 13% 84%",
  "--destructive": "0 72% 45%",
  "--destructive-foreground": "0 0% 100%",
};

const darkSurfaces = {
  "--background": "160 24% 8%",
  "--foreground": "140 29% 94%",
  "--card": "157 23% 12%",
  "--card-foreground": "140 29% 94%",
  "--popover": "157 23% 14%",
  "--popover-foreground": "140 29% 94%",
  "--secondary": "157 24% 18%",
  "--secondary-foreground": "140 29% 94%",
  "--muted": "157 23% 14%",
  "--muted-foreground": "144 15% 73%",
  "--accent": "38 85% 65%",
  "--accent-foreground": "160 24% 8%",
  "--border": "160 20% 28%",
  "--input": "153 16% 43%",
  "--destructive": "356 76% 70%",
  "--destructive-foreground": "160 24% 8%",
  "--workspace-header": "#172620",
  "--workspace-sidebar": "#0b1914",
  "--workspace-sidebar-foreground": "#edf5ef",
  "--workspace-sidebar-muted": "#b0c3b7",
  "--workspace-sidebar-faint": "#8fa99a",
  "--workspace-sidebar-border": "#294237",
  "--workspace-sidebar-overlay": "#203a2e",
  "--surface-shadow": "0 12px 30px -18px rgb(0 0 0 / 0.6)",
};

export function hexToHslChannels(value, fallback = "171 62% 29%") {
  const match = /^#([0-9a-f]{6})$/i.exec(value || "");
  if (!match) return fallback;
  const [red, green, blue] = [0, 2, 4].map(
    (index) => Number.parseInt(match[1].slice(index, index + 2), 16) / 255,
  );
  const maximum = Math.max(red, green, blue);
  const minimum = Math.min(red, green, blue);
  const lightness = (maximum + minimum) / 2;
  const delta = maximum - minimum;
  let hue = 0;
  let saturation = 0;
  if (delta) {
    saturation = delta / (1 - Math.abs(2 * lightness - 1));
    if (maximum === red) hue = 60 * (((green - blue) / delta) % 6);
    else if (maximum === green) hue = 60 * ((blue - red) / delta + 2);
    else hue = 60 * ((red - green) / delta + 4);
  }
  if (hue < 0) hue += 360;
  return `${Math.round(hue)} ${Math.round(saturation * 100)}% ${Math.round(lightness * 100)}%`;
}

export function readableForeground(value) {
  const match = /^#([0-9a-f]{6})$/i.exec(value || "");
  if (!match) return "#FFFFFF";
  const channels = [0, 2, 4]
    .map((index) => Number.parseInt(match[1].slice(index, index + 2), 16) / 255)
    .map((channel) =>
      channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4,
    );
  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2] >
    0.42
    ? "#17312B"
    : "#FFFFFF";
}

function withAlpha(value, alpha) {
  return /^#[0-9a-f]{6}$/i.test(value || "") ? `${value}${alpha}` : value;
}

export function businessThemeStyle(identity = {}, options = {}) {
  const branding = identity.branding || {};
  const typography = branding.typography || {};
  const style = branding.style || {};
  const workspace = branding.workspace || {};
  const workspaceEnabled =
    options.workspace && workspace.use_business_branding !== false;
  const workspaceOptOut =
    options.workspace && workspace.use_business_branding === false;
  const primary = workspaceOptOut
    ? "#1C786A"
    : branding.primary_color || "#165B4C";
  const background = workspaceOptOut
    ? "#FAF9F5"
    : workspaceEnabled
      ? workspace.background_color
      : branding.background_color;
  const foreground = workspaceOptOut
    ? "#17312B"
    : branding.text_color || "#17312B";
  const muted = workspaceOptOut
    ? "#5D6D68"
    : branding.muted_text_color || "#5D6D68";
  const sidebar = workspaceOptOut
    ? "#102A2A"
    : workspace.sidebar_color || branding.secondary_color || "#17362F";
  const sidebarForeground = readableForeground(sidebar);
  const dark = options.workspace && options.dark;
  const [hue, saturation] = hexToHslChannels(primary).split(" ");
  const darkPrimary = `${hue} ${Math.max(35, Math.min(65, Number.parseInt(saturation, 10)))}% 70%`;
  return {
    ...lightSurfaces,
    "--brand-primary": primary,
    "--brand-secondary": workspaceOptOut
      ? "#102A2A"
      : branding.secondary_color || "#17362F",
    "--brand-accent": workspaceOptOut
      ? "#F5AD32"
      : branding.accent_color || "#D8922B",
    "--brand-link": workspaceOptOut ? primary : branding.link_color || primary,
    "--primary": hexToHslChannels(primary),
    "--primary-foreground": hexToHslChannels(
      readableForeground(primary),
      "0 0% 100%",
    ),
    "--ring": hexToHslChannels(primary),
    "--background": hexToHslChannels(background || "#FAF9F5", "44 33% 97%"),
    "--foreground": hexToHslChannels(foreground, "174 35% 12%"),
    "--muted-foreground": hexToHslChannels(muted, "173 10% 38%"),
    "--radius": workspaceOptOut
      ? "8px"
      : radiusValues[branding.border_radius] || "8px",
    "--button-radius": workspaceOptOut
      ? "8px"
      : radiusValues[style.button_radius] || "8px",
    "--card-radius": workspaceOptOut
      ? "12px"
      : radiusValues[style.card_radius] || "12px",
    "--input-radius": workspaceOptOut
      ? "8px"
      : radiusValues[style.input_radius] || "8px",
    "--modal-radius": workspaceOptOut
      ? "12px"
      : radiusValues[style.modal_radius] || "12px",
    "--business-border-width": workspaceOptOut
      ? "1px"
      : borderValues[style.border_width] || "1px",
    "--surface-shadow": workspaceOptOut
      ? shadowValues.subtle
      : shadowValues[style.shadow_intensity] || shadowValues.subtle,
    "--content-max-width": workspaceOptOut
      ? contentWidths.wide
      : contentWidths[style.content_width] || contentWidths.wide,
    "--business-font": workspaceOptOut
      ? "'Manrope', sans-serif"
      : `'${typography.primary_font || branding.font_family || "Manrope"}', sans-serif`,
    "--business-heading-font": workspaceOptOut
      ? "'Newsreader', serif"
      : `'${typography.heading_font || branding.heading_font_family || "Newsreader"}', serif`,
    "--business-base-size": typography.base_font_size || "16px",
    "--workspace-sidebar": sidebar,
    "--workspace-sidebar-foreground": sidebarForeground,
    "--workspace-sidebar-muted": withAlpha(sidebarForeground, "A6"),
    "--workspace-sidebar-faint": withAlpha(sidebarForeground, "66"),
    "--workspace-sidebar-border": withAlpha(sidebarForeground, "1F"),
    "--workspace-sidebar-overlay": withAlpha(sidebarForeground, "14"),
    "--workspace-header": workspace.header_color || "#FFFFFF",
    ...(dark
      ? {
          ...darkSurfaces,
          "--primary": darkPrimary,
          "--primary-foreground": "160 24% 8%",
          "--ring": darkPrimary,
          "--brand-primary": `hsl(${darkPrimary})`,
          "--brand-secondary": `hsl(${hue} 30% 57%)`,
          "--brand-link": `hsl(${darkPrimary})`,
        }
      : {}),
  };
}

export function storefrontBackgroundStyle(identity = {}) {
  const background = identity.branding?.storefront?.background || {};
  const assets = identity.branding_assets || {};
  if (background.type === "gradient")
    return {
      background: `linear-gradient(${background.gradient_angle || 135}deg, ${background.gradient_from}, ${background.gradient_to})`,
    };
  if (background.type === "image" && assets[background.asset_id]?.url)
    return {
      backgroundColor: background.color,
      backgroundImage: `url(${assets[background.asset_id].url})`,
      backgroundPosition: "center",
      backgroundSize: "cover",
      backgroundRepeat: "no-repeat",
    };
  return {
    backgroundColor:
      background.color || identity.branding?.background_color || "#FAF9F5",
  };
}
