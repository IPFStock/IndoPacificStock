# Indo Pacific Films — Live Rebuild Checklist (Maintenance Mode)

**Approach:** Rebuild on live WordPress (GoDaddy cPanel). Site may be down or in maintenance for several days. **Email stays active** — do not change MX records or delete mail accounts.

**Brand:** Light editorial (cream/navy, serif headlines). **Separate company** from Indo Pacific Stock — no cross-links.

**Stack:** GeneratePress + custom child theme `indo-pacific-films` · Block editor · LiteSpeed/cache · &lt;10 plugins

---

## Phase 0 — Before you touch the theme

- [ ] **Note live admin URL** and ensure you can log in
- [ ] **cPanel → Stats** — record file count (inodes) and disk used
- [ ] **Free space where safe** (helps installs and cache):
  - [ ] Delete `public_html/ipftesting/` (failed staging) if still present
  - [ ] Delete `indopacific.zip` and Duplicator/installer leftovers in staging or root
  - [ ] Review `application_backups/` — remove old backups you do not need
  - [ ] Empty WP trash; remove unused plugins you will never use again
- [ ] **Full backup (download to Mac)** — Duplicator or All-in-One WP Migration export; store offline
- [ ] **Export list of pages/posts** (optional): Tools → Export → All content
- [ ] **Screenshot or note** current menu structure, key URLs, contact form recipient email
- [ ] **Confirm email works** — send/receive one test message (do not change MX)

---

## Phase 1 — Maintenance mode ON

- [ ] Install **WP Maintenance Mode** or **SeedProd** (free) *or* use GeneratePress maintenance after theme install
- [ ] Enable maintenance — visitors see “coming back soon”; **you** can preview while logged in
- [ ] Optional: maintenance page text + contact email only (no Stock link)
- [ ] Tell anyone who needs the site that it is down for redesign (email still works)

**Email reminder:** Maintenance plugins only affect the website. Mail at your domain is unchanged.

---

## Phase 2 — Clean up plugins & prep (still on Brooklyn until child theme ready)

- [ ] **Plugins →** deactivate plugins you will not need post-rebuild (sliders, old builders, duplicate cache plugins)
- [ ] **Do not delete Brooklyn yet** until new theme is verified
- [ ] Install **GeneratePress** (free) — **do not activate yet**
- [ ] Install **GenerateBlocks** or **Kadence Blocks** (free) if you want layout blocks
- [ ] Install **LiteSpeed Cache** (or use GoDaddy’s cache if already there) — configure after new theme is live
- [ ] PHP version in cPanel **MultiPHP** → **8.1** or **8.2**

---

## Phase 3 — Child theme (light editorial)

- [ ] Receive/install child theme **`indo-pacific-films`** (zip upload: Appearance → Themes → Add New → Upload)
- [ ] **Activate** `Indo Pacific Films` child theme (GeneratePress parent must stay installed)
- [ ] **Appearance → Customize** — set:
  - [ ] Site identity (logo or wordmark)
  - [ ] Colors: background cream `#F5F0E8`, text navy `#1E293B`, accent coral or amber (not Stock green)
  - [ ] Typography: serif headlines, sans body
  - [ ] Layout: container width, header layout
- [ ] **Settings → Reading** — confirm homepage is a static page (not blog) when ready
- [ ] **Settings → Permalinks** — Post name (`/%postname%/`) → Save (flushes rewrite rules)

---

## Phase 4 — Rebuild pages (block editor)

Use **existing Media Library** — no re-upload unless you want new assets.

### Core pages

- [ ] **Home** — hero still, one-line positioning, 3–6 featured projects, showreel embed, contact CTA
- [ ] **Work / Projects** — grid of case studies (BBC, Nat Geo, Aman, etc.)
- [ ] **Showreels** — YouTube/Vimeo embeds (channel: @indopacificfilms)
- [ ] **Services** — filming, RED, drone, underwater, conservation, production support, etc.
- [ ] **About** — story, clients, awards (partner logos if desired)
- [ ] **Journal** — blog index (Posts page)
- [ ] **Contact** — form (WPForms Lite or block form); test delivery to correct inbox

### Navigation

- [ ] **Appearance → Menus** — primary menu matches new structure
- [ ] Footer: company name, copyright, optional social icons — **no Stock link**

### Content migration tips

- [ ] Copy text from old Brooklyn pages into new blocks (don’t try to “convert” Brooklyn layouts)
- [ ] Re-assign featured images from Media Library
- [ ] Old blog posts: usually stay as Posts; update featured images if needed
- [ ] Delete or unpublish obsolete Brooklyn demo pages when replaced

---

## Phase 5 — Performance & SEO

- [ ] **LiteSpeed Cache** (or host cache): enable page cache, browser cache; exclude logged-in users
- [ ] **Images:** install ShortPixel or Imagify — WebP for new uploads; bulk optimize if quota allows
- [ ] **Remove** deactivated bloat plugins permanently
- [ ] **Replace Brooklyn** parent theme only after everything works (optional delete to save space/inodes)
- [ ] **Yoast SEO** or **Rank Math** (optional): title/description for Home, About, Contact
- [ ] Test mobile layout on phone

---

## Phase 6 — Pre-launch QA (logged in + logged out)

- [ ] Homepage loads; no broken images
- [ ] All menu links work (no 404s)
- [ ] Contact form sends to correct email
- [ ] Showreel/video embeds play
- [ ] Journal/blog lists and single posts open
- [ ] **No links** to indopacificstock.com anywhere
- [ ] **Privacy:** staging URLs (`/ipftesting/`) removed or blocked if folder still exists
- [ ] [PageSpeed Insights](https://pagespeed.web.dev/) — note score (target 80+ mobile reasonable on WP)

---

## Phase 7 — Go live

- [ ] **Disable maintenance mode**
- [ ] Visit site in private/incognito window — confirm public view
- [ ] Submit sitemap in Google Search Console if you use it (optional)
- [ ] Delete Duplicator/installer files from server if any remain
- [ ] **cPanel Stats** — check disk/inodes after cleanup

---

## Phase 8 — After launch (within 1 week)

- [ ] Monitor contact form and email deliverability
- [ ] Fix any broken old URLs (redirect plugin if slugs changed)
- [ ] Remove Wordfence/maintenance plugin bloat if duplicated
- [ ] Second backup of **new** site to Mac

---

## Do NOT do during rebuild

| Avoid | Why |
|-------|-----|
| Change MX / DNS mail records | Breaks email |
| Delete `mail` folder in cPanel | Breaks email |
| Full staging clone on same account | Inode/disk limits |
| Elementor + heavy page builders | Slow, bloated |
| Cross-link to Indo Pacific Stock | Separate companies |
| Delete `wp-content/uploads` | Breaks all media |

---

## Plugin shortlist (target &lt;10 active)

| Plugin | Purpose |
|--------|---------|
| GeneratePress | Parent theme |
| (Child theme) | indo-pacific-films |
| GenerateBlocks / Kadence Blocks | Layout (optional) |
| LiteSpeed Cache or host cache | Speed |
| WPForms Lite | Contact |
| Wordfence or iThemes Security | Keep if already configured |
| ShortPixel / Imagify | Images (optional) |
| Yoast or Rank Math | SEO (optional) |

---

## When child theme is ready

1. Child theme zip will be built in Cursor (`indo-pacific-films` folder).
2. Upload via **Appearance → Themes → Add New → Upload Theme**.
3. Activate after GeneratePress is installed.

---

## Support contacts

- **GoDaddy hosting:** support if disk/inode errors return during install
- **Films site content:** your existing WP admin + Media Library

*Last updated: rebuild plan B — maintenance on live.*
