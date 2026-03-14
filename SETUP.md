# Coppertales Kennel – Installationsguide

Steg-för-steg för att få Notion → GitHub Pages att fungera.
Beräknad tid: ca 30–45 minuter.

---

## Steg 1 – Skapa GitHub-konto

1. Gå till **https://github.com** och klicka **Sign up**.
2. Välj ett användarnamn (t.ex. `coppertaleskennel`), en e-postadress och ett lösenord.
3. Välj den gratis planen (**Free**).
4. Verifiera e-postadressen via länken du får.

---

## Steg 2 – Skapa ett nytt repo

1. Klicka på **+** (uppe till höger) → **New repository**.
2. Namnge det exakt: `coppertales.se`
   *(eller `coppertaleskennel.github.io` om du vill ha det som standarddomän)*
3. Sätt det till **Public**.
4. Klicka **Create repository**.

---

## Steg 3 – Ladda upp filerna

1. Öppna repot du precis skapade.
2. Klicka på **uploading an existing file** (länken mitt på sidan).
3. Dra och släpp hela mappen `github-pages/` (alla filer och mappar).
4. Klicka **Commit changes**.

> **Tips:** Om du är bekväm med terminalen kan du istället köra:
> ```bash
> git init
> git remote add origin https://github.com/DITT-ANVÄNDARNAMN/coppertales.se.git
> git add .
> git commit -m "Initial commit"
> git push -u origin main
> ```

---

## Steg 4 – Aktivera GitHub Pages

1. Gå till repot → **Settings** → **Pages** (i vänstermenyn).
2. Under **Build and deployment**, välj:
   - Source: **GitHub Actions**
3. Spara. GitHub Pages är nu aktiverat.

---

## Steg 5 – Skapa Notion Integration

1. Gå till **https://www.notion.so/my-integrations**
2. Klicka **+ New integration**.
3. Namnge den `Coppertales Webbsida`.
4. Välj din workspace.
5. Under **Capabilities**: se till att **Read content** är ikryssat.
6. Klicka **Save** och kopiera **Internal Integration Token** (börjar med `secret_…`).

---

## Steg 6 – Koppla Notion-databaser till integrationen

### Bloggen
1. Öppna **📝 Blogg**-databasen i Notion (skapad i NRG's Space).
2. Klicka på **···** (uppe till höger) → **+ Add connections** → välj `Coppertales Webbsida`.
3. Databasens ID är redan känt:
   `f591e264e7d7447f96e99008af68266a`

### Galleriet
1. Öppna **🖼️ Galleri**-databasen i Notion.
2. Klicka på **···** → **+ Add connections** → välj `Coppertales Webbsida`.
3. Databasens ID är redan känt:
   `4fefd2aab913486f89b7adc6bec56923`

---

## Steg 7 – Lägg till Secrets i GitHub

1. Gå till ditt repo → **Settings** → **Secrets and variables** → **Actions**.
2. Klicka **New repository secret** och lägg till dessa tre:

| Secret-namn            | Värde                              |
|------------------------|------------------------------------|
| `NOTION_TOKEN`         | Token från steg 5 (`secret_…`)              |
| `NOTION_BLOG_DB_ID`    | `f591e264e7d7447f96e99008af68266a`          |
| `NOTION_GALLERY_DB_ID` | `4fefd2aab913486f89b7adc6bec56923`          |

---

## Steg 8 – Kör första synken manuellt

1. Gå till repot → **Actions** → **Sync Notion → GitHub Pages**.
2. Klicka **Run workflow** → **Run workflow**.
3. Vänta ca 1–2 minuter.
4. Om allt går grönt är sidan live! 🎉

Adressen är: `https://DITT-ANVÄNDARNAMN.github.io/coppertales.se/`

---

## Steg 9 – Koppla din domän coppertales.se (valfritt)

Om du vill att sidan ska ligga på `coppertales.se` istället:

1. Lägg till en fil som heter `CNAME` i repots rot med bara texten:
   `coppertales.se`
2. Uppdatera DNS-inställningarna hos din domänregistrator:
   Lägg till dessa fyra **A-records** som pekar på GitHub Pages:
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
   Och en **CNAME**-record:
   `www → DITT-ANVÄNDARNAMN.github.io`
3. I GitHub Pages-inställningarna, skriv in `coppertales.se` under **Custom domain**.

DNS-ändringar tar upp till 24 timmar att slå igenom.

---

## Notion-databaser – Fältstruktur

### Blogg-databas
| Fältnamn        | Typ         | Beskrivning                        |
|-----------------|-------------|------------------------------------|
| Titel           | Title       | Inläggets rubrik                   |
| Sammanfattning  | Text        | Kort ingress (visas på startsidan) |
| Datum           | Date        | Publiceringsdatum                  |
| Omslagsbild     | Files       | Omslagsfoto till inlägget          |
| Publicerad      | Checkbox    | ✅ = visas på sidan                |

### Galleri-databas
| Fältnamn  | Typ     | Beskrivning                          |
|-----------|---------|--------------------------------------|
| Titel     | Title   | Bildens titel/beskrivning            |
| Bild      | Files   | Själva bilden                        |
| Kategori  | Select  | T.ex. Mixa, Mila, Kull, Tävling      |
| Datum     | Date    | Datum för bilden                     |

---

## Hur publicerar Louise ett nytt inlägg?

1. Öppna Notion → Blogg-databasen.
2. Klicka **+ New** och fyll i Titel, Sammanfattning, Datum och Omslagsbild.
3. Skriv inläggets text direkt på sidan i Notion.
4. Markera **Publicerad** ✅.
5. Klart! Sidan uppdateras automatiskt nästa morgon kl 06:00.
   Om Louise vill att det ska synas direkt: gå till GitHub → Actions → kör workflow manuellt.

---

## Vanliga frågor

**Q: Kostar det något?**
GitHub Pages är helt gratis för publika repos. Notion gratis-plan räcker gott.

**Q: Hur lägger jag till bilder på hundarna och hjälten?**
Lägg bilderna i mappen `img/` i repot med dessa namn:
- `hero.jpg` – Startsidans hero-bild (liggande, helskärm)
- `kennel.jpg` – Bild i "Om kenneln"-sektionen
- `mixa.jpg`, `mila.jpg`, `ipa.jpg` – Hundbilder
- `cola.jpg` – Cola (kullsektionen)
- `louise.jpg` – Bild på Louise
- `kull1.jpg`, `kull2.jpg`, `kull3.jpg` – Bilder i kullsektionen
- `favicon.png` – Liten ikon i webbläsarens flik

**Q: Hur ändrar jag texten om kenneln och Louise?**
Öppna `index.html` och redigera texten direkt. Committa sedan till GitHub.

**Q: Sidan uppdateras inte direkt.**
GitHub Pages kan ta 1–5 minuter att bygga. Prova rensa webbläsarens cache (Ctrl+Shift+R).
