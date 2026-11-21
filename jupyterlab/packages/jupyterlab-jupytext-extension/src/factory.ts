import {
  IToolbarWidgetRegistry,
  createToolbarFactory,
} from '@jupyterlab/apputils';

import {
  INotebookTracker,
  NotebookPanel,
  NotebookWidgetFactory,
} from '@jupyterlab/notebook';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { IRenderMimeRegistry } from '@jupyterlab/rendermime';

import { IEditorServices } from '@jupyterlab/codeeditor';

import { ITranslator, TranslationBundle } from '@jupyterlab/translation';

import { IDisposable } from '@lumino/disposable';

import { IRisePreviewFactory } from 'jupyterlab-rise';

import { FACTORY, FILE_TYPES } from './tokens';

class JupytextNotebookWidgetFactory extends NotebookWidgetFactory {
  constructor(
    options: NotebookWidgetFactory.IOptions<NotebookPanel>,
    private readonly notebookFactory: NotebookWidgetFactory.IFactory,
  ) {
    super(options);
  }

  override get contentProviderId(): string | undefined {
    // Other extensions can assign the Notebook provider after registration.
    return super.contentProviderId ?? this.notebookFactory.contentProviderId;
  }

  override set contentProviderId(value: string | undefined) {
    super.contentProviderId = value;
  }
}

export function createFactory(
  kernelFileTypeNames: string[],
  toolbarRegistry: IToolbarWidgetRegistry,
  settingRegistry: ISettingRegistry,
  docRegistry: DocumentRegistry,
  notebookTracker: INotebookTracker,
  notebookFactory: NotebookWidgetFactory.IFactory,
  contentFactory: NotebookPanel.IContentFactory,
  editorServices: IEditorServices,
  rendermime: IRenderMimeRegistry,
  translator: ITranslator,
  trans: TranslationBundle,
  riseFactory: IRisePreviewFactory | null,
) {
  const allFileTypes = FILE_TYPES.concat(kernelFileTypeNames);
  // primarily this block is copied/pasted from jlab4 code and specifically
  // jupyterlab/packages/notebook-extension/src/index.ts
  // inside the function `activateWidgetFactory` at line 1150 as of this writing
  //
  const toolbarFactory = createToolbarFactory(
    toolbarRegistry,
    settingRegistry,
    'Notebook',
    '@jupyterlab/notebook-extension:panel',
    translator,
  );
  // Duplicate notebook factory to apply it on Jupytext notebooks
  // Mirror: https://github.com/jupyterlab/jupyterlab/blob/8a8c3752564f37493d4eb6b4c59008027fa83880/packages/notebook-extension/src/index.ts#L860
  const factory = new JupytextNotebookWidgetFactory(
    {
      name: FACTORY,
      label: trans.__(FACTORY),
      fileTypes: allFileTypes,
      modelName: notebookFactory.modelName ?? 'notebook',
      preferKernel: notebookFactory.preferKernel ?? true,
      canStartKernel: notebookFactory.canStartKernel ?? true,
      rendermime,
      contentFactory,
      editorConfig: notebookFactory.editorConfig,
      notebookConfig: notebookFactory.notebookConfig,
      mimeTypeService: editorServices.mimeTypeService,
      toolbarFactory: toolbarFactory,
      translator,
    },
    notebookFactory,
  );
  docRegistry.addWidgetFactory(factory);

  // The list of extensions in the Jupytext Notebook factory.
  const factoryExtensions: IDisposable[] = [];
  const updateWidgetExtensions = () => {
    // Dispose of all existing extensions.
    factoryExtensions.forEach((extension) => extension.dispose());
    // Add all the widgets extensions in the Notebook factory.
    for (const extension of docRegistry.widgetExtensions('Notebook')) {
      docRegistry.addWidgetExtension(FACTORY, extension);
    }
  };

  // Listen for changes in Notebook factory extensions.
  docRegistry.changed.connect((_, change) => {
    if (change.type === 'widgetExtension' && change.name === 'Notebook') {
      updateWidgetExtensions();
    }
  });
  updateWidgetExtensions();

  // Register widget created with the new factory in the notebook tracker
  // This is required to activate notebook commands (and therefore shortcuts)
  let id = 0; // The ID counter for notebook panels.
  const ft = docRegistry.getFileType('notebook');

  factory.widgetCreated.connect((sender, widget) => {
    // If the notebook panel does not have an ID, assign it one.
    widget.id = widget.id || `notebook-jupytext-${++id}`;

    // Set up the title icon
    widget.title.icon = ft?.icon;
    widget.title.iconClass = ft?.iconClass ?? '';
    widget.title.iconLabel = ft?.iconLabel ?? '';

    // Notify the widget tracker if restore data needs to update.
    widget.context.pathChanged.connect(() => {
      // @ts-expect-error Trick using private API
      void notebookTracker.save(widget);
    });
    // Add the notebook panel to the tracker.
    //   @ts-expect-error Trick using private API
    void notebookTracker.add(widget);
  });

  // Add support for RISE slides
  if (riseFactory) {
    for (const fileType of allFileTypes) {
      riseFactory.addFileType(fileType);
    }
  }
}
