import { IEditorLanguageRegistry } from '@jupyterlab/codemirror';

import {
  ServiceManager,
  ServerConnection,
  KernelSpec,
} from '@jupyterlab/services';

import { LabIcon } from '@jupyterlab/ui-components';

import { URLExt } from '@jupyterlab/coreutils';

import { DocumentRegistry, IDocumentWidget } from '@jupyterlab/docregistry';

import { CommandRegistry } from '@lumino/commands';

import { Buffer } from 'buffer';

import {
  NS,
  SERVER_SETTINGS,
  AUTO_LANGUAGE_FILETYPE_DATA,
  JUPYTEXT_CREATE_TEXT_NOTEBOOK_FILETYPE_DATA,
  FACTORY,
  CommandIDs,
  IFileTypeData,
} from './tokens';

/**
 * Get kernel icon SVG string
 */
async function getKernelIconBase64String(
  kernelIconUrl: string,
): Promise<string> {
  // Seems like URL prefix is already included in kernelIconUrl. We need to strip
  // it off as baseUrl will already has url prefix.
  kernelIconUrl = `/kernelspecs${kernelIconUrl.split('kernelspecs')[1]}`;
  const url = URLExt.join(SERVER_SETTINGS.baseUrl, kernelIconUrl);
  const response = await ServerConnection.makeRequest(url, {}, SERVER_SETTINGS);
  const blob = await response.arrayBuffer();
  const contentType = response.headers.get('content-type');
  return `data:${contentType};base64,${Buffer.from(blob).toString('base64')}`;
}

/**
 * Make a SVG string from base64 image
 */
function base64ToSvgStr(width: number, imageBase64: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink" preserveAspectRatio="none" viewBox="0 0 ${width} ${width}">
  <g id="layer1">
     <image xlink:href="${imageBase64}"/>
  </g>
</svg>`.replace(/\n/g, ' ');
}

/**
 * Get kernel Icon
 */
async function getKernelIcon(
  specModel: KernelSpec.ISpecModel,
  fileType: DocumentRegistry.IFileType | undefined,
): Promise<LabIcon> {
  // First check for logo-svg
  if (specModel.resources['logo-svg']) {
    const svgStr = await getKernelIconBase64String(
      specModel.resources['logo-svg'],
    );
    return new LabIcon({
      name: `${NS}:icon:${specModel.name}`,
      svgstr: svgStr,
    });
  }
  // Else check if 64x64 kernel icon is available
  if (specModel.resources['logo-64x64']) {
    const iconBase64String = await getKernelIconBase64String(
      specModel.resources['logo-64x64'],
    );
    return new LabIcon({
      name: `${NS}:icon:${specModel.name}`,
      svgstr: base64ToSvgStr(64, iconBase64String),
    });
  }
  // Finally check for 32x32 kernel icon
  if (specModel.resources['logo-32x32']) {
    const iconBase64String = await getKernelIconBase64String(
      specModel.resources['logo-32x32'],
    );
    return new LabIcon({
      name: `${NS}:icon:${specModel.name}`,
      svgstr: base64ToSvgStr(32, iconBase64String),
    });
  }
  if (fileType && fileType.icon) {
    return fileType.icon;
  }
  // If not found, make a generic kernel icon
  return LabIcon.resolve({
    icon: 'ui-components:kernel',
  });
}

/**
 * Get all available kernel languages so that we replace auto format
 * with these language file extensions
 */
export async function getAvailableKernelLanguages(
  languages: IEditorLanguageRegistry,
  docRegistry: DocumentRegistry,
  serviceManager: ServiceManager.IManager,
): Promise<Map<string, IFileTypeData[]>> {
  const specsManager = serviceManager.kernelspecs;
  await specsManager.ready;
  const fileTypes = new Map<string, IFileTypeData[]>();
  const specs = specsManager.specs?.kernelspecs ?? {};
  for (const [spec, specModel] of Object.entries(specs)) {
    if (specModel) {
      // First check if kernel is one of the pre-defined types (Python, R, Julia)
      const exts = AUTO_LANGUAGE_FILETYPE_DATA.get(specModel.language);
      if (exts !== undefined) {
        fileTypes.set(specModel.language, exts);
      } else {
        // If not, try to get languageInfo from codemirror languages
        const languageInfo = languages.findByName(specModel.language);
        // If we managed to find the language, construct the FileTypeData
        // Here we make an assumption that first extension in
        // languageInfo.extensions is the most common one.
        if (languageInfo && languageInfo.extensions) {
          const fileExt = languageInfo.extensions[0];
          const fileType = docRegistry.getFileTypesForPath(
            `test.${fileExt}`,
          )[0];
          // We attempt to get kernelIcon here for specModel.resources
          // If none provided, we return generic kernel icon
          const kernelIcon = await getKernelIcon(specModel, fileType);
          const displayName =
            languageInfo.displayName || specModel.display_name;
          const exts: IFileTypeData[] = [
            {
              fileExt,
              paletteLabel: `New ${displayName} Text Notebook`,
              caption: `Create a new ${displayName} Text Notebook`,
              kernelIcon: kernelIcon,
              launcherLabel: displayName,
              kernelName: spec,
            },
          ];
          fileTypes.set(specModel.language, exts);
        }
      }
    }
  }
  return fileTypes;
}

/**
 * Get all available 'Create New Text Notebook' commands based on configured
 * formats and available kernels
 */
export async function getAvailableCreateTextNotebookCommands(
  includeFormats: string[],
  availableKernelLanguages: Map<string, IFileTypeData[]>,
): Promise<Map<string, IFileTypeData[]>> {
  const numKernels = availableKernelLanguages.size;

  // Initialise a map of 'Create New Text Notebook' command filetypes
  const createTextNotebookCommands = new Map<string, IFileTypeData[]>();

  // Iterate through all JUPYTEXT_CREATE_TEXT_NOTEBOOK_FILETYPE_DATA file types.
  JUPYTEXT_CREATE_TEXT_NOTEBOOK_FILETYPE_DATA.forEach(
    (fileTypes: IFileTypeData[], format: string) => {
      fileTypes.map((fileType: IFileTypeData) => {
        // If format is auto, we need to add all currently available kernels
        // For instance if there are Python and R kernels available, format
        // auto:percent will be replaced by py:percent and R:percent
        if (format.startsWith('auto')) {
          const formatType = format.split(':')[1];
          let mapIndex = 0;
          availableKernelLanguages.forEach(
            (kernelLanguages: IFileTypeData[], kernelKey: string) => {
              const updatedKernelKey = `${kernelKey}:${formatType}`;
              createTextNotebookCommands.set(updatedKernelKey, []);
              mapIndex += 1;
              kernelLanguages.map((kernelLanguageFileType) => {
                // Merge fileType object from kernel and Jupytext format and push
                // it to createTextNotebookCommands
                const updatedKernelLanguageFileType = {
                  ...kernelLanguageFileType,
                };
                updatedKernelLanguageFileType.fileExt = `${updatedKernelLanguageFileType.fileExt}:${formatType}`;
                updatedKernelLanguageFileType.paletteLabel = `${updatedKernelLanguageFileType.paletteLabel} with ${fileType.paletteLabel}`;
                updatedKernelLanguageFileType.caption = `${updatedKernelLanguageFileType.caption} with ${fileType.caption}`;
                updatedKernelLanguageFileType.launcherLabel = `${updatedKernelLanguageFileType.launcherLabel} - ${fileType.launcherLabel}`;
                if (numKernels === mapIndex) {
                  updatedKernelLanguageFileType.separator = true;
                }
                const kernelCommands =
                  createTextNotebookCommands.get(updatedKernelKey);
                if (!kernelCommands) {
                  return;
                }
                kernelCommands.push(updatedKernelLanguageFileType);
                // Update includeFormats with the language specific formats
                // Effectiviely we will add formats like py:light, js:light here
                if (includeFormats.includes(format)) {
                  includeFormats.push(updatedKernelLanguageFileType.fileExt);
                }
              });
            },
          );
        } else {
          if (createTextNotebookCommands.get(format) === undefined) {
            createTextNotebookCommands.set(format, []);
          }
          const formatCommands = createTextNotebookCommands.get(format);
          if (!formatCommands) {
            return;
          }
          formatCommands.push(fileType);
        }
      });
    },
  );
  return createTextNotebookCommands;
}

/**
 * Create New Text Notebook file
 */
export const createNewTextNotebook = async (
  cwd: string,
  kernelId: string,
  kernelName: string,
  format: string,
  commands: CommandRegistry,
) => {
  const model = await commands.execute(CommandIDs.newUntitled, {
    path: cwd,
    type: 'notebook',
    // We should not have auto in format at this point. If somehow we end up having
    // it, ensure we replace by py as Python kernel exists always
    ext: format.replace('auto', 'py'),
  });
  if (model !== undefined) {
    const widget = (await commands.execute('docmanager:open', {
      path: model.path,
      factory: FACTORY,
      kernel: { id: kernelId, name: kernelName },
    })) as unknown as IDocumentWidget;
    widget.isUntitled = true;
    return widget;
  }
};
