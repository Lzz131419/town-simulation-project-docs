import { test as base, expect } from "@playwright/test";

// Opt-in isolation for the dedicated tests/browser_server.py application only.
// Existing developer servers never receive a reset request by default.
export const test = base.extend<{ resetWorld: void }>({
  resetWorld: [
    async ({ request }, use) => {
      if (process.env.TOWN_E2E_RESET_WORLD === "1") {
        const response = await request.post("/__test/reset-world");
        expect(response.ok()).toBeTruthy();
        expect(await response.json()).toEqual({ reset: true });
      }
      await use();
    },
    { auto: true },
  ],
});
export { expect };
export type { Page } from "@playwright/test";
