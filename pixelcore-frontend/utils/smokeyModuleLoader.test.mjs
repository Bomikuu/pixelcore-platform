import test from "node:test";
import assert from "node:assert/strict";
import {
  validateSmokeyManifest,
  validateSmokeyExports,
  loadPixelCoreSmokeyModule,
} from "./smokeyModuleLoader.js";
const url = "https://host.test/smokey-assets/channels/stable-v1.json";
const manifest = {
  schemaVersion: 1,
  release: "1.0.0",
  adapter: { major: 1, minMinor: 0 },
  hostApi: { major: 1, minMinor: 0 },
  entry: "../releases/1.0.0/smokey.hash.mjs",
  stylesheet: "../releases/1.0.0/styles.hash.css",
  assets: "../releases/1.0.0/assets/",
};
test("only compatible releases confined to the host asset directory load", () => {
  assert.equal(
    validateSmokeyManifest(manifest, url).entry,
    "https://host.test/smokey-assets/releases/1.0.0/smokey.hash.mjs",
  );
  for (const entry of [
    "//evil.test/module.mjs",
    "https://evil.test/module.mjs",
    "../../../auth/module.mjs",
    "../releases/2.0.0/module.mjs",
    "../releases/1.0.0/%2fmodule.mjs",
    "../releases/1.0.0/module.mjs?token=1",
  ])
    assert.throws(() => validateSmokeyManifest({ ...manifest, entry }, url), {
      code: "INVALID_MODULE",
    });
  for (const change of [
    { schemaVersion: 2 },
    { hostApi: { major: 2, minMinor: 0 } },
    { adapter: { major: 1, minMinor: 1 } },
    { assets: "../releases/1.0.0/assets" },
    { stylesheet: "../releases/1.0.0/styles.js" },
  ])
    assert.throws(
      () => validateSmokeyManifest({ ...manifest, ...change }, url),
      { code: "INVALID_MODULE" },
    );
  assert.throws(() => validateSmokeyExports({}, "1.0.0"), {
    code: "INVALID_MODULE",
  });
  assert.throws(
    () =>
      validateSmokeyExports(
        {
          sdkVersion: "2.0.0",
          contractVersion: { major: 1 },
          mountSmokey() {},
        },
        "1.0.0",
      ),
    { code: "INVALID_MODULE" },
  );
  validateSmokeyExports(
    { sdkVersion: "1.0.0", contractVersion: { major: 1 }, mountSmokey() {} },
    "1.0.0",
  );
});
test("network and MIME failures stay retryable and import no module", async () => {
  const originalFetch = globalThis.fetch,
    originalLocation = globalThis.location;
  globalThis.location = { href: url, origin: "https://host.test" };
  try {
    globalThis.fetch = async () => new Response("offline", { status: 503 });
    await assert.rejects(loadPixelCoreSmokeyModule({ manifestUrl: url }), {
      code: "INVALID_MODULE",
    });
    globalThis.fetch = async (asset, options) =>
      options.method === "HEAD"
        ? new Response("", {
            headers: {
              "content-type": String(asset).endsWith(".css")
                ? "text/html"
                : "application/javascript",
            },
          })
        : new Response(JSON.stringify(manifest), {
            headers: { "content-type": "application/json" },
          });
    await assert.rejects(
      loadPixelCoreSmokeyModule({ manifestUrl: url }),
      /styles could not load/,
    );
    globalThis.fetch = async (_url, options) =>
      options.method === "HEAD"
        ? new Response("", { headers: { "content-type": "text/html" } })
        : new Response(JSON.stringify(manifest), {
            headers: { "content-type": "application/json" },
          });
    await assert.rejects(loadPixelCoreSmokeyModule({ manifestUrl: url }), {
      code: "INVALID_MODULE",
    });
    await assert.rejects(
      loadPixelCoreSmokeyModule({
        manifestUrl: "https://evil.test/channels/stable-v1.json",
      }),
      { code: "INVALID_MODULE" },
    );
  } finally {
    globalThis.fetch = originalFetch;
    if (originalLocation === undefined) delete globalThis.location;
    else globalThis.location = originalLocation;
  }
});
