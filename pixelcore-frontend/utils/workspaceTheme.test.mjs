import assert from "node:assert/strict";
import test from "node:test";
import { businessThemeStyle } from "./businessTheme.js";
import {
  isWorkspaceThemeRoute,
  resolveWorkspaceTheme,
  workspaceThemePreference,
} from "./workspaceTheme.js";

function luminance(value) {
  const [h, s, l] = value
    .replace(/^hsl\(|\)$/g, "")
    .split(/\s+/)
    .map(Number.parseFloat);
  const saturation = s / 100;
  const lightness = l / 100;
  const a = saturation * Math.min(lightness, 1 - lightness);
  const channels = [0, 8, 4].map((n) => {
    const k = (n + h / 30) % 12;
    const channel = lightness - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
    return channel <= 0.04045
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function contrast(first, second) {
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("system preference follows the device until a manual preference is chosen", () => {
  assert.equal(resolveWorkspaceTheme("system", true), "dark");
  assert.equal(resolveWorkspaceTheme("system", false), "light");
  assert.equal(resolveWorkspaceTheme("light", true), "light");
  assert.equal(resolveWorkspaceTheme("dark", false), "dark");
  assert.equal(workspaceThemePreference("invalid"), "system");
  assert.equal(resolveWorkspaceTheme(null, true), "dark");
});

test("workspace preferences apply only to administrative route boundaries", () => {
  for (const path of [
    "/workspace",
    "/workspace/analytics",
    "/settings/identity",
  ])
    assert.equal(isWorkspaceThemeRoute(path), true);
  for (const path of [
    "/site/shop",
    "/login",
    "/pos-terminal",
    "/workspace-other",
    "/settings-preview",
  ])
    assert.equal(isWorkspaceThemeRoute(path), false);
});

test("dark surfaces meet text, action, and field-boundary contrast", () => {
  for (const primary of [
    "#165B4C",
    "#000000",
    "#FFFFFF",
    "#1700FF",
    "#FFEC00",
    "#A2278D",
  ]) {
    const style = businessThemeStyle(
      { branding: { primary_color: primary } },
      { workspace: true, dark: true },
    );
    for (const [foreground, background] of [
      ["--foreground", "--background"],
      ["--card-foreground", "--card"],
      ["--muted-foreground", "--card"],
      ["--popover-foreground", "--popover"],
      ["--primary-foreground", "--primary"],
      ["--destructive-foreground", "--destructive"],
    ])
      assert.ok(
        contrast(style[foreground], style[background]) >= 4.5,
        `${primary}: ${foreground}/${background}`,
      );
    assert.ok(contrast(style["--primary"], style["--card"]) >= 3);
    assert.ok(contrast(style["--input"], style["--card"]) >= 3);
  }
});

test("dark mapping preserves brand hue and shape; light mode restores business colors", () => {
  const identity = {
    branding: {
      primary_color: "#A2278D",
      border_radius: "large",
      workspace: { header_color: "#FAF0E7", background_color: "#FEF9F0" },
    },
  };
  const light = businessThemeStyle(identity, { workspace: true });
  const dark = businessThemeStyle(identity, { workspace: true, dark: true });
  assert.equal(
    dark["--primary"].split(" ")[0],
    light["--primary"].split(" ")[0],
  );
  assert.equal(dark["--radius"], light["--radius"]);
  assert.equal(light["--workspace-header"], "#FAF0E7");
  assert.notEqual(dark["--workspace-header"], light["--workspace-header"]);
  assert.deepEqual(
    businessThemeStyle(identity, { workspace: false, dark: true }),
    businessThemeStyle(identity),
  );
  assert.equal(
    businessThemeStyle(identity, { workspace: true, dark: false })["--card"],
    "0 0% 100%",
  );
});
