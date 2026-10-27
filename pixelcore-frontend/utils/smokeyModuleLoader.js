const invalid = (
  message = "Smokey release is not compatible with this platform.",
) => Object.assign(new Error(message), { code: "INVALID_MODULE" });
export const validateSmokeyManifest = (
  data,
  manifestUrl,
  hostVersion = { major: 1, minor: 0 },
) => {
  const base = new URL(manifestUrl);
  if (data?.schemaVersion !== 1 || !/^\d+\.\d+\.\d+$/.test(data.release || ""))
    throw invalid();
  for (const [required, version] of [
    [data.adapter, { major: 1, minor: 0 }],
    [data.hostApi, hostVersion],
  ]) {
    if (
      !required ||
      required.major !== version.major ||
      !Number.isInteger(required.minMinor) ||
      required.minMinor < 0 ||
      required.minMinor > version.minor
    )
      throw invalid();
  }
  const urls = {};
  for (const key of ["entry", "stylesheet", "assets"]) {
    const path = data[key];
    if (
      typeof path !== "string" ||
      path.startsWith("//") ||
      path.includes("\\") ||
      /%2f|%5c/i.test(path)
    )
      throw invalid();
    const url = new URL(path, base);
    if (
      url.origin !== base.origin ||
      !url.pathname.startsWith(
        "/smokey-assets/releases/" + data.release + "/",
      ) ||
      url.search ||
      url.hash
    )
      throw invalid();
    urls[key] = url.href;
  }
  if (
    !urls.entry.endsWith(".mjs") ||
    !urls.stylesheet.endsWith(".css") ||
    !urls.assets.endsWith("/")
  )
    throw invalid();
  return { ...data, ...urls };
};
export const validateSmokeyExports = (module, release) => {
  if (
    module?.contractVersion?.major !== 1 ||
    typeof module.mountSmokey !== "function" ||
    (release && module.sdkVersion !== release)
  )
    throw invalid();
  return module;
};
export const loadPixelCoreSmokeyModule = async ({
  source,
  manifestUrl,
  hostVersion,
  signal,
}) => {
  let entry, assetsBaseUrl, stylesheetUrl, release;
  if (source === "development" && import.meta.dev) {
    entry = "/smokey-assets/dev/src/sdk/devEntry.ts";
    assetsBaseUrl = "/smokey-assets/dev/";
  } else {
    const url = new URL(manifestUrl, location.href);
    if (
      url.origin !== location.origin ||
      !url.pathname.startsWith("/smokey-assets/channels/")
    )
      throw invalid(
        "Smokey release configuration must use the platform asset origin.",
      );
    const response = await fetch(url, {
      cache: "no-cache",
      signal: signal || AbortSignal.timeout(15000),
    });
    if (!response.ok || !response.headers.get("content-type")?.includes("json"))
      throw invalid("Smokey release could not load. Please try again.");
    const manifest = validateSmokeyManifest(
      await response.json(),
      url.href,
      hostVersion,
    );
    entry = manifest.entry;
    assetsBaseUrl = manifest.assets;
    stylesheetUrl = manifest.stylesheet;
    release = manifest.release;
  }
  const response = await fetch(entry, {
    method: "HEAD",
    signal: signal || AbortSignal.timeout(15000),
  });
  if (
    !response.ok ||
    !/javascript/.test(response.headers.get("content-type") || "")
  )
    throw invalid("Smokey module service is unavailable. Please try again.");
  if (stylesheetUrl) {
    const stylesheet = await fetch(stylesheetUrl, {
      method: "HEAD",
      signal: signal || AbortSignal.timeout(15000),
    });
    if (
      !stylesheet.ok ||
      !stylesheet.headers.get("content-type")?.startsWith("text/css")
    )
      throw invalid("Smokey styles could not load. Please try again.");
  }
  let module;
  try {
    module = validateSmokeyExports(
      await import(/* @vite-ignore */ entry),
      release,
    );
  } catch {
    throw invalid(
      "Smokey module could not initialize. Please reload the assistant.",
    );
  }
  return { module, assetsBaseUrl, stylesheetUrl };
};
