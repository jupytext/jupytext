import { expect } from '@playwright/test';
import { test } from '@jupyterlab/galata/lib/fixtures';

// Main Jupytext menu
const jupytextMenu = ['File>New Text Notebook', 'File>Jupytext'];

test.describe('Jupytext Menu Tests', () => {
  test.use({ autoGoto: false });

  jupytextMenu.forEach((menuPath) => {
    test(`Open menu item ${menuPath}`, async ({ page }) => {
      await page.goto();
      await page.menu.open(menuPath);
      expect(await page.menu.isOpen(menuPath)).toBeTruthy();

      const imageName = `opened-jupytext-menu-${menuPath.replace(
        />/g,
        '-',
      )}.png`;
      // const menu = await page.menu.getOpenMenu();
      expect(await page!.screenshot()).toMatchSnapshot(imageName.toLowerCase());
    });
  });
});
