# PART 1 — HOW BITLIFE'S ACTOR PACK ACTUALLY WORKS

## 1.1 Access and framing

The acting career is not part of the base BitLife loop. It sits behind a paywall as a **Special Career**, sold either as the standalone **Actor Pack** or inside the **Jobs Pack** bundle (originally gated behind Boss Mode / legacy Bitizen). It shipped as the **Movie Star Update** on **March 10, 2022**.

Structurally it's an *overlay* on the standard BitLife life loop: you still age one year per tap, you still have Happiness / Health / Smarts / Looks, and the acting content is a new menu branch under `Occupation → Special Careers → Actor` plus a **Fame** panel that appears once you land your first credited role.

## 1.2 The prerequisite phase (ages 0–18)

Before you can meaningfully audition, the game asks you to farm two numbers:

| Input | How it's raised | Notes |
|---|---|---|
| **Looks** | Born value, then walks, healthy eating, gym, spa, plastic surgery | Community consensus: you want **80+**. This is the hardest gate for a random-start character. |
| **Acting skill** | *Acting Lessons* under `Activities → Mind & Body`, from **age 8**; parents pay until 18, then ~**$3,000/session** | Practice **~4×/year**; target **90%+** before serious auditions. |
| **Acting special talent** | Character-creation option, requires God Mode | Starts you with a large innate bonus. |
| **Drama club** | School extracurricular | Small contribution, mostly flavor. |

That's the whole preparation model: two sliders, both raised by repeating one button.

## 1.3 The casting layer

After high school you unlock the Actor special career. The casting screen is a **list of job postings** — a rolling set of open roles, each with a short description stating the production, the medium, the genre, and the character being cast.

**Role tiers** (ascending):

1. **Extra** — uncredited, no lines, a few hundred dollars, no skill requirement. The intended on-ramp.
2. **Bit part** — small credited role.
3. **Supporting role**
4. **Lead role**
5. **TV recurring role** — paid *per episode*, renews across seasons, the reliable-income option.

**Mediums and genres:** television (crime, drama, action, sitcom) and film (comedy, drama, thriller, horror), plus regional flavors added at launch — **Bollywood films** and **telenovelas**.

**Two-stage RNG.** Applying does not get you an audition; landing an audition does not get you the part. Guides describe this explicitly as "another layer of luck." The role description carries soft requirements — most importantly **age fit** (a 25-year-old auditioning for a 57-year-old character is near-hopeless) and appearance — and your acting skill weights the roll.

**Talent agent.** Hireable for roughly **$1,500** (some guides cite ~$20,000 for a good one). The agent surfaces better roles and **negotiates pay**; their **commission percentage** is shown on their profile. This is the one genuinely interesting economic decision in the pack.

**Pay display.** TV contracts show **per-episode** compensation; film contracts show a **flat fee**.

## 1.4 The on-set layer

Once cast, each year of the role gives you a menu of actions:

- **Practice / rehearse lines**
- **Develop your character**
- **Co-star interactions** — befriend, compliment, gift, rehearse with, date, hook up. Some co-stars are written as conceited and will rebuff you.
- **On-set situations** — scripted events you resolve by choice. Some are director requests, including illicit ones (drugs), which move **reputation** hard.
- **Perform stunts**
- **Eat exotic foods** (flavor event)
- **Publicity stunts** to promote the project

## 1.5 The output layer

- **Fame** — a percentage stat that unlocks on your first role. Maintained by social-media posting, commercials, photo shoots and talk shows (the latter two gate at ~50% fame), and book writing. It **decays if neglected**. The influencer path tags you as famous around **300,000 followers**.
- **Reputation** — a parallel stat, separate from fame. Bad on-set behavior tanks it; awards raise it. Gates access to better roles.
- **Bitcademy Awards** — Best Picture / Best TV Show and Best Actor / Best Actress (plus supporting categories). **Best Actor is reserved for leading roles.** Nominations follow from several completed projects with good performance, critical reception, and box-office success. Winning gives a large fame + reputation boost and an acceptance-speech beat.
- **Achievements** — a set of acting-specific unlockables.

## 1.6 The loop, compressed

```
raise Looks + Acting skill  →  scroll a job list  →  RNG audition  →
tap 3-5 on-set buttons  →  age up  →  Fame/Reputation tick  →  maybe an award
```

---

