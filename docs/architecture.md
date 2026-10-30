# Architecture

Diagrams of how Snap Safe India is put together and how a photo moves through it. They follow the same four steps the
project has always been explained with (attack, plan, edit, re-attack) and the file layout in the README. The prose is in
[how-it-works.md](how-it-works.md).

## The system

```mermaid
flowchart LR
  subgraph clients["Clients"]
    W["Web page<br/>static/index.html"]
    T["Telegram bot<br/>app/telegram_bot.py<br/>(separate process)"]
  end
  subgraph server["FastAPI server, Docker on Render"]
    API["API<br/>app/main.py<br/>/api/run, /api/sample, /api/samples, /api/status"]
    AG["Agent loop<br/>app/agent.py"]
    MD["Model calls, pacing, checks<br/>app/meta.py"]
    PL["Image pipeline<br/>app/pipeline.py"]
    RG["Region packs<br/>app/regions"]
    SM[("Recorded samples<br/>static/samples")]
  end
  GM[("Vision model<br/>Gemini 3 Flash or Gemma 4<br/>Google AI Studio")]
  TG[("Telegram Bot API")]

  W -->|"photos, caption, language, access code"| API
  API --> AG
  T --> AG
  T <-->|"messages, photos"| TG
  AG --> MD
  AG --> PL
  MD --> RG
  MD -->|"photo and prompt"| GM
  GM -->|"exposure graph as JSON"| MD
  API -.->|"replay, no model call"| SM
```

## What happens to one photo

```mermaid
flowchart TD
  A["Upload a photo and, optionally, a caption"] --> B["Decode: upright, at most 2048 px, read the EXIF"]
  B --> C1["1. Attack<br/>the model returns an exposure graph"]
  B --> C2["Text check<br/>transcribe the photo, count IDs with regular expressions"]
  C1 --> D{"Report rates details lower<br/>than the regex counts?"}
  C2 --> D
  D -->|"yes"| E["One retry, told the counts and never the values"]
  D -->|"no"| F
  E --> F["2. Plan<br/>cheapest clues to remove, a minimum-cost hitting set"]
  F --> G["3. Edit<br/>pixelate or inpaint inside each snapped box"]
  G --> H["4. Re-attack the edited photo"]
  H --> I{"Anything still above the limits,<br/>and fewer than 4 attacks so far?"}
  I -->|"yes"| F
  I -->|"no"| J["Done: PNG with no EXIF or GPS,<br/>what was hidden, exposure before and after"]
```

## A live check, step by step

```mermaid
sequenceDiagram
  actor U as Person
  participant P as Web page
  participant S as Server
  participant A as Agent
  participant M as Vision model

  U->>P: choose a photo, a language, enter the access code
  P->>S: POST /api/run
  S->>S: check the code, the rate limits, one run at a time
  S->>A: run(photo, caption)
  loop up to 4 attacks
    A->>M: photo and prompt, with the region note and language
    M-->>A: exposure graph (JSON)
    A->>A: plan the edits, then edit inside the boxes
    A-->>P: progress events
  end
  A-->>P: done: safe copy, report, list of what was hidden
  P-->>U: before and after, the report, and choices to keep a detail
```

## What the model returns

```mermaid
classDiagram
  class Clue {
    id
    box
    label
    kind
    observation
    legibility
    removal_impact
    suggested
  }
  class Way {
    clues
    level 1 to 4
    confidence
  }
  class Inference {
    category
    reasoning
  }
  Inference "1" --> "many" Way : reached by
  Way "many" --> "many" Clue : needs
```

A **way** is the smallest set of clues that is enough to reach a conclusion, at a precision from 1 (broad) to 4 (exact).
The planner removes clues until every way is blocked or low enough.

## Region packs

```mermaid
flowchart LR
  ENV["REGION=in,us"] --> REG["app/regions/__init__.py"]
  IN["india.py"] --> REG
  US["us.py"] --> REG
  VER["verhoeff.py<br/>Aadhaar checksum"] --> IN
  REG -->|"IDS, EXTRA, PHONE, ADDRESS"| CT["text check<br/>meta.CONTACT"]
  REG -->|"NOTE"| PR["attacker prompt"]
```

## The benchmark

```mermaid
flowchart LR
  S["scenes.json<br/>and the rendered images"] --> V1["Verifier reads the original"]
  V1 --> AG["Agent runs on the scene"]
  AG --> V2["Verifier reads the result"]
  V1 --> SC["Score: a secret counts only if<br/>it was readable before and is gone after"]
  V2 --> SC
  SC --> R["summary.md and results.json"]
  R --> UI["Results section on the page"]
```

## Build and deploy

```mermaid
flowchart LR
  DEV["Laptop"] -->|"git push main"| GH["GitHub<br/>Yasaswini-ch/snap-safe-india"]
  GH -->|"auto-deploy"| RD["Render<br/>builds the Dockerfile"]
  SEC["Secrets in Render<br/>OPEN_API_KEY, LIVE_CODE"] --> RD
  RD --> SITE["snap-safe-india.onrender.com"]
  SITE -->|"photo and prompt"| GM[("Google AI Studio")]
  DEV -.->|"python -m app.telegram_bot"| TGB["Telegram bot"]
```
