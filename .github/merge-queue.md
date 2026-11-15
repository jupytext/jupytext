# Merge queue for main

The CI workflow runs on `merge_group: checks_requested` as well as pull requests.
GitHub can therefore test each queued change against the current `main` branch
and any changes ahead of it in the queue. The `Pass` job aggregates the CI jobs,
including the security audit and development container smoke test.

## Administrator setup

Merge the workflow change into `main` before enabling the queue. An administrator
must configure the repository rules; write access alone is insufficient.

In **Settings > Rules > Rulesets**, create an active branch ruleset targeting
the default branch (`main`), or extend an existing ruleset without removing its
review requirements, required checks, or bypass restrictions:

- Require a pull request before merging. Preserve the project's review policy.
- Require status checks to pass, including **Pass** from GitHub Actions.
- Require a merge queue.
- Keep force pushes and branch deletion blocked.

Start with these queue settings:

| Setting | Value |
| --- | --- |
| Merge method | Squash |
| Build concurrency | 1 |
| Only merge non-failing pull requests | Enabled |
| Status check timeout | 60 minutes |
| Minimum pull requests to merge | 1 |
| Maximum pull requests to merge | 1 |

The queue tests changes against the latest base branch, so a separate requirement
for authors to update their branches before enqueueing is unnecessary. Preserve
any other required checks, but ensure their workflows also run on `merge_group`
before activating the rule. In particular, the separate website deployment
workflow does not currently run on that event; do not make its check required
for the queue without first adding merge-group build support.

## Verification

Use a reviewed pull request with successful checks to verify the setup:

1. Add the pull request to the merge queue from GitHub's merge panel.
2. Confirm a new CI run starts with the `merge_group` event on a
   `gh-readonly-queue/main/...` branch.
3. Confirm **Pass** succeeds for that merge group before GitHub merges it.

To inspect queue CI runs:

```bash
gh run list --repo jupytext/jupytext --workflow ci.yml --event merge_group
```

If a group fails or times out, inspect its checks and fix the cause before
enqueueing the pull request again. Increase build concurrency only after checking
runner capacity and queue CI duration.
