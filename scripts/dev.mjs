import { spawn, spawnSync } from "node:child_process";
import { createHash, randomBytes } from "node:crypto";
import { accessSync, constants, existsSync, mkdirSync, readFileSync, rmdirSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parseEnv } from "node:util";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const backend = join(root, "pixelcore-backend");
const frontend = join(root, "pixelcore-frontend");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const python = join(backend, "venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const children = new Set();
let stopping;

// Parse dotenv files as data, never as executable shell commands. Shell values win.
const fileEnv = {};
for (const name of [".env", ".env.local"]) {
  const path = join(root, name);
  if (existsSync(path)) Object.assign(fileEnv, parseEnv(readFileSync(path, "utf8")));
}
const localEnv = { ...fileEnv, ...process.env };
const frontendPort = Number(localEnv.PIXELCORE_FRONTEND_PORT || 3001);
const backendPort = Number(localEnv.PIXELCORE_BACKEND_PORT || 8000);
const frontendUrl = `http://localhost:${frontendPort}`;
const backendUrl = `http://localhost:${backendPort}`;
const env = {
  ...localEnv,
  NODE_ENV: "development",
  NUXT_TELEMETRY_DISABLED: "1",
  PYTHONUNBUFFERED: "1",
  DJANGO_SETTINGS_MODULE: "pixelcore_backend.settings",
  DJANGO_SECRET_KEY: process.env.DJANGO_SECRET_KEY || fileEnv.DJANGO_SECRET_KEY || randomBytes(48).toString("hex"),
  DJANGO_DEBUG: "True",
  DJANGO_SECURE_SSL_REDIRECT: "False",
  DJANGO_ALLOWED_HOSTS: "localhost,127.0.0.1,.pixelcore.localhost",
  DJANGO_DB_ENGINE: "sqlite",
  CELERY_TASK_ALWAYS_EAGER: "True",
  CELERY_TASK_EAGER_PROPAGATES: "True",
  CELERY_BROKER_URL: "memory://",
  CELERY_RESULT_BACKEND: "cache+memory://",
  EMAIL_BACKEND: "django.core.mail.backends.console.EmailBackend",
  PIXELCORE_USE_S3: "False",
  PIXELCORE_COOKIE_SAMESITE: "Lax",
  PIXELCORE_FRONTEND_URL: frontendUrl,
  PIXELCORE_PUBLIC_API_URL: `${backendUrl}/api`,
  CORS_ALLOWED_ORIGINS: frontendUrl,
  CSRF_TRUSTED_ORIGINS: frontendUrl,
  NUXT_PUBLIC_API_BASE_URL: `${backendUrl}/api/`,
  NUXT_API_INTERNAL_BASE_URL: `http://127.0.0.1:${backendPort}/api/`,
  PIXELCORE_LOCAL_DEV: "1",
};

function start(command, args, cwd, keepGroup = false) {
  const child = spawn(command, args, {
    cwd, env, stdio: "inherit", detached: process.platform !== "win32",
  });
  const record = { child };
  children.add(record);
  record.done = new Promise((resolve) => {
    child.once("error", (error) => resolve({ error }));
    child.once("exit", (code, signal) => resolve({ code, signal }));
  }).then((result) => {
    if (!keepGroup) children.delete(record);
    return result;
  });
  return record;
}

async function run(command, args, cwd = root) {
  const result = await start(command, args, cwd).done;
  if (result.error) throw new Error(`Cannot run ${command}: ${result.error.message}`);
  if (result.code !== 0) throw new Error(`${command} ${args.join(" ")} failed (${result.signal || result.code}).`);
}

function signalChild(record, signal) {
  if (!record.child.pid) return;
  try {
    if (process.platform === "win32") record.child.kill(signal);
    else process.kill(-record.child.pid, signal);
  } catch (error) {
    if (error.code !== "ESRCH") console.error(`[dev] ${error.message}`);
  }
}

function stop() {
  stopping ??= (async () => {
    const active = [...children];
    for (const record of active) signalChild(record, "SIGTERM");
    let timer;
    await Promise.race([
      Promise.all(active.map((record) => record.done)),
      new Promise((resolve) => { timer = setTimeout(resolve, 5000); }),
    ]);
    clearTimeout(timer);
    // Also stop descendants of npm and Django's autoreloader.
    for (const record of active) signalChild(record, "SIGKILL");
  })();
  return stopping;
}

for (const [signal, code] of [["SIGINT", 130], ["SIGTERM", 143]]) {
  process.once(signal, () => {
    process.exitCode = code;
    console.log("\n[dev] Stopping local development servers...");
    void stop().then(() => process.exit(code));
  });
}

function fingerprint(paths) {
  const hash = createHash("sha256");
  for (const path of paths) hash.update(readFileSync(path));
  return hash.digest("hex");
}

async function installIfChanged(marker, paths, install) {
  const expected = fingerprint(paths);
  if (existsSync(marker) && readFileSync(marker, "utf8") === expected) return;
  await install();
  writeFileSync(marker, expected);
}

async function assertPortFree(port) {
  await new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", () => reject(new Error(`Port ${port} is busy. Stop the process using it, then run npm run dev again.`)));
    server.listen(port, "127.0.0.1", () => server.close(resolve));
  });
}

function ensureWritableDirectory(path) {
  mkdirSync(path, { recursive: true });
  try {
    accessSync(path, constants.W_OK);
  } catch {
    // Docker can leave empty, root-owned bind mount directories behind.
    // rmdir only removes an empty directory; existing data is preserved.
    try {
      rmdirSync(path);
      mkdirSync(path);
    } catch {
      throw new Error(`Cannot write to ${path}. Fix this directory's ownership before rerunning; Docker may have created it as root.`);
    }
  }
}

async function main() {
  const args = process.argv.slice(2);
  const seedMode = args[0] === "--seed";
  if (args.includes("--help")) {
    if (seedMode) {
      console.log("Usage: npm run seed:demo [-- --month YYYY-MM] [--owner-email EXISTING_EMAIL] [--slug DEMO_SLUG] [--fixture PATH] [--media-only]\n\nImports the bundled sample business into local SQLite after dependency and migration checks.\n--media-only restores missing demo images without refreshing activity.\nDefaults to the current month in Asia/Manila. No Docker, builds, servers, or frontend installation.");
      return;
    }
    console.log("Usage: npm run dev [-- --check]\n\nSets up local dependencies, checks Django and migration files, applies migrations,\nand starts Nuxt (:3001) and Django (:8000) with SQLite and inline Celery tasks.\n--check performs setup and migration checks without starting servers.\nRequires Node.js >=20.19, npm, and Python >=3.11 with venv/pip (or uv). No Docker required.");
    return;
  }
  if (!seedMode && args.some((arg) => arg !== "--check")) throw new Error("Unknown option. Use npm run dev -- --help.");
  const [major, minor] = process.versions.node.split(".").map(Number);
  if (major < 20 || (major === 20 && minor < 19)) throw new Error("Node.js >=20.19 is required.");
  if ([frontendPort, backendPort].some((port) => !Number.isInteger(port) || port < 1 || port > 65535) || frontendPort === backendPort) {
    throw new Error("PIXELCORE_FRONTEND_PORT and PIXELCORE_BACKEND_PORT must be distinct ports from 1 to 65535.");
  }
  if (!seedMode && !args.includes("--check")) {
    await assertPortFree(backendPort);
    await assertPortFree(frontendPort);
  }
  for (const path of (seedMode ? [join(backend, "media")] : [join(frontend, "node_modules"), join(frontend, ".nuxt"), join(backend, "media")])) {
    ensureWritableDirectory(path);
  }

  if (spawnSync(python, ["-m", "pip", "--version"], { stdio: "ignore" }).status !== 0) {
    console.log("[dev] Creating the backend virtual environment...");
    const interpreter = process.env.PYTHON || "python3";
    if (spawnSync("uv", ["--version"], { stdio: "ignore" }).status === 0) {
      await run("uv", ["venv", "--seed", "--allow-existing", "--python", interpreter, join(backend, "venv")]);
    } else {
      await run(interpreter, ["-m", "venv", join(backend, "venv")]);
    }
  }
  await run(python, ["-c", "import sys; assert sys.version_info >= (3, 11), 'Python >=3.11 is required'"]);
  await installIfChanged(
    join(backend, "venv", ".pixelcore-requirements.sha256"),
    [join(backend, "requirements.txt")],
    async () => {
      console.log("[dev] Installing backend dependencies...");
      await run(python, ["-m", "pip", "install", "-r", "requirements.txt"], backend);
    },
  );
  if (!seedMode) await installIfChanged(
    join(frontend, "node_modules", ".pixelcore-dependencies.sha256"),
    [join(frontend, "package.json"), join(frontend, "package-lock.json")],
    async () => {
      console.log("[dev] Installing frontend dependencies...");
      await run(npm, ["ci", "--no-audit", "--no-fund"], frontend);
    },
  );

  console.log("[dev] Checking Django and missing migration files...");
  await run(python, ["manage.py", "check"], backend);
  await run(python, ["manage.py", "makemigrations", "--check", "--dry-run"], backend);
  console.log("[dev] Applying pending migrations to the local SQLite database...");
  await run(python, ["manage.py", "migrate", "--noinput"], backend);
  await run(python, ["manage.py", "migrate", "--check"], backend);
  if (seedMode) {
    await run(python, ["manage.py", "seed_month_demo", ...args.slice(1)], backend);
    return;
  }
  if (args.includes("--check")) {
    console.log("[dev] Local setup and migration checks passed.");
    return;
  }

  console.log(`[dev] Frontend: ${frontendUrl}\n[dev] API: ${backendUrl}/api/\n[dev] Admin: ${backendUrl}/admin/\n[dev] SQLite and inline Celery tasks; email codes appear here. Ctrl+C stops both servers.`);
  const api = start(python, ["manage.py", "runserver", `127.0.0.1:${backendPort}`], backend, true);
  const ui = start(npm, ["run", "dev", "--", "--host", "127.0.0.1", "--port", String(frontendPort)], frontend, true);
  const result = await Promise.race([api.done, ui.done]);
  if (stopping) return;
  throw new Error(`A development server stopped unexpectedly (${result.error?.message || result.signal || result.code}).`);
}

try {
  await main();
} catch (error) {
  if (!stopping) {
    console.error(`[dev] ${error.message}`);
    process.exitCode = 1;
  }
} finally {
  await stop();
}
