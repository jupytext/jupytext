import { expect, test } from '@jupyterlab/galata';

test('Jupytext Notebook follows the built-in notebook content provider', async ({
  page,
}) => {
  const providers = await page.evaluate(() => {
    const registry = window.jupyterapp.docRegistry;
    const notebook = registry.getWidgetFactory('Notebook');
    const jupytext = registry.getWidgetFactory('Jupytext Notebook');
    if (!notebook || !jupytext) {
      throw new Error('Expected both notebook factories to be registered');
    }

    const original = notebook.contentProviderId ?? null;
    const before = jupytext.contentProviderId ?? null;
    // Collaboration can assign its provider after Jupytext has registered.
    (notebook as { contentProviderId?: string }).contentProviderId ??=
      'test-provider';
    return { original, before, after: jupytext.contentProviderId ?? null };
  });

  expect(providers.before).toBe(providers.original);
  expect(providers.after).toBe(providers.original ?? 'test-provider');
});
