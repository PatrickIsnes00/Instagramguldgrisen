# Guldgrisen Instagram – arbetsbeskrivning

Det här repot innehåller bilderna till @guldgrisen och reglerna för det dagliga flödet.
Tre publiceringsdagar per vecka: **måndag** (inlägg + story), **onsdag** (bara inlägg) och **fredag** (inlägg + story). Allt skapas som **utkast** i Metricool.
Patrick granskar och godkänner allt innan publicering.

## Struktur

- `render.py` – gör `post.jpg` och `story.jpg` av en `spec.json`
- `posts/ÅÅÅÅ-MM-DD/spec.json` – innehåll, layout, tema och bildtext för den dagen
- `history.json` – logg över publicerade ämnen (används för variation)

## Månadstak: max 20 i Metricool

Metricool-planen tillåter max 20 schemalagda objekt per kalendermånad. Varje inlägg och varje story räknas som ett objekt.

- Summera `metricool_items` i `history.json` för publiceringsdagens månad innan något skapas.
- Får båda inte plats: skapa bara inlägget och hoppa över storyn.
- Är taket nått (20): skapa ingenting och rapportera det.
- Spara alltid antalet skapade objekt i `metricool_items` för dagen.

## Rutin (körs kvällen före varje publiceringsdag)

1. Läs `history.json` och de senaste 14 dagarnas `spec.json`.
2. Publiceringsdag = imorgon. Kontrollera veckodagen: måndag och fredag = inlägg + story, onsdag = bara inlägg. Kontrollera månadstaket ovan. Välj sedan ämne enligt variationsreglerna nedan.
3. Hämta fakta från rätt guide eller kalkylator på guldgrisen.se (WebFetch). Kontrollera regler som kan ändras (skatt, ränteavdrag, amorteringskrav, föräldrapenning) med en webbsökning.
4. Räkna ut alla siffror med Python, inte i huvudet.
5. Skriv `posts/<datum>/spec.json`, kör `python3 render.py posts/<datum>/spec.json` och titta på båda bilderna.
6. Committa och pusha till `main`.
7. Skapa utkast i Metricool (varumärke `guldgrisen`, blogId 7801849, tidszon Europe/Stockholm) med `draft: true`:
   - Inlägg: `instagramData.type = "POST"`, bildtext från `caption`, media = raw-länken till `post.jpg`
   - Story: `instagramData.type = "STORY"`, ingen text, media = raw-länken till `story.jpg`
   - Standardtider: inlägg 07:42, story 17:13 (om inget annat anges)
8. Lägg till dagen i `history.json` (med `metricool_items`) och pusha.

Rå-länkar: `https://raw.githubusercontent.com/<ägare>/Instagramguldgrisen/main/posts/<datum>/post.jpg`

## Variationsregler

- Samma **kategori** får inte förekomma två publiceringsdagar i rad, och högst en gång per vecka.
- Samma **layout** för inlägget får inte förekomma två publiceringsdagar i rad.
- Samma **tema** (färg) får inte förekomma två publiceringsdagar i rad.
- På onsdagar finns ingen story: utelämna `story` i spec.json så renderas bara `post.jpg`.
- Storyn ska ha en annan layout än inlägget samma dag och gärna en annan vinkel (fråga, myt, steg).
- Upprepa aldrig samma ämne inom 30 dagar.
- Ungefär en gång per vecka: lyft en kalkylator eller Mitt konto som verktyg.

## Kategorier och ämnesbank

| Kategori | Exempel på ämnen | Källa på guldgrisen.se |
|---|---|---|
| `bolan` | Förhandla räntan, rörlig eller bunden, amorteringskrav, kontantinsats, hur mycket får jag låna | guide-bolan, guide-hur-mycket-kan-jag-lana, hur-mycket-kan-jag-lana |
| `sparande` | Ränta på ränta, börja med 500 kr/mån, sparmål, tid slår timing | guide-kom-igang, guide-ranta-pa-ranta-forklarat, ranta-pa-ranta, sparmal |
| `investera` | ISK vs KF vs vanligt konto, vad är en fond, fondavgifter, 4 %-regeln | guide-isk-kapitalforsakring, guide-vad-ar-en-fond, fondavgifter, guide-fyraprocentsregeln |
| `budget` | Budget utan stress, prenumerationsrensning, små utgifter över tid | guide-budgetering, hushallsbudget, budget, prenumerationer |
| `trygghet` | Buffert, bedrägerier (SMS, telefon, falska investeringar) | guide-buffert, buffertkalkylator, guide-bedragerier |
| `lon_familj` | Brutto till netto, föräldrapenning, planering inför föräldraledighet | guide-nettolon, nettolon-kalkylator, guide-foraldrapenning |
| `lan` | Billån och restvärde, skuld och amortering, dyra smålån | guide-billan-restvarde, billan-kalkylator, skuldkalkylator |
| `beslut` | Hyra eller köpa, amortera eller investera, tänk innan du sparar | guide-hyra-eller-kopa, guide-amortera-eller-investera |
| `barn` | Veckopeng, sparmål för barn, prata pengar med barn | barn |
| `mitt_konto` | Spara budgeten, följ sparmål, logga in med e-postkod | mitt-konto |
| `ordlista` | Förklara ett begrepp (t.ex. snittränta, belåningsgrad, KALP) | ordlista |

## Layouter

- `stat` – stor siffra + räkneexempel (kräver `number`, `unit`, `rows`)
- `tips` – 3–5 numrerade steg
- `question` – en fråga som väcker nyfikenhet (bra för story)
- `compare` – A mot B med två värden och en slutsats
- `myth` – myt kontra fakta

Teman: `green`, `cream`, `gold`, `ink`.

## Innehållsregler

- Svenska, du-tilltal, rakt och uppmuntrande. Ingen hype eller press.
- Inga personliga investeringsråd. Skriv ”räkneexempel” och ange antaganden (avkastning, ränta, tid).
- Avkastningsexempel: ange antagen avkastning och att framtida avkastning inte är garanterad.
- Bildtext: krok på första raden, räkneexemplet, 2–4 konkreta steg eller insikter, hänvisning till guide/kalkylator (”länk i bio”), 6–10 hashtags.
- Max cirka 90 ord på inläggsbilden. Ingen text i storyn utanför bilden.
- Inga påhittade siffror om verkligheten (t.ex. ”70 % av svenskarna …”) utan källa.
