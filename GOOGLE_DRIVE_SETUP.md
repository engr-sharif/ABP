# Google Drive sync — setup guide

This explains how to create the Google Cloud project + OAuth credential the ABP
Visualizer needs to save/open project files directly in Google Drive.

**Do the connectivity check first.** In the app: **Export tab → "Test Google
connectivity"**, run it on the *deployed* page (`engr-sharif.github.io/...`).
If any endpoint shows ✗, your network blocks Google and in-app Drive sync will
not work — stop here and use the project-file + shared-folder workflow instead.
Only proceed if all three are ✓.

---

## What we're setting up, in plain terms

For the website to read/write your Google Drive, Google requires the site to be
a **registered application** with an **OAuth Client ID**. The user (you) clicks
"Connect Google Drive," signs in through Google's own popup, and grants the app
permission. No passwords ever touch the website.

We use the **least-privilege scope, `drive.file`** — the app can only see files
*it* created, never the rest of your Drive. Each person's files live in *their
own* Drive, so multi-user is automatic and private.

You need: a Google account (a Google Workspace/org account is fine, but see the
"org-managed account" note at the end — your IT may need to approve it).

Total time: ~15–20 minutes, one-time.

---

## Step 1 — Create a Google Cloud project

1. Go to <https://console.cloud.google.com/>.
2. Top bar, click the **project dropdown** (says "Select a project") → **New Project**.
3. Name it something like `ABP-Visualizer`. Leave Organization/Location as-is
   (or pick your org). Click **Create**.
4. Wait ~10 seconds, then make sure the new project is selected in the top bar.

## Step 2 — Enable the Google Drive API

1. Left menu (☰) → **APIs & Services → Library**.
2. Search **Google Drive API** → click it → **Enable**.
   (This is the only API we need. Don't enable anything else.)

## Step 3 — Configure the OAuth consent screen

This is the "who is this app and what does it ask for" screen users see.

1. Left menu → **APIs & Services → OAuth consent screen**.
2. **User Type:**
   - Choose **Internal** if everyone using the tool is in your Google Workspace
     organization (simplest — no verification, no test-user list).
   - Choose **External** if any user is outside your org (e.g. personal Gmail).
     External works fine but starts in "Testing" mode (see Step 6).
   - Click **Create**.
3. **App information:**
   - App name: `ABP Visualizer`
   - User support email: your email
   - Developer contact email: your email
   - (Logo/links optional — skip.)
   - **Save and Continue.**
4. **Scopes:** click **Add or Remove Scopes**, search for and check:
   - `.../auth/drive.file` — "See, edit, create, and delete only the specific
     Google Drive files you use with this app."
   - **Update → Save and Continue.**
5. **Test users** (only appears for External): add the Google accounts (emails)
   of everyone who'll use the tool while it's in Testing mode. **Save and Continue.**
6. Review → **Back to Dashboard.**

## Step 4 — Create the OAuth Client ID

1. Left menu → **APIs & Services → Credentials**.
2. **+ Create Credentials → OAuth client ID.**
3. **Application type: Web application.**
4. Name: `ABP Visualizer Web`.
5. **Authorized JavaScript origins** — click **+ Add URI** and add the exact
   origin(s) the app is served from (origin = scheme + host, NO path):
   - `https://engr-sharif.github.io`
   - (add `http://localhost:8000` or whatever you use for local testing, if any)
6. **Authorized redirect URIs** — for the token-model flow we use, you can leave
   this empty, OR add the same origin if Google asks. (Google Identity Services
   token flow doesn't require a redirect URI.)
7. Click **Create.**
8. A dialog shows your **Client ID** (looks like
   `1234567890-abc123def456.apps.googleusercontent.com`). **Copy it.** You do
   NOT need the client secret for a browser app — ignore it.

## Step 5 — Give the Client ID to the app

The app has a field for it (no code edit needed):

1. Open the app → **Export** tab → **Google Drive sync**.
2. Paste your Client ID into the **OAuth Client ID** field → click **Save**.
   (It's stored in your browser's localStorage. The Client ID is not a secret —
   it's designed to live in public client-side code — so this is safe.)
3. Click **Connect Google Drive** → a Google sign-in popup appears → choose your
   account → grant the `drive.file` permission.
4. Status flips to **Connected ✓**. Now:
   - **☁ Save to Drive** uploads the current project into a folder named
     **"ABP Visualizer Projects"** in your Drive. The first save creates the
     file; later saves update that same file.
   - **☁ Open from Drive** lists your `.abp.json` projects → pick one → it loads,
     and subsequent **Save to Drive** updates that file.

Access tokens last ~1 hour; if it expires, click **Connect Google Drive** again.

## Step 6 — Publishing (External apps only)

While in **Testing**, only the test users you listed can connect, and Google
shows an "unverified app" warning they must click through ("Advanced → Go to
ABP Visualizer"). That's fine for a small team.

For wider use without the warning, you'd **Publish** the app (OAuth consent
screen → Publishing status → Publish App). With only the `drive.file` scope,
Google generally does **not** require the heavyweight security assessment that
broader scopes trigger — `drive.file` is a "non-sensitive/recommended" scope.
For an internal team tool, staying in Testing (or Internal user type) is usually
simplest.

---

## Notes & gotchas

- **`drive.file` only.** Never request `drive` (full Drive) or `drive.readonly`
  unless you truly need to read files the app didn't create — those are
  "restricted" scopes and trigger Google's CASA security review.
- **Origins must match exactly.** `https://engr-sharif.github.io` ≠
  `https://engr-sharif.github.io/` (trailing slash) ≠ a custom domain. If you
  later move to a custom domain, add it to Authorized JavaScript origins.
- **Tokens are short-lived (~1 hour).** The app will ask you to re-connect when
  a token expires. That's normal and not a misconfiguration.
- **Org-managed accounts:** if your Google account is managed by a company/agency
  Workspace, an admin may have to **allow the app** (by Client ID) or unblock
  third-party API access. If "Connect Google Drive" fails with an admin/policy
  error, that's the cause — send your IT admin the Client ID and the single
  scope (`drive.file`).
- **The Client ID is not a secret.** It's designed to live in public client-side
  code. The OAuth consent + the Authorized origins are what actually protect
  access. (The client *secret* would be sensitive — but browser apps don't use it.)

---

## What happens after setup (the in-app experience we'll build)

1. **Connect Google Drive** button → Google sign-in popup → grant access.
2. **Save to Drive** → uploads the same project JSON the app already generates,
   into the user's own Drive (in an app-created folder).
3. **Open from Drive** → lists the user's ABP project files → pick one → loads it.
4. Disconnect any time; tokens are never stored server-side (there is no server).

This reuses the exact project-file payload that **Save Project / Open Project**
already produce, so Drive sync is just "the same file, stored in your Drive
instead of your Downloads folder."
