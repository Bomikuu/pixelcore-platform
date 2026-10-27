import assert from "node:assert/strict";
import test from "node:test";
import {
  analyticsCsv,
  analyticsMetricDefinitions,
  dateKeyInZone,
  groupSalesActivity,
  shiftDate,
  validReportRange,
} from "./analytics.js";

test("report date validation rejects normalized invalid dates and excessive ranges", () => {
  assert.equal(validReportRange("2026-02-30", "2026-03-01"), false);
  assert.equal(validReportRange("2026-10-02", "2026-10-01"), false);
  assert.equal(validReportRange("2025-01-01", "2026-10-01"), false);
  assert.equal(validReportRange("2024-02-29", "2024-02-29"), true);
  assert.equal(validReportRange(undefined, undefined), false);
  assert.equal(validReportRange(["2026-10-01"], "2026-10-26"), false);
});

test("date helpers preserve date-only arithmetic across timezone boundaries", () => {
  assert.equal(
    dateKeyInZone(new Date("2026-10-01T01:00:00Z"), "America/Los_Angeles"),
    "2026-09-30",
  );
  assert.equal(
    dateKeyInZone(new Date("2026-10-01T23:00:00Z"), "Asia/Manila"),
    "2026-10-02",
  );
  assert.equal(shiftDate("2024-03-01", -1), "2024-02-29");
  assert.equal(
    dateKeyInZone(new Date("2026-10-01T23:00:00Z"), "Invalid/Zone"),
    "2026-10-02",
  );
});

test("weekly and monthly buckets conserve sales and order totals at partial boundaries", () => {
  const days = [
    { date: "2026-09-30", sales: "10.20", orders: 2 },
    { date: "2026-10-01", sales: "20.30", orders: 3 },
    { date: "2026-10-05", sales: "40.50", orders: 4 },
  ];
  const weekly = groupSalesActivity(days, "weekly");
  assert.equal(weekly.length, 2);
  assert.deepEqual(weekly[0], {
    key: "2026-09-28",
    from: "2026-09-30",
    to: "2026-10-01",
    sales: 30.5,
    orders: 5,
  });
  for (const interval of ["daily", "weekly", "monthly"]) {
    const rows = groupSalesActivity(days, interval);
    assert.equal(
      rows.reduce((sum, row) => sum + row.sales, 0),
      71,
    );
    assert.equal(
      rows.reduce((sum, row) => sum + row.orders, 0),
      9,
    );
  }
});

test("CSV preserves quotes, newlines, numeric negatives, and neutralizes formula names", () => {
  const csv = analyticsCsv([
    ["Name", "Value"],
    ["=SUM(A1)", -12.5],
    ['A "quoted", name\nnext', 2],
  ]);
  assert.ok(csv.startsWith("\uFEFF"));
  assert.ok(csv.includes('"\'=SUM(A1)","-12.5"'));
  assert.ok(csv.includes('"A ""quoted"", name\nnext","2"'));
});

test("each analytics tab selects relevant full-period metrics", () => {
  const report = {
    sales: "1200.00",
    gross_profit: "800.00",
    expenses: "100.00",
    net_operating_result: "700.00",
    orders: { total: 10, paid: 8 },
    bookings: { total: 4, confirmed: 3 },
    inventory: { value_at_cost: "4000.00", low_stock_items: 2 },
    invoice_aging: { open_count: 5, overdue_count: 1 },
    analytics: {
      orders_placed: 12,
      item_sales: "1000.00",
      product_summary: {
        units_sold: 50,
        products_sold: 20,
        categories_sold: 9,
      },
      top_products: [{ name: "Leading product", sales: "100.00", quantity: 5 }],
      status_breakdown: [
        { key: "fulfilled", count: 6 },
        { key: "cancelled", count: 2 },
      ],
    },
  };
  const sets = Object.fromEntries(
    ["overview", "sales", "products", "operations"].map((tab) => [
      tab,
      analyticsMetricDefinitions(report, tab),
    ]),
  );
  assert.equal(
    new Set(
      Object.values(sets).map((rows) => rows.map((row) => row.key).join(",")),
    ).size,
    4,
  );
  for (const rows of Object.values(sets)) assert.equal(rows.length, 6);
  const find = (tab, key) => sets[tab].find((row) => row.key === key).value;
  assert.equal(find("overview", "operating-result"), 700);
  assert.equal(find("sales", "orders-placed"), 12);
  assert.equal(find("sales", "paid-orders"), 8);
  assert.equal(find("sales", "cancelled-orders"), 2);
  assert.equal(find("products", "units-sold"), 50);
  assert.equal(find("products", "products-sold"), 20);
  assert.equal(find("products", "categories-sold"), 9);
  assert.equal(find("products", "average-unit"), 20);
  assert.equal(find("products", "top-product-share"), 0.1);
  assert.equal(find("operations", "inventory-cost"), 4000);
  assert.equal(find("operations", "bookings"), 4);
  assert.ok(
    sets.operations
      .find((row) => row.key === "open-invoices")
      .explanation.includes("independent of the selected reporting period"),
  );
});

test("empty tabs keep six finite metrics and restaurant booking vocabulary", () => {
  for (const tab of ["overview", "sales", "products", "operations"]) {
    assert.ok(
      analyticsMetricDefinitions({}, tab).every(
        (row) => Number.isFinite(row.value) && row.value === 0,
      ),
    );
  }
  assert.equal(
    analyticsMetricDefinitions({}, "operations", true).find(
      (row) => row.key === "bookings",
    ).label,
    "Reservations",
  );
});
