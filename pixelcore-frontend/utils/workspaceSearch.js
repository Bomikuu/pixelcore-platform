import { workspaceCreateRole } from "./workspaceQuickActions.js";

export const workspaceSearchKinds = [
  { id: "products", label: "Products", module: "sell", icon: "Package" },
  { id: "promotions", label: "Promotions", module: "sell", icon: "Tags" },
  { id: "categories", label: "Categories", module: "sell", icon: "Shapes" },
  { id: "employees", label: "Employees", module: "operate", icon: "Users" },
];

export function workspaceSearchScopes(user, business) {
  const role = workspaceCreateRole(user, business);
  if (!["owner", "admin", "manager", "staff"].includes(role)) return [];
  return workspaceSearchKinds.filter(
    (kind) =>
      business?.enabled_modules?.includes(kind.module) &&
      (kind.id !== "employees" || ["owner", "admin"].includes(role)),
  );
}

export function workspaceRecordGroups(response, scopes) {
  return scopes.map((kind) => ({
    ...kind,
    items: (
      response?.groups?.find((group) => group.kind === kind.id)?.items || []
    )
      .filter((record) => record.public_id && record.name)
      .map((record) => {
        const id = encodeURIComponent(record.public_id);
        const to = {
          products: `/workspace/sell/catalog/${id}`,
          promotions: `/workspace/sell/promotions/${id}`,
          categories: `/workspace/sell/categories?edit=${id}`,
          employees: `/workspace/operate/workforce/employees/${id}`,
        }[kind.id];
        return { ...record, id: `record:${kind.id}:${record.public_id}`, to };
      }),
  }));
}
