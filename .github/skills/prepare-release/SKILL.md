---
name: prepare-release
description: "Prepare a new release for blender-driving-scenario-creator. Use when: bumping version, updating changelog, creating release commit and tag. Triggers: release, version bump, changelog update, prepare release, new version."
argument-hint: "Provide the new version number, e.g. 0.30.0"
---

# Prepare Release

Automate the release preparation workflow for the Blender Driving Scenario Creator addon.

## When to Use

- Preparing a new release version
- Bumping the version number
- Updating the changelog for a release

## Procedure

Follow these steps **in order**. Do NOT skip any step.

### Step 1: Check the current branch

Run in terminal:
```
git branch --show-current
```

If the current branch is not `main`, stop and tell the user that releases must be prepared from `main`.
Ask them to prepare the `main` branch first and wait for explicit confirmation before continuing the release workflow.

### Step 2: Determine the previous release tag

Run in terminal:
```
git tag --sort=-v:refname | head -1
```
This gives the latest tag (e.g. `v0.29.2`). Extract the version components `MAJOR.MINOR.PATCH` from it.

### Step 3: Review changes since last release

Run in terminal:
```
git log <PREV_TAG>..HEAD --format='--- %h %s%n%B'
```
Review the complete commit messages, including their body text, rather than only the summary line. Extract every release-relevant change from the full messages, then formulate concise changelog entries from those details. Show the commits and summarize the changes grouped into categories: **Added**, **Changed**, **Fixed**, **Removed** (only include categories that have entries).

### Step 4: Determine the new version number

Apply semantic versioning based on the changes found in Step 3:

- If **only** bugfixes (all changes fall under **Fixed**): increment the PATCH version. Example: `0.29.2` → `0.29.3`
- If there are any new features (**Added**), behavioral changes (**Changed**), or removals (**Removed**): increment the MINOR version and reset PATCH to 0. Example: `0.29.2` → `0.30.0`

The MAJOR version stays at `0` until the tool is considered stable.

Proceed immediately to update the files. Do NOT ask the user for confirmation before making file changes.

### Step 5: Update version in `addon/__init__.py`

Find the line:
```python
'version' : (X, Y, Z),
```
Replace `(X, Y, Z)` with the new version tuple. For version `0.30.0`, use `(0, 30, 0)`.

### Step 6: Update `CHANGELOG.md`

The changelog follows [Keep a Changelog](https://keepachangelog.com/) format.

#### 4a: Add new version section

Replace:
```markdown
## [Unreleased]
```
with:
```markdown
## [Unreleased]

## [NEW_VERSION] - YYYY-MM-DD
```
where `YYYY-MM-DD` is **today's date**.

Below the new version header, add the categorized changes from Step 2 using these section headers as needed:
```markdown
### Added
### Changed
### Fixed
### Removed
```

**Writing style for changelog entries:**
- Do NOT start entries with the category verb (e.g. don't write "Add ...", "Fix ...", "Remove ...").
- Instead, describe **what** was added/fixed/changed as a noun phrase or concise description.
- Examples:
  - **Added**: "Guardrail support for road cross sections" (not "Add guardrail to road cross section")
  - **Fixed**: "Crash due to export options not present in Blender 5.x" (not "Fix export options not present in Blender 5.")
  - **Fixed**: "Popup window closing behavior for Blender 5.x compatibility" (not "Fixed popup window closing...")
- Look at the existing entries in `CHANGELOG.md` for reference on tone and style.

#### 4b: Update bottom reference links

The bottom of `CHANGELOG.md` has reference-style links. Update them:

1. Change the `[Unreleased]` link to compare against the new tag:
   ```
   [Unreleased]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/vNEW_VERSION...HEAD
   ```

2. Add a new comparison link for the new version right below the `[Unreleased]` line:
   ```
   [NEW_VERSION]: https://github.com/johschmitz/blender-driving-scenario-creator/compare/vPREV_VERSION...vNEW_VERSION
   ```
   where `PREV_VERSION` is extracted from `PREV_TAG` (without the `v` prefix).

### Step 7: Pause for user review

After updating `addon/__init__.py` and `CHANGELOG.md`, **stop immediately**. Do not create a commit or tag yet.
Briefly tell the user both files have been updated and ask them to review the changes directly in the files.
Wait for explicit confirmation before continuing with the remaining steps.

### Step 8: Create the release commit

Run in terminal:
```
git add addon/__init__.py CHANGELOG.md
git commit -m "Update version number and changelog"
```

### Step 9: Create the annotated git tag

Run in terminal:
```
git tag -a vNEW_VERSION -m "Version NEW_VERSION"
```

### Step 10: Confirm

Show the user:
- The new version number
- The commit hash (from `git log -1 --oneline`)
- The tag (from `git tag -n1 vNEW_VERSION`)
- Remind them to push with `git push --follow-tags` when ready
