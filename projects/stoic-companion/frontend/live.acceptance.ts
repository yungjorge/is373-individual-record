import { test, expect } from "@playwright/test";
import fs from "node:fs";

const scenario =
  "I worked extremely hard for a promotion, but another employee got it. I feel jealous and like my work was wasted. What would the Stoics recommend?";
const followup =
  "How can I stay fair to my colleague while preparing for my next opportunity?";
function resultFromSSE(body: string) {
  const frame = body.split("\n\n").find((x) => x.startsWith("event: result"));
  if (!frame) throw new Error("No validated live result was returned");
  const data = frame.split("\n").find((x) => x.startsWith("data: "));
  return JSON.parse(data!.slice(6));
}
test("real container RAG conversation, source inspection and follow-up", async ({
  page,
  request,
}) => {
  fs.mkdirSync("../docs/evidence", { recursive: true });
  const health = await (await request.get("/api/v1/health")).json();
  expect(health.embedding_provider).toBe("openai");
  expect(health.generation_provider).toBe("openai");
  await page.goto("/");
  await page.getByLabel("Your reflection").fill(scenario);
  await expect(
    page.getByRole("button", { name: "Send reflection" }),
  ).toBeEnabled();
  const responsePromise = page.waitForResponse(
    (r) => r.url().includes("/messages") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Send reflection" }).click();
  const first = resultFromSSE(await (await responsePromise).text());
  expect(first.mode).toBe("openai");
  expect(first.debug.usage.input_tokens).toBeGreaterThan(0);
  expect(first.citations.length).toBeGreaterThan(0);
  for (const c of first.citations) {
    const stored = await (
      await request.get("/api/v1/passages/" + encodeURIComponent(c.passage_id))
    ).json();
    expect(stored.quote_text.replace(/\s+/g, " ")).toContain(
      c.quote_text.replace(/\s+/g, " "),
    );
    expect(c.author).toBe(stored.author);
    expect(c.translator).toBe(stored.translator);
    expect(c.reference).toBe(stored.reference);
    expect(c.source_url).toBe(stored.source_url);
  }
  await expect(page.locator(".citation-main").first()).toBeVisible();
  await page.locator(".citation-main").first().click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByText("Read the surrounding passage", { exact: true }).click();
  await expect(page.locator(".full-passage")).toBeVisible();
  await page.screenshot({
    path: "../docs/evidence/live-source-inspection.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close passage" }).click();
  await page.getByLabel("Your reflection").fill(followup);
  const secondPromise = page.waitForResponse(
    (r) => r.url().includes("/messages") && r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Send reflection" }).click();
  const second = resultFromSSE(await (await secondPromise).text());
  expect(second.mode).toBe("openai");
  expect(second.debug.rewritten_query).toContain(scenario);
  expect(second.debug.rewritten_query).toContain(followup);
  await expect(page.locator(".assistant-message .practice")).toHaveCount(2);
  await page.screenshot({
    path: "../docs/evidence/live-conversation.png",
    fullPage: true,
  });
  fs.writeFileSync(
    "../docs/evidence/live-conversation.json",
    JSON.stringify(
      { health, scenario, followup, first, second, verified: true },
      null,
      2,
    ),
  );
});
