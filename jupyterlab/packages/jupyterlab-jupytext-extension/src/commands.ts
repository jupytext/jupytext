import { showErrorMessage } from '@jupyterlab/apputils';

import { INotebookTracker } from '@jupyterlab/notebook';

import * as nbformat from '@jupyterlab/nbformat';

import { TranslationBundle } from '@jupyterlab/translation';

import {
  LANGUAGE_INDEPENDENT_NOTEBOOK_EXTENSIONS,
  JUPYTEXT_FORMATS,
  IJupytextSection,
} from './tokens';

/**
 * Get Jupytext format of current widget if it is a text notebook
 */
function getWidgetJupytextFormats(
  notebookTracker: INotebookTracker,
): Array<string> {
  const widget = notebookTracker.currentWidget;
  if (!widget) {
    return [];
  }

  const model = widget.context.model;

  const jupytext: IJupytextSection = (model as any).getMetadata('jupytext');
  if (!jupytext) {
    return [];
  }
  const formats: Array<string> = jupytext.formats
    ? jupytext.formats.split(',')
    : [];
  return formats.filter((format) => {
    return format !== '';
  });
}

/**
 * Get file extension of current notebook widget
 */
function getNotebookFileExtension(notebookTracker: INotebookTracker): string {
  const widget = notebookTracker.currentWidget;
  if (!widget) {
    return '';
  }

  let notebookFileExtension: string | undefined =
    widget.context.path.split('.').pop();
  if (!notebookFileExtension) {
    return '';
  }

  notebookFileExtension = LANGUAGE_INDEPENDENT_NOTEBOOK_EXTENSIONS.includes(
    notebookFileExtension,
  )
    ? notebookFileExtension
    : 'auto';
  return notebookFileExtension;
}

/**
 * Get a list of all selected formats
 */
function getSelectedFormats(notebookTracker: INotebookTracker): Array<string> {
  if (!notebookTracker.currentWidget) {
    return [];
  }

  let formats = getWidgetJupytextFormats(notebookTracker);

  const model = notebookTracker.currentWidget.context.model;

  const languageInfo = (model as any).getMetadata(
    'language_info',
  ) as nbformat.ILanguageInfoMetadata;
  if (languageInfo && languageInfo.file_extension) {
    const scriptExt = languageInfo.file_extension.substring(1);
    formats = formats.map((format) => {
      // By default use percent format
      if (format === scriptExt) {
        return 'auto:percent';
      }
      // Replace language specific extension with auto
      return format.replace(`${scriptExt}:`, 'auto:');
    });
  }

  const notebookFileExtension = getNotebookFileExtension(notebookTracker);
  if (!notebookFileExtension) {
    return formats;
  }
  // Remove variant after : in format
  const formatExtensions = formats.map((format) => {
    return format.split(':')[0];
  });
  // If current notebook file extension in formats, return
  if (formatExtensions.includes(notebookFileExtension)) {
    return formats;
  }

  // When notebook loads for the first time, ipynb extension would not be
  // in the formats. Here we add it and return formats
  if (
    LANGUAGE_INDEPENDENT_NOTEBOOK_EXTENSIONS.includes(notebookFileExtension)
  ) {
    formats.push(notebookFileExtension);
  } else {
    const model = notebookTracker.currentWidget.context.model;
    const jupytext: IJupytextSection = (model as any).getMetadata(
      'jupytext',
    ) as IJupytextSection;
    const formatName = jupytext
      ? jupytext?.text_representation?.formatName || 'percent'
      : 'percent';
    formats.push(`auto:${formatName}`);
  }
  return formats;
}

/**
 * Toggle pair command
 */
export function isPairCommandToggled(
  format: string,
  notebookTracker: INotebookTracker,
): boolean {
  if (!notebookTracker.currentWidget) {
    return false;
  }

  // Get selected formats on current widget
  const selectedFormats = getSelectedFormats(notebookTracker);

  if (format === 'custom') {
    for (const selectedFormat of selectedFormats) {
      if (!JUPYTEXT_FORMATS.includes(selectedFormat)) {
        return true;
      }
    }
    return false;
  }
  return selectedFormats.includes(format);
}

/**
 * Enable pair command
 */
export function isPairCommandEnabled(
  format: string,
  notebookTracker: INotebookTracker,
): boolean {
  if (!notebookTracker.currentWidget) {
    return false;
  }

  const notebookFileExtension: string | undefined =
    notebookTracker.currentWidget.context.path.split('.').pop();
  if (format === notebookFileExtension) {
    return false;
  }

  // Get selected formats on current widget
  const selectedFormats = getSelectedFormats(notebookTracker);

  if (format === 'none') {
    return selectedFormats.length > 1;
  }

  return true;
}

/**
 * Execute pair command
 */
export function executePairCommand(
  command: string,
  format: string,
  notebookTracker: INotebookTracker,
  trans: TranslationBundle,
): void {
  if (!notebookTracker.currentWidget) {
    return;
  }
  const model = notebookTracker.currentWidget.context.model;
  let jupytext = (model as any).getMetadata(
    'jupytext',
  ) as
    | IJupytextSection
    | undefined;

  // Get selected formats on current widget
  let selectedFormats = getSelectedFormats(notebookTracker);

  // Toggle the selected format
  console.debug('Jupytext: executing command=' + command);
  if (format === 'custom') {
    showErrorMessage(
      trans.__('Error'),
      trans.__(
        'Please edit the notebook metadata directly if you wish a custom configuration.',
      ),
    );
    return;
  }

  // Get current notebook widget extension
  const notebookFileExtension = getNotebookFileExtension(notebookTracker);

  // Toggle the selected format
  const index = selectedFormats.indexOf(format);
  if (format === 'none') {
    // Only keep one format - one that matches the current extension
    for (const selectedFormat of selectedFormats) {
      if (selectedFormat.split(':')[0] === notebookFileExtension) {
        selectedFormats = [selectedFormat];
        break;
      }
    }
  } else if (index !== -1) {
    selectedFormats.splice(index, 1);

    // The current file extension can't be unpaired
    let extFound = false;
    for (const selectedFormat of selectedFormats) {
      if (selectedFormat.split(':')[0] === notebookFileExtension) {
        extFound = true;
        break;
      }
    }

    if (!extFound) {
      return;
    }
  } else {
    // We can't have the same extension multiple times
    const newFormats = [];
    for (const selectedFormat of selectedFormats) {
      if (selectedFormat.split(':')[0] !== format.split(':')[0]) {
        newFormats.push(selectedFormat);
      }
    }

    selectedFormats = newFormats;
    selectedFormats.push(format);
  }

  if (selectedFormats.length === 1) {
    if (notebookFileExtension !== 'auto') {
      selectedFormats = [];
    } else if (jupytext?.text_representation) {
      jupytext.text_representation.formatName =
        selectedFormats[0].split(':')[1];
      selectedFormats = [];
    }
  }

  if (selectedFormats.length === 0) {
    // an older version was re-fetching the jupytext metadata here
    // but this is not necessary, as the metadata is already available
    if (!jupytext) {
      return;
    }

    if (jupytext.formats) {
      delete jupytext.formats;
    }
    if (Object.keys(jupytext).length === 0) {
      (model as any).deleteMetadata('jupytext');
    }
    (model as any).setMetadata('jupytext', jupytext);
    return;
  }

  // set the desired format
  if (jupytext) {
    jupytext.formats = selectedFormats.join();
  } else {
    jupytext = { formats: selectedFormats.join() };
  }
  (model as any).setMetadata('jupytext', jupytext);
}

/**
 * Toggle metadata command
 */
export function isMetadataCommandToggled(
  notebookTracker: INotebookTracker,
): boolean {
  if (!notebookTracker.currentWidget) {
    return false;
  }

  const model = notebookTracker.currentWidget.context.model;
  const jupytextMetadata = (model as any).getMetadata('jupytext');
  if (!jupytextMetadata) {
    return false;
  }

  const jupytext: IJupytextSection =
    jupytextMetadata as unknown as IJupytextSection;

  if (jupytext.notebook_metadata_filter === '-all') {
    return false;
  }

  return true;
}

/**
 * Enable metadata command
 */
export function isMetadataCommandEnabled(
  notebookTracker: INotebookTracker,
): boolean {
  if (!notebookTracker.currentWidget) {
    return false;
  }

  const model = notebookTracker.currentWidget.context.model;
  const jupytextMetadata = (model as any).getMetadata('jupytext');
  if (!jupytextMetadata) {
    return false;
  }

  const jupytext: IJupytextSection =
    jupytextMetadata as unknown as IJupytextSection;

  if (jupytext.notebook_metadata_filter === undefined) {
    return true;
  }

  if (jupytext.notebook_metadata_filter === '-all') {
    return true;
  }

  return false;
}

/**
 * Execute metadata command
 */
export function executeMetadataCommand(
  notebookTracker: INotebookTracker,
): void {
  console.debug('Jupytext: toggling YAML header');
  if (!notebookTracker.currentWidget) {
    return;
  }

  const model = notebookTracker.currentWidget.context.model;
  const jupytextMetadata = (model as any).getMetadata('jupytext');
  if (!jupytextMetadata) {
    return;
  }

  const jupytext = ((jupytextMetadata as unknown) ?? {}) as IJupytextSection;

  if (jupytext.notebook_metadata_filter) {
    delete jupytext.notebook_metadata_filter;
    if (jupytext.notebook_metadata_filter === '-all') {
      delete jupytext.notebook_metadata_filter;
    }
  } else {
    jupytext.notebook_metadata_filter = '-all';
    if (jupytext.notebook_metadata_filter === undefined) {
      jupytext.notebook_metadata_filter = '-all';
    }
  }
  (model as any).setMetadata('jupytext', jupytext);
}
