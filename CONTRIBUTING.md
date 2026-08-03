
# Contributing to Macapype
(largely inspired by the CONTRIBUTING.md from [nipype project](https://github.com/nipy/nipype/blob/master/CONTRIBUTING.md))

Welcome to **Macapype**! We are excited to have you contribute to our open-source project for non-human primate anatomical MRI processing pipelines.

These guidelines provide a quick start on how to report issues, contribute code, and submit Pull Requests (PRs).

---

## 1. Getting Started & Prerequisites

To contribute to Macapype on GitHub:
1. **Create a GitHub account:** If you do not have one, sign up for a free account at [github.com/join](https://github.com/join).
2. **Set up Git:** Ensure Git is installed and configured on your machine with your name and email address.

---

## 2. Opening Issues & Using Labels

Before opening a new issue, check existing open issues on [Macapype Issues](https://github.com/Macatools/macapype/issues) to avoid duplicates. When opening an issue, please use one of the primary labels below:

### ![bug](https://img.shields.io/badge/-bug-fc2929.svg)
Use this label for pipeline crashes, unexpected errors, or incorrect image processing outputs.
* **What to include:**
  * Operating system, Python version, Macapype version, and relevant underlying software (e.g., Nipype, AFNI, ANTs, FSL, SPM).
  * A minimal reproducible script or command line call.
  * Full error tracebacks.
  * **Images & Screenshots:** Attach visual artifacts, failed brain masks/segmentations, or Quality Control (QC) output images to illustrate the defect.

### ![feature](https://img.shields.io/badge/-feature-a2eeef.svg)
Use this label to request new pipelines, support for additional neuroimaging packages, or enhancements to existing workflows.
* **What to include:**
  * Clear explanation of the feature and its scientific or operational benefit.
  * Expected input/output specifications.
  * **Diagrams & Visuals:** Attach workflow flowcharts, node diagrams, or target output images where applicable.

### ![documentation](https://img.shields.io/badge/-documentation-0075ca.svg)
Use this label to report typos, missing docstrings, unclear installation steps, or request new tutorials.
* **What to include:**
  * Link or file location of the relevant documentation page.
  * Suggested revisions or additions.
  * **Screenshots:** Attach screenshots showing rendering or formatting errors if applicable.

---

## 3. Development Workflow & Pull Requests

### Step 1: Fork and Clone
1. Fork the [Macatools/macapype](https://github.com/Macatools/macapype) repository to your GitHub profile by clicking **Fork**.
2. Clone your fork to your local environment:
   ```bash
   git clone https://github.com/<your-username>/macapype.git
   cd macapype
   ```
3. Set up the upstream repository reference:
   ```bash
   git remote add upstream https://github.com/Macatools/macapype.git
   ```

### Step 2: Create a Feature Branch
Always base your work on the latest state of the default `main` branch:
```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout -b my-feature-branch
```

### Step 3: Make Changes & Test
* Implement your edits, bug fixes, or documentation updates.
* Ensure code follows standard Python (PEP8) formatting.
* Test your changes locally to confirm existing pipelines remain functional.

### Step 4: Commit and Push
Commit your changes with clear, descriptive commit messages:
```bash
git add .
git commit -m "FIX: Correct brain extraction node behavior"
git push origin my-feature-branch
```

### Step 5: Submit and Link Your Pull Request
1. Go to [Macatools/macapype Pull Requests](https://github.com/Macatools/macapype/pulls) and click **New Pull Request**.
2. Select `my-feature-branch` from your fork to merge into `Macatools/macapype:main`.
3. Add a descriptive title with standard prefixes:
   * `[FIX]` Bug fix
   * `[ENH]` Enhancement / Feature
   * `[DOC]` Documentation update
4. **Link to a previously created issue:** In the PR description, reference the issue using keywords so GitHub automatically closes it when merged:
   * Examples: `Fixes #320`, `Closes #123`, or `Resolves #320`.

---

Thank you for helping improve Macapype!
