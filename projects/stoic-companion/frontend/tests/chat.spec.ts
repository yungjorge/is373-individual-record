import { test, expect } from "@playwright/test";
import fs from "node:fs";

test("reflection, citations, bookmarks, multi-turn persistence and deletion", async ({
  page,
  isMobile,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "A little distance. A clearer perspective.",
    }),
  ).toBeVisible();
  fs.mkdirSync("../docs/screenshots", { recursive: true });
  await page.screenshot({
    path: `../docs/screenshots/${isMobile ? "mobile" : "desktop"}.png`,
    fullPage: true,
  });
  await page
    .getByLabel("Your reflection")
    .fill("I feel anxious about things outside my control.");
  await expect(
    page.getByRole("button", { name: "Send reflection" }),
  ).toBeEnabled();
  await page.getByRole("button", { name: "Send reflection" }).click();
  await expect(page.locator(".citation-main").first()).toBeVisible();
  await page.locator(".citation-main").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(
    page
      .getByRole("dialog")
      .getByText("Exact source excerpt; whitespace normalization only."),
  ).toBeVisible();
  const sourceLink = page.getByRole("link", {
    name: "Read the original source",
  });
  await expect(sourceLink).toHaveAttribute(
    "href",
    /https:\/\/(www.gutenberg.org|en.wikisource.org)/,
  );
  await page.getByRole("button", { name: "Save passage", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Saved", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close passage" }).click();
  await page
    .getByLabel("Your reflection")
    .fill("How can I put this into practice tomorrow?");
  await page.getByRole("button", { name: "Send reflection" }).click();
  await expect(page.locator(".assistant-message .practice")).toHaveCount(2);
  await page.reload();
  if (isMobile)
    await page.getByRole("button", { name: "Open sidebar" }).click();
  await page
    .getByRole("button", {
      name: "I feel anxious about things outside my control.",
      exact: true,
    })
    .click();
  if (isMobile)
    await page.getByRole("button", { name: "Close sidebar" }).click();
  await expect(page.locator(".user-message")).toHaveCount(2);
  if (isMobile)
    await page.getByRole("button", { name: "Open sidebar" }).click();
  await page.getByRole("button", { name: "Saved passages 1" }).click();
  if (isMobile)
    await page.getByRole("button", { name: "Close sidebar" }).click();
  await expect(page.locator(".library-grid .citation")).toHaveCount(1);
  if (isMobile)
    await page.getByRole("button", { name: "Open sidebar" }).click();
  await page
    .getByRole("button", {
      name: "Delete I feel anxious about things outside my control.",
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Delete I feel anxious about things outside my control.",
    }),
  ).toHaveCount(0);
});

test("library search and author filter", async ({ page, isMobile }) => {
  await page.goto("/");
  if (isMobile)
    await page.getByRole("button", { name: "Open sidebar" }).click();
  await page.getByRole("button", { name: "Source library 6" }).click();
  if (isMobile)
    await page.getByRole("button", { name: "Close sidebar" }).click();
  await page.getByLabel("Search source library").fill("fear");
  await page.getByLabel("Library author").selectOption("Seneca");
  await expect(page.locator(".library-grid .citation").first()).toBeVisible();
  await expect(
    page.locator(".library-grid .citation-author").first(),
  ).toHaveText("Seneca");
});
