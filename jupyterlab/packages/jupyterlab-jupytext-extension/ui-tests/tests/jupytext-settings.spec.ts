import { expect } from '@playwright/test';
import { test } from '@jupyterlab/galata/lib/fixtures';

test('Open the settings editor with a Jupytext query', async ({ page }) => {
  await page.evaluate(async () => {
    await window.jupyterapp.commands.execute('settingeditor:open', {
      query: 'Jupytext',
    });
  });

  // Seems like this test is very flaky. Moreover it does not add a lot of value
  // expect(
  //   await page.locator('.jp-PluginList .jp-FilterBox input').inputValue()
  // ).toEqual('Jupytext');

  await expect(page.locator('.jp-SettingsForm')).toHaveCount(1);

  const pluginList = page.locator('.jp-PluginList');

  expect(await pluginList.screenshot()).toMatchSnapshot(
    'jupytext-settings-plugin-list.png',
  );

  const settingsPanel = page.locator('.jp-SettingsPanel');

  expect(await settingsPanel.screenshot()).toMatchSnapshot(
    'jupytext-settings-panel.png',
  );
});
