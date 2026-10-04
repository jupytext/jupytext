import { DocumentRegistry } from '@jupyterlab/docregistry';

import { TranslationBundle } from '@jupyterlab/translation';

import { markdownIcon, LabIcon, fileIcon } from '@jupyterlab/ui-components';

import { IDisposable } from '@lumino/disposable';

import { IFileTypeData } from './tokens';

/**
 * Return the source of a regular expression matching `text`, whatever the case
 * of its letters. JupyterLab compares extensions in a case-insensitive way, but
 * matches `pattern` as it is written.
 */
function caseInsensitiveSource(text: string): string {
  return text
    .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    .replace(
      /[a-zA-Z]/g,
      (letter) => `[${letter.toLowerCase()}${letter.toUpperCase()}]`,
    );
}

export function registerFileTypes(
  availableKernelLanguages: Map<string, IFileTypeData[]>,
  docRegistry: DocumentRegistry,
  trans: TranslationBundle,
) {
  const mystExtensions = ['myst', 'mystnb', 'mnb'];
  const rmdExtensions = ['Rmd'];
  const quartoExtensions = ['qmd'];

  // Add kernel file types to registry
  availableKernelLanguages.forEach(
    (kernelFileTypes: IFileTypeData[], kernelLanguage: string) => {
      kernelFileTypes.map((kernelFileType) => {
        docRegistry.addFileType({
          name: kernelLanguage,
          contentType: 'notebook',
          displayName: trans.__(
            kernelFileType.paletteLabel.split('New')[1].trim(),
          ),
          extensions: [`.${kernelFileType.fileExt}`],
          icon: kernelFileType.iconName
            ? LabIcon.resolve({ icon: kernelFileType.iconName })
            : kernelFileType.kernelIcon,
        });
      });
    },
  );

  const markdownNotebookIcon = markdownIcon.bindprops({
    boxSizing: 'border-box',
    border: '2px solid var(--jp-notebook-icon-color)',
    borderRadius: '2px',
  });

  // Add markdown file types to registry - these will be open with Notebook by default
  docRegistry.addFileType(
    {
      name: 'myst',
      contentType: 'notebook',
      displayName: trans.__('MyST Markdown Notebook'),
      extensions: mystExtensions.map((ext) => '.' + ext),
      icon: markdownNotebookIcon,
    },
    ['Notebook'],
  );

  docRegistry.addFileType(
    {
      name: 'r-markdown',
      contentType: 'notebook',
      displayName: trans.__('R Markdown Notebook'),
      // Extension file are transformed to lower case...
      extensions: rmdExtensions.map((ext) => '.' + ext),
      icon: markdownNotebookIcon,
    },
    ['Notebook'],
  );

  docRegistry.addFileType(
    {
      name: 'quarto',
      contentType: 'notebook',
      displayName: trans.__('Quarto Notebook'),
      extensions: quartoExtensions.map((ext) => '.' + ext),
      icon: markdownNotebookIcon,
    },
    ['Notebook'],
  );

  // Jupytext's contents manager gives the `notebook` type to every file it can
  // open, and JupyterLab resolves the icon of such a file from the file types
  // which declare the `notebook` content type, falling back to the notebook
  // file type when none of them matches (#398). Copy the file types which can
  // describe a text notebook, and cover the extensions which none of them
  // describes with a catch-all. The copies match on their extensions rather
  // than on a `pattern`, because a `pattern` takes precedence over the file
  // type it copies, and would also take over the name that JupyterLab shows in
  // menu entries such as "Rename Notebook…" (#1629).
  const knownExtensions = new Set<string>();
  const copiedFileTypes = new Set<string>();
  let catchAllFileType: IDisposable | null = null;

  const addNotebookFileTypes = () => {
    let isCatchAllStale = false;
    for (const fileType of [...docRegistry.fileTypes()]) {
      if (!fileType.extensions.length) {
        continue;
      }
      if (fileType.extensions.some((ext) => !knownExtensions.has(ext))) {
        fileType.extensions.forEach((ext) => knownExtensions.add(ext));
        isCatchAllStale = true;
      }
      // Notebooks and directories already resolve correctly, and files stored
      // as base64 (images, audio, video) are never text notebooks.
      if (
        fileType.contentType !== 'file' ||
        fileType.fileFormat === 'base64' ||
        copiedFileTypes.has(fileType.name)
      ) {
        continue;
      }
      copiedFileTypes.add(fileType.name);
      docRegistry.addFileType({
        name: `${fileType.name}-jupytext-notebook`,
        contentType: 'notebook',
        displayName: fileType.displayName,
        extensions: fileType.extensions,
        fileFormat: fileType.fileFormat,
        icon: fileType.icon,
        iconClass: fileType.iconClass,
        iconLabel: fileType.iconLabel,
      });
      isCatchAllStale = true;
    }
    if (!isCatchAllStale) {
      return;
    }
    const knownEnding = [...knownExtensions]
      .map(caseInsensitiveSource)
      .join('|');
    catchAllFileType?.dispose();
    catchAllFileType = docRegistry.addFileType({
      name: 'jupytext-notebook-file',
      contentType: 'notebook',
      displayName: trans.__('File'),
      pattern: `^(?!.*(${knownEnding})$).*$`,
      icon: fileIcon,
    });
  };

  addNotebookFileTypes();

  // Extensions activated after Jupytext register their file types later
  docRegistry.changed.connect((_, change) => {
    if (change.type === 'fileType' && change.change === 'added') {
      addNotebookFileTypes();
    }
  });
}
