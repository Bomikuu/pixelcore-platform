const failure = (code, message, status = 0) =>
  Object.assign(new Error(message), {
    code,
    status,
    retryable: !status || status >= 500,
  });
const sameIdentity = (left, right) =>
  left &&
  right &&
  ["hostId", "organizationId", "actorId", "revision"].every(
    (key) => left[key] === right[key],
  );
const uuid = (value) => {
  if (
    typeof value !== "string" ||
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
      value,
    )
  )
    throw failure("INVALID_PARAMETER", "Invalid resource identifier.");
  return value;
};
export const pixelCoreSmokeyOperation = ({
  operation,
  identity,
  params = {},
  body,
}) => {
  const business = "businesses/" + uuid(identity.organizationId) + "/";
  const resource = (prefix, identifier) =>
    prefix + "/" + uuid(identifier) + "/";
  let path,
    method = "GET";
  switch (operation) {
    case "integration.get":
      return { path: business + "smokey-integration/", method };
    case "module.enable":
      return {
        path: business + "capabilities/smokey/",
        method: "PATCH",
        body: { status: "active" },
      };
    case "settings.get":
      path = "settings/";
      break;
    case "settings.update":
      path = "settings/";
      method = "PATCH";
      break;
    case "connections.list":
      path = "connections/";
      break;
    case "connections.create":
      path = "connections/";
      method = "POST";
      break;
    case "connections.update":
      path = resource("connections", params.connectionId);
      method = "PATCH";
      break;
    case "connections.delete":
      path = resource("connections", params.connectionId);
      method = "DELETE";
      break;
    case "connections.models":
      path = resource("connections", params.connectionId) + "models/";
      break;
    case "connections.check":
      path = resource("connections", params.connectionId) + "check/";
      method = "POST";
      break;
    case "models.discover":
      path = "models/";
      method = "POST";
      break;
    case "generations.create":
      path = "generations/";
      method = "POST";
      break;
    case "generations.get":
      path = resource("generations", params.generationId);
      break;
    case "generations.cancel":
      path = resource("generations", params.generationId) + "cancel/";
      method = "POST";
      break;
    case "reports.list":
      path = "reports/";
      break;
    case "reports.get":
      path = resource("reports", params.reportId);
      break;
    case "reports.delete":
      path = resource("reports", params.reportId);
      method = "DELETE";
      break;
    case "reports.rows":
      if (
        typeof params.tableKey !== "string" ||
        !/^[a-z][a-z0-9_]{0,63}$/.test(params.tableKey)
      )
        throw failure("INVALID_PARAMETER", "Invalid report table.");
      path =
        resource("reports", params.reportId) +
        "tables/" +
        params.tableKey +
        "/";
      break;
    case "usage.get":
      path = "usage/";
      break;
    case "asset.get":
      path = "asset/";
      break;
    case "asset.upload":
      path = "asset/";
      method = "POST";
      break;
    default:
      throw failure("INVALID_OPERATION", "Unsupported assistant operation.");
  }
  const query = new URLSearchParams();
  if (operation === "reports.rows") {
    if (params.page_size !== undefined) {
      const size = String(params.page_size);
      if (!["20", "50", "100"].includes(size))
        throw failure("INVALID_PARAMETER", "Invalid report page size.");
      query.set("page_size", size);
    }
    if (params.search !== undefined) {
      if (typeof params.search !== "string" || params.search.length > 100)
        throw failure(
          "INVALID_PARAMETER",
          "Search must be at most 100 characters.",
        );
      query.set("search", params.search);
    }
  }
  for (const key of ["offset", "date_from", "date_to"]) {
    if (params[key] === undefined) continue;
    const value = String(params[key]);
    if (
      key === "offset"
        ? !/^\d+$/.test(value)
        : !/^\d{4}-\d{2}-\d{2}$/.test(value)
    )
      throw failure("INVALID_PARAMETER", "Invalid report range.");
    query.set(key, value);
  }
  return {
    path: business + "smokey/" + path + (query.size ? "?" + query : ""),
    method,
    body,
  };
};
export const createPixelCoreSmokeyAdapter = ({
  apiFetch,
  currentContext,
  navigate,
  sourceOrigin,
}) => ({
  contractVersion: { major: 1, minor: 0 },
  navigate,
  resolveSourceLink: ({ href }) => {
    if (
      typeof href !== "string" ||
      !/^\/workspace(?:\/|$)/.test(href) ||
      href.includes("\\")
    )
      return null;
    const origin = new URL(sourceOrigin);
    const url = new URL(href, origin);
    return url.origin === origin.origin ? url.href : null;
  },
  async request(request) {
    const check = () => {
      if (!sameIdentity(request.identity, currentContext()?.identity))
        throw failure("STALE_CONTEXT", "Your business context changed.");
      if (request.signal?.aborted)
        throw failure("ABORTED", "The request was stopped.");
    };
    check();
    const operation = pixelCoreSmokeyOperation(request);
    const headers =
      request.operation === "generations.create" && request.idempotencyKey
        ? { "Idempotency-Key": request.idempotencyKey }
        : {};
    try {
      const result = await apiFetch(operation.path, {
        method: operation.method,
        body: operation.body,
        headers,
        signal: request.signal,
        timeout: 15000,
        ...(request.operation === "asset.get" ? { responseType: "blob" } : {}),
      });
      check();
      return result;
    } catch (error) {
      check();
      if (error?.code === "ABORTED") throw error;
      throw failure(
        error?.data?.error?.code || error?.code || "REQUEST_FAILED",
        error?.data?.error?.message ||
          error?.message ||
          "The request could not complete.",
        error?.status || error?.response?.status || 0,
      );
    }
  },
});
