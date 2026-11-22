import { expect } from '@playwright/test';
import { test } from '@jupyterlab/galata/lib/fixtures';

test.describe('Jupytext Launcher Category', () => {
  test.use({ autoGoto: false, viewport: { height: 1020, width: 1280 } });
  test('should have Jupytext category in launcher', async ({ page }) => {
    await page.goto();
    await page.waitForSelector('.jp-LauncherCard-label');

    const imageName = 'launcher-category.png';
    expect(await page.screenshot()).toMatchSnapshot(imageName.toLowerCase());
  });
});

test.describe('Jupytext Context Menu', () => {
  test.use({ autoGoto: false, viewport: { height: 1020, width: 1280 } });
  test('should have New Text Notebook in Context Menu', async ({ page }) => {
    await page.goto();
    await page.waitForSelector('.jp-FileBrowser');

    // Right click within file browser
    await page.locator('.jp-FileBrowser').click({ button: 'right' });

    // Wait for a moment to observe the context menu
    await page.waitForTimeout(5000);

    const imageName = 'context-menu.png';
    expect(await page.screenshot()).toMatchSnapshot(imageName.toLowerCase());
  });
});
