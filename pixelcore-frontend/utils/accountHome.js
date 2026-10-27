export function accountHome(user) {
  if (user?.has_delivery_access && !user?.businesses?.length)
    return "/rider/deliveries";
  if (user?.needs_onboarding) return "/onboarding";

  const memberships = Array.isArray(user?.businesses) ? user.businesses : [];
  const isEmployeeOnly =
    memberships.length > 0 &&
    memberships.every((membership) => membership.role === "staff");

  return isEmployeeOnly ? "/employee" : "/workspace";
}
