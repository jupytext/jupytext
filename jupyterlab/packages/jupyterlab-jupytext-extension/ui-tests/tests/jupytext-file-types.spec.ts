import { expect, IJupyterLabPageFixture, test } from '@jupyterlab/galata';

const notebookName = 'file-types.ipynb';
const scriptName = 'file-types.py';
const textFileName = 'file-types.txt';

/**
 * Open the context menu of a tab of the main area and return the labels of
 * its items.
 */
async function getTabContextMenuLabels(
  page: IJupyterLabPageFixture,
  tabName: string,
): Promise<string[]> {
  await page.activity.getTabLocator(tabName).click({ button: 'right' });
  const menu = page.locator('.lm-Menu').last();
  await expect(menu).toBeVisible();
  const labels = await menu.locator('.lm-Menu-itemLabel').allInnerTexts();
  await page.keyboard.press('Escape');
  return labels;
}

test.describe('Jupytext File Type Tests', () => {
  test('Notebook commands are named after the notebook file type', async ({
    page,
  }) => {
    await page.notebook.createNew(notebookName, { kernel: 'python3' });

    const labels = await getTabContextMenuLabels(page, notebookName);

    expect(labels).toContain('Rename Notebook…');
    expect(labels.filter((label) => label.includes('default'))).toEqual([]);
  });

  test('Text file commands are not named after the default file type', async ({
    page,
    tmpPath,
  }) => {
    await page.contents.uploadContent(
      'Some text\n',
      'text',
      `${tmpPath}/${textFileName}`,
    );
    await page.filebrowser.refresh();
    await page.filebrowser.open(textFileName);

    const labels = await getTabContextMenuLabels(page, textFileName);

    expect(labels.filter((label) => label.includes('default'))).toEqual([]);
  });

  test('Scripts keep the icon of their language in the file browser', async ({
    page,
    tmpPath,
  }) => {
    await page.contents.uploadContent(
      '1 + 1\n',
      'text',
      `${tmpPath}/${scriptName}`,
    );
    await page.filebrowser.refresh();

    const item = page
      .getByRole('region', { name: 'File Browser Section' })
      .getByRole('listitem', { name: new RegExp(`^Name: ${scriptName}`) });

    await expect(
      item.locator('.jp-DirListing-itemIcon [data-icon]'),
    ).toHaveAttribute('data-icon', 'ui-components:python');
  });
});
