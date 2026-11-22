# Integration Testing

This folder contains the integration tests of the extension.

They are defined using [Playwright](https://playwright.dev/docs/intro) test runner
and the [Galata](https://github.com/jupyterlab/jupyterlab/tree/main/galata) fixtures.
The specs import those fixtures directly because Galata's CommonJS entry point
loads a benchmark reporter that requires Vega 5.

The Playwright configuration is defined in [playwright.config.js](./playwright.config.js).

The JupyterLab server configuration to use for the integration test is defined
in [jupyter_server_test_config.py](./jupyter_server_test_config.py).

The default configuration will produce video for failing tests and an HTML report.

> There is a new experimental UI mode that you may fall in love with; see [that video](https://www.youtube.com/watch?v=jF0yA-JLQW0).

## Run the tests

> All commands are assumed to be executed from the _jupyterlab-jupytext-extension_ directory

To run the tests, you need to:

1. Compile the extension:

```sh
jlpm install
jlpm build:prod
```

> Check the extension is installed in JupyterLab.

2. Install test dependencies (needed only once):

```sh
cd ./ui-tests
jlpm install
jlpm playwright install
cd ..
```

3. Execute the [Playwright](https://playwright.dev/docs/intro) tests:

```sh
cd ./ui-tests
jlpm playwright test
```

Test results will be shown in the terminal. In case of any test failures, the test report
will be opened in your browser at the end of the tests execution; see
[Playwright documentation](https://playwright.dev/docs/test-reporters#html-reporter)
for configuring that behavior.

## Update the tests snapshots

> All commands are assumed to be executed from the _main-menu_ directory

If you are comparing snapshots to validate your tests, you may need to update
the reference snapshots stored in the repository. To do that, you need to:

1. Compile the extension:

```sh
jlpm install
jlpm build:prod
```

> Check the extension is installed in JupyterLab.

2. Install test dependencies (needed only once):

```sh
cd ./ui-tests
jlpm install
jlpm playwright install
cd ..
```

3. Execute the [Playwright](https://playwright.dev/docs/intro) command:

```sh
cd ./ui-tests
jlpm playwright test -u
```

To regenerate snapshots on CI, open **Actions → Update Playwright Snapshots**,
select **Run workflow**, and choose the branch to test. Download the
`playwright-snapshots` artifact from the completed run and extract it. To apply a
nonempty patch, run `git apply /path/to/playwright-snapshots.patch` from the root
of that branch's checkout, then review and commit the updated snapshots.
For a fork PR, run the workflow in the fork or regenerate the snapshots locally.

## Create tests

> All commands are assumed to be executed from the _main-menu_ directory

To create tests, the easiest way is to use the code generator tool of playwright:

1. Compile the extension:

```sh
jlpm install
jlpm build:prod
```

> Check the extension is installed in JupyterLab.

2. Install test dependencies (needed only once):

```sh
cd ./ui-tests
jlpm install
jlpm playwright install
cd ..
```

3. Start the server:

```sh
cd ./ui-tests
jlpm start
```

4. Execute the [Playwright code generator](https://playwright.dev/docs/codegen) in **another terminal**:

```sh
cd ./ui-tests
jlpm playwright codegen localhost:8888
```

## Debug tests

> All commands are assumed to be executed from the _main-menu_ directory

To debug tests, a good way is to use the inspector tool of playwright:

1. Compile the extension:

```sh
jlpm install
jlpm build:prod
```

> Check the extension is installed in JupyterLab.

2. Install test dependencies (needed only once):

```sh
cd ./ui-tests
jlpm install
jlpm playwright install
cd ..
```

3. Execute the Playwright tests in [debug mode](https://playwright.dev/docs/debug):

```sh
cd ./ui-tests
jlpm playwright test --debug
```

## Upgrade Playwright and the browsers

To update the web browser versions, you must update the package `@playwright/test`:

```sh
cd ./ui-tests
jlpm up "@playwright/test"
jlpm playwright install
```
