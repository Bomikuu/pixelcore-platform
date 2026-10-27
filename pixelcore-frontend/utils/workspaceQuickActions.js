export const workspaceQuickActions = [
  {
    id: "product",
    label: "Add product",
    description: "Create a product or bookable service.",
    group: "Commerce",
    module: "sell",
    icon: "PackagePlus",
    to: "/workspace/sell/products/new",
  },
  {
    id: "promotion",
    label: "Add promotion",
    description: "Set up a discount or campaign.",
    group: "Commerce",
    module: "sell",
    icon: "Tags",
    to: "/workspace/sell/promotions/new",
  },
  {
    id: "expense",
    label: "Record expense",
    description: "Capture a business cost and receipt.",
    group: "Operations",
    module: "operate",
    icon: "ReceiptText",
    resource: "expenses",
  },
  {
    id: "invoice",
    label: "Create invoice",
    description: "Prepare a customer invoice.",
    group: "Operations",
    module: "operate",
    icon: "FileText",
    resource: "invoices",
  },
  {
    id: "quotation",
    label: "Create quotation",
    description: "Prepare a price quote for a customer.",
    group: "Operations",
    module: "operate",
    icon: "ClipboardList",
    resource: "quotations",
  },
  {
    id: "purchase-order",
    label: "Create purchase order",
    description: "Start a supplier order for stock.",
    group: "Operations",
    module: "operate",
    icon: "ShoppingCart",
    resource: "purchase-orders",
  },
  {
    id: "supplier",
    label: "Add supplier",
    description: "Save a purchasing contact.",
    group: "Operations",
    module: "operate",
    icon: "Truck",
    resource: "suppliers",
  },
  {
    id: "employee",
    label: "Add employee",
    description: "Create a workforce profile.",
    group: "Workforce",
    module: "operate",
    icon: "UserPlus",
    to: "/workspace/operate/workforce/employees/new",
  },
];

export function workspaceCreateRole(user, business) {
  if (!business?.public_id) return "";
  return (
    user?.businesses?.find(
      (membership) => membership.public_id === business.public_id,
    )?.role || ""
  );
}

export function availableWorkspaceActions(user, business) {
  if (
    !["owner", "admin", "manager"].includes(workspaceCreateRole(user, business))
  )
    return [];
  const modules = Array.isArray(business?.enabled_modules)
    ? business.enabled_modules
    : [];
  return workspaceQuickActions.filter((action) =>
    modules.includes(action.module),
  );
}

export function emptyOperationsReferences() {
  return {
    suppliers: [],
    locations: [],
    customers: [],
    categories: [],
    inventory: [],
    variants: [],
  };
}

export async function loadQuickActionReferences(
  apiFetch,
  businessId,
  resource,
  signal,
) {
  const references = emptyOperationsReferences();
  const required = {
    suppliers: [],
    expenses: ["suppliers", "expense-categories"],
    invoices: ["customers"],
    quotations: ["customers"],
    "purchase-orders": ["suppliers", "locations", "offerings"],
  }[resource];
  if (!required) throw new Error("This create action is not available.");
  const responses = await Promise.all(
    required.map(async (endpoint) => {
      const records = [];
      for (let page = 1; page <= 100; page += 1) {
        const response = await apiFetch(
          `businesses/${businessId}/${endpoint}/`,
          {
            query: { page, page_size: 100 },
            signal,
          },
        );
        records.push(
          ...(Array.isArray(response) ? response : response.results || []),
        );
        if (!response.next) return [endpoint, records];
      }
      throw new Error(
        "There are too many choices to load in Quick actions. Open this action from its module.",
      );
    }),
  );
  for (const [endpoint, records] of responses) {
    if (endpoint === "offerings")
      references.variants = records.flatMap((offering) =>
        (offering.variants || [])
          .filter((variant) => variant.is_active)
          .map((variant) => ({
            public_id: variant.public_id,
            label: `${offering.name} · ${variant.name}`,
          })),
      );
    else
      references[endpoint === "expense-categories" ? "categories" : endpoint] =
        records;
  }
  return references;
}
