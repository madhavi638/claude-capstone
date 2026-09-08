name: Test File Sync Agent
description: |
  Automates the process of adding, committing, and pushing all test files and new changes to the appropriate Git branch for a given ticket.
  Ensures all test artifacts are tracked, versioned, and traceable by ticket ID.

argument-hint: |
  Input: Repository URL, Ticket ID (e.g., SC-1), Branch Type (feature, bugfix, hotfix, release), Base Branch (default: main)

tools: ['execute', 'read', 'search', 'edit', 'web', 'github', 'jira', 'todo']

---

## Operation Instructions

### 1. Input & Credential Validation

- Ensure all required inputs are provided: repository URL, ticket ID, branch type.
- Validate branch type: feature, bugfix, hotfix, release.
- Validate base branch (default: main).
- Validate ticket ID format (e.g., SC-1, HMS-101).
- Load GitHub and Jira credentials from `.env` file.

---

### 2. Repository Access

- Check if the repository exists and is
 accessible (`git ls-remote <repository_url>`).
- If the repository is empty, initialize with README.md, commit, and push main branch.
- If access fails, generate `TEST_FILE_SYNC_ERROR_<ticket_id>.md` and stop.

---

### 3. Branch Preparation

- Clone repository if not present locally.
- Checkout and pull the latest base branch (e.g., `main`).
- Check if the target branch exists:
  - If yes: `git checkout <branch_name>` and `git pull origin <branch_name>`
  - If no: `git checkout -b <branch_name>` from base branch and push.

---

### 4. Add, Commit, and Push Test Files

- **Stage all new or changed files (including test files):**
  - Execute: `git add .`
- **Commit the staged files:**
  - Execute: `git commit -m "test: add/update test files and changes for {ticket_id}"`
- **Push the commit to the remote branch:**
  - Execute: `git push origin <branch_name>`
- **If no changes to commit, log "No new changes to push."**

---

### 5. Validation

- Confirm all test files and changes are present in the remote repository under the correct branch.
- Log commit hash, status, and file list for traceability.

---

### 6. Jira Update (Optional)

- Add a comment to the Jira ticket with:
  - Branch name, commit info, and list of test files/changes added.
- Optionally, update ticket status or add branch as a development link.

---

### 7. Output

- Store logs and metadata in `artifacts/git/<ticket_id>/`.
- If any validation fails, generate `TEST_FILE_SYNC_ERROR_<ticket_id>.md` with details.

---

## Best Practices

- Always use meaningful commit messages referencing the ticket ID.
- Validate that all test files and changes are present in the repo after push.
- Use secure credentials for private repos (from `.env`).
- Log all actions for traceability and audit.
- Run this agent after all test file generation steps are complete.