export function dateKeyInZone(value, timeZone = "Asia/Manila") {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(value);
  } catch (error) {
    if (error instanceof RangeError && timeZone !== "Asia/Manila")
      return dateKeyInZone(value, "Asia/Manila");
    throw error;
  }
}

export function shiftDate(key, days) {
  const value = new Date(`${key}T12:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

export function validReportRange(from, to) {
  const validDate = (key) =>
    typeof key === "string" &&
    /^\d{4}-\d{2}-\d{2}$/.test(key) &&
    !Number.isNaN(Date.parse(`${key}T12:00:00Z`)) &&
    new Date(`${key}T12:00:00Z`).toISOString().slice(0, 10) === key;
  if (!validDate(from) || !validDate(to)) return false;
  const days = (Date.parse(to) - Date.parse(from)) / 86400000;
  return days >= 0 && days <= 366;
}

export function groupSalesActivity(activity, interval = "daily") {
  const groups = new Map();
  for (const day of activity || []) {
    const date = new Date(`${day.date}T12:00:00Z`);
    const key =
      interval === "monthly"
        ? `${day.date.slice(0, 7)}-01`
        : interval === "weekly"
          ? shiftDate(day.date, -((date.getUTCDay() + 6) % 7))
          : day.date;
    const row = groups.get(key) || {
      key,
      from: day.date,
      to: day.date,
      sales: 0,
      orders: 0,
    };
    row.sales += Number(day.sales || 0);
    row.orders += Number(day.orders || 0);
    row.to = day.date;
    groups.set(key, row);
  }
  return [...groups.values()];
}

export function analyticsCsv(rows) {
  return (
    "\uFEFF" +
    rows
      .map((row) =>
        row
          .map((value) => {
            const text = String(value ?? "");
            // User-controlled names must remain text when opened in a spreadsheet.
            const safe =
              /^[\s]*[=+@-]/.test(text) && typeof value !== "number"
                ? `'${text}`
                : text;
            return `"${safe.replaceAll('"', '""')}"`;
          })
          .join(","),
      )
      .join("\r\n")
  );
}

export function analyticsMetricDefinitions(
  report,
  tab = "overview",
  restaurant = false,
) {
  if (!report) return [];
  const analytics = report.analytics || {};
  const daily = report.daily_activity || [];
  const number = (value) => Number(value) || 0;
  const count = (value) => new Intl.NumberFormat("en-PH").format(number(value));
  const statusCount = (key) =>
    number(analytics.status_breakdown?.find((row) => row.key === key)?.count);
  const metric = (
    key,
    label,
    value,
    format,
    icon,
    detail,
    explanation,
    values = [],
  ) => ({ key, label, value, format, icon, detail, explanation, values });
  const sales = metric(
    "gross-sales",
    "Gross sales",
    number(report.sales),
    "money",
    "Banknote",
    "Recorded order totals",
    "Sum of order grand totals in this period, excluding cancelled orders. This is not a cash-receipts or net-refund report.",
    daily.map((day) => day.sales),
  );
  const orderTotal = number(report.orders?.total);
  const average = metric(
    "average-order",
    "Average order value",
    orderTotal ? number(report.sales) / orderTotal : 0,
    "money",
    "Tag",
    "Gross sales ÷ orders",
    "Gross sales divided by the non-cancelled order count. Daily averages appear in the sparkline.",
    daily.map((day) => (day.orders ? number(day.sales) / day.orders : 0)),
  );
  const expenses = metric(
    "expenses",
    "Expenses",
    number(report.expenses),
    "money",
    "ReceiptText",
    "Incurred in this period",
    "Recorded business expenses by incurred date within the reporting period.",
    daily.map((day) => day.expenses),
  );

  if (tab === "sales")
    return [
      sales,
      metric(
        "orders-placed",
        "Orders placed",
        number(analytics.orders_placed),
        "count",
        "ShoppingCart",
        "All order statuses",
        "All orders placed in this period, including cancelled and refunded orders. This count differs from the non-cancelled sales-report order count.",
      ),
      metric(
        "paid-orders",
        "Paid orders",
        number(report.orders?.paid),
        "count",
        "WalletCards",
        "Fully paid, not cancelled",
        "Non-cancelled orders placed in this period whose payment status is fully paid. This is an order count, not a payment-receipt total.",
      ),
      average,
      metric(
        "fulfilled-orders",
        "Fulfilled orders",
        statusCount("fulfilled"),
        "count",
        "Package",
        "Placed in this period",
        "Orders placed in the selected period that currently have fulfilled status. The period is based on placement date, not fulfillment date.",
      ),
      metric(
        "cancelled-orders",
        "Cancelled orders",
        statusCount("cancelled"),
        "count",
        "ReceiptText",
        "Excluded from gross sales",
        "Orders placed in this period that currently have cancelled status. Their value is excluded from gross sales and product metrics.",
      ),
    ];

  if (tab === "products") {
    const product = analytics.product_summary || {};
    const itemSales = number(analytics.item_sales);
    const units = number(product.units_sold);
    const leader = analytics.top_products?.[0];
    return [
      metric(
        "item-sales",
        "Item sales",
        itemSales,
        "money",
        "Banknote",
        "Recorded product lines",
        "Sum of all non-cancelled order item totals in this period. Shipping and order-level adjustments can make this differ from gross sales.",
      ),
      metric(
        "units-sold",
        "Units sold",
        units,
        "count",
        "Package",
        "Across all sold items",
        "Total quantity across every non-cancelled order item in this period, including products and services outside the top-six ranking.",
      ),
      metric(
        "products-sold",
        "Products sold",
        number(product.products_sold),
        "count",
        "ShoppingCart",
        "Distinct recorded products",
        "Distinct product and recorded-name combinations sold across the full period. Variants with the same product and recorded name are counted together; renamed snapshots remain distinct.",
      ),
      metric(
        "categories-sold",
        "Categories sold",
        number(product.categories_sold),
        "count",
        "Tag",
        "Includes uncategorized items",
        "Current catalog category groups represented by non-cancelled item sales, including Uncategorized when present. This includes categories grouped into Other in the chart.",
      ),
      metric(
        "average-unit",
        "Average unit value",
        units ? itemSales / units : 0,
        "money",
        "BarChart3",
        "Item sales ÷ units sold",
        "Recorded item sales divided by total units sold in the selected period. This is a per-unit value, not average order value.",
      ),
      metric(
        "top-product-share",
        "Top product share",
        itemSales > 0 ? number(leader?.sales) / itemSales : 0,
        "percent",
        "BarChart3",
        leader?.name || "No item sales in this period",
        leader
          ? `${leader.name} accounts for this share of all recorded item sales in the period. The denominator includes every product, not only the top-six ranking.`
          : "The leading product's share appears after item sales are recorded in this period.",
      ),
    ];
  }

  if (tab === "operations")
    return [
      expenses,
      metric(
        "bookings",
        restaurant ? "Reservations" : "Bookings",
        number(report.bookings?.total),
        "count",
        "CalendarDays",
        `${count(report.bookings?.confirmed)} confirmed in period`,
        "Bookings with a start date in this reporting period. The detail shows how many of those bookings currently have confirmed status.",
      ),
      metric(
        "inventory-cost",
        "Inventory at cost",
        number(report.inventory?.value_at_cost),
        "money",
        "Package",
        "Current inventory position",
        "Current on-hand inventory valued at recorded unit cost. This is a current balance and does not follow the selected reporting period.",
      ),
      metric(
        "low-stock",
        "Low-stock items",
        number(report.inventory?.low_stock_items),
        "count",
        "Package",
        "Current stock alerts",
        "Current inventory balances whose available stock is at or below their configured low-stock threshold, including out-of-stock balances.",
      ),
      metric(
        "open-invoices",
        "Open invoices",
        number(report.invoice_aging?.open_count),
        "count",
        "ReceiptText",
        "Current unpaid balances",
        "Current invoices whose status is neither paid nor void. This current position is independent of the selected reporting period.",
      ),
      metric(
        "overdue-invoices",
        "Overdue invoices",
        number(report.invoice_aging?.overdue_count),
        "count",
        "CalendarDays",
        "Current past-due invoices",
        "Current non-paid, non-void invoices with a due date before today in the business timezone. This is not a period invoice count.",
      ),
    ];

  return [
    sales,
    metric(
      "total-orders",
      "Total orders",
      orderTotal,
      "count",
      "ShoppingCart",
      `${count(report.orders?.paid)} fully paid`,
      "Orders placed in this reporting period. Cancelled orders are excluded, following the sales report definition.",
      daily.map((day) => day.orders),
    ),
    average,
    metric(
      "gross-profit",
      "Gross profit",
      number(report.gross_profit),
      "money",
      "BarChart3",
      "Less recorded item costs",
      "Gross sales less product costs stored on order items. Items without a recorded cost contribute zero cost.",
    ),
    expenses,
    metric(
      "operating-result",
      "Net operating result",
      number(report.net_operating_result),
      "money",
      "WalletCards",
      "Gross profit − expenses",
      "Gross profit less recorded expenses. This operational result is not an accounting statement or a forecast.",
    ),
  ];
}
