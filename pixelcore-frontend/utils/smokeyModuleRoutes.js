const sections = new Set([
  "overview",
  "assistant",
  "reports",
  "connections",
  "appearance",
  "usage",
]);
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export const parseSmokeyRoute = (path) => {
  const tail = path.replace(/^\/workspace\/smokey\/?/, "").split("/");
  const section = sections.has(tail[0]) ? tail[0] : "overview";
  return {
    section,
    ...(section === "reports" && uuid.test(tail[1] || "")
      ? { reportId: tail[1] }
      : {}),
  };
};
export const smokeyRoutePath = (route) => {
  const section = sections.has(route.section) ? route.section : "overview";
  return (
    "/workspace/smokey" +
    (section === "overview"
      ? ""
      : "/" +
        section +
        (section === "reports" && uuid.test(route.reportId || "")
          ? "/" + route.reportId
          : ""))
  );
};
