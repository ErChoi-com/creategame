"""
CALLBACK — simulation harness (v8)
Verifies every tuned constant in the design document.

  python3 callback-sim.py reception  # 4.10  reception-model correlations
  python3 callback-sim.py palette    # 5.3-5.7 film palette, coherence, actor positions
  python3 callback-sim.py leverage   # 6.4-6.5 indispensability + the holdout
  python3 callback-sim.py director   # 7.4   development pipeline
  python3 callback-sim.py studio     # 8.2   per-tier ROI + slate outcomes
  python3 callback-sim.py genre      # 9.3   genre boom/bust cycles
  python3 callback-sim.py budget     # 0.2   decision-load audit
  python3 callback-sim.py all
"""
import sys, random, math, statistics as st
def clamp(x, a, b): return max(a, min(b, x))


def reception():
    print("=== 4.10 RECEPTION MODEL ===")
    def corr(x,y):
        mx,my=st.mean(x),st.mean(y)
        n=sum((a-mx)*(b-my) for a,b in zip(x,y))
        d=math.sqrt(sum((a-mx)**2 for a in x)*sum((b-my)**2 for b in y))
        return n/d

    def run(seed=3, N=40000, p=None):
        random.seed(seed)
        P_,FC_,YN_,A_,ROI_=[],[],[],[],[]
        for _ in range(N):
            craft=clamp(random.gauss(65,15),5,100); inst=clamp(random.gauss(55,18),5,100)
            pres=clamp(random.gauss(60,15),5,100)
            fit=clamp(random.gauss(70,18),0,100); prep=clamp(random.gauss(60,20),0,100)
            chem=clamp(random.gauss(60,18),0,100)
            dsk=clamp(random.gauss(58,16),5,100); dpr=clamp(random.gauss(50,20),0,100)
            cond=clamp(random.gauss(78,14),20,100)
            base=0.28*craft+0.18*inst+0.16*pres+0.16*fit+0.12*prep+0.10*chem
            P=base*(0.86+0.0028*dsk)*(0.80+0.0020*cond)+random.gauss(0,16-0.09*craft)
            if random.random()<inst/320: P+=random.uniform(9,26)
            P=clamp(P,0,100); bw=1.0
            script=clamp(random.gauss(60,14),0,100)
            ens=0.80*P+0.20*clamp(random.gauss(60,14),0,100)
            prod=clamp(random.gauss(58,15),0,100); post=random.gauss(52,14)
            PQ=(0.60-p['pens'])*script+0.22*dsk+p['pens']*ens+0.08*prod+0.10*post
            gb=random.choice([4,-5,-4,-3,0,0])
            FC=clamp(PQ+gb+0.10*(dpr-50)+random.gauss(0,p['fcn']),0,100)
            YN=clamp(p['pyn']*P+0.25*FC+0.13*(50+30*bw)+random.gauss(0,7),0,100)
            dem=clamp(random.gauss(60,15),0,100); csp=clamp(random.gauss(50,20),0,100)
            A=clamp(p['apq']*PQ+p['adem']*dem+p['acsp']*csp+p['aelit']*(100-PQ)+random.gauss(0,p['an']),0,100)
            budget=random.choice([5,15,25,40,90,160]); mkt=0.45*budget
            opening=budget*(p['ob']+0.004*csp+0.005*dem)
            legs=clamp(1.7+p['legs']*(A-50),1.15,4.4)
            roi=(0.62*opening*legs)/(budget+mkt)
            P_.append(P);FC_.append(FC);YN_.append(YN);A_.append(A);ROI_.append(roi)
        return dict(
          Pm=st.mean(P_),Psd=st.pstdev(P_),FCm=st.mean(FC_),FCsd=st.pstdev(FC_),
          YNm=st.mean(YN_),Am=st.mean(A_),Asd=st.pstdev(A_),
          roimed=st.median(ROI_),prof=100*sum(1 for r in ROI_ if r>1)/len(ROI_),
          c_p_yn=corr(P_,YN_),c_p_fc=corr(P_,FC_),c_p_roi=corr(P_,ROI_),
          c_fc_roi=corr(FC_,ROI_),c_fc_a=corr(FC_,A_))



    p=dict(pens=0.29,pyn=0.52,fcn=5.5,apq=0.62,adem=0.17,acsp=0.11,aelit=0.06,an=5.5,ob=0.68,legs=0.048)
    r=run(seed=3,N=40000,p=p)



    print("Perf mean %.1f sd %.1f | FilmCritic %.1f/%.1f | Notices %.1f | Aud %.1f/%.1f"
          %(r['Pm'],r['Psd'],r['FCm'],r['FCsd'],r['YNm'],r['Am'],r['Asd']))
    print("ROI median %.2f  profitable %.0f%%"%(r['roimed'],r['prof']))
    print()
    for k,label,tgt in [('c_p_yn','corr(Perf, YourNotices)','0.70-0.80'),
                        ('c_p_fc','corr(Perf, FilmCritic) ','0.40-0.48'),
                        ('c_p_roi','corr(Perf, ROI)        ','0.20-0.30'),
                        ('c_fc_roi','corr(FilmCritic, ROI)  ','0.20-0.30'),
                        ('c_fc_a','corr(FilmCritic, Aud)  ','0.40-0.50')]:
        lo,hi=[float(x) for x in tgt.split('-')]
        ok='OK ' if lo<=r[k]<=hi else '<<<'
        print("%s %s = %.2f   target %s  %s"%(ok,label,r[k],tgt,''))


def palette():
    """Part 5.3-5.7 — the film palette, coherence, landmarks, performance contrast"""
    print("\n=== 5.3-5.7 PALETTE, COHERENCE, PERFORMANCE ===")
    random.seed(4)
    DIALS = 6
    W = {  #            pace col scale int clar text
      "action": {"a": [5, 4, 4, 4, 4, 4], "c": [-2, -1, 0, 3, -4, 3]},
      "horror": {"a": [2, 1, 1, -3, 1, 2], "c": [1, 2, 0, -4, -5, 3]},
      "comedy": {"a": [6, 3, 1, 0, 4, 2], "c": [3, 0, -1, -2, -3, 1]},
      "drama":  {"a": [3, 2, 2, 2, 6, 2], "c": [-3, -1, -1, 3, -6, 3]},
      "scifi":  {"a": [4, 4, 5, 3, 4, 3], "c": [-1, 1, 2, 0, -4, 2]},
    }
    def eff(p, g):
        w = W[g]
        return (sum(x*v/100 for x, v in zip(w["a"], p)),
                sum(x*v/100 for x, v in zip(w["c"], p)))
    def cr(X, Y):
        mx, my = st.mean(X), st.mean(Y)
        return (sum((a-mx)*(b-my) for a, b in zip(X, Y))
                / math.sqrt(sum((a-mx)**2 for a in X) * sum((b-my)**2 for b in Y)))

    print("  IS IT ONE AXIS?  (it must not be)")
    print("  %-8s %-18s %s" % ("genre", "corr(aud, crit)", "aud effect range"))
    for g in W:
        P = [[random.uniform(-50, 50) for _ in range(DIALS)] for _ in range(8000)]
        A = [eff(p, g)[0] for p in P]; C = [eff(p, g)[1] for p in P]
        print("  %-8s %-18.2f %+.0f..%+.0f" % (g, cr(A, C), min(A), max(A)))
    print("  [target: spread from about -0.7 to +0.6, with 2+ genres near zero]")

    ARCH = {"blockbuster": [40,35,45,30,40,40], "art film": [-40,-25,-35,-10,-45,-35],
            "horror": [10,-20,-25,20,-25,5], "chamber": [-25,0,-45,-25,5,-30],
            "epic": [-10,25,50,15,20,0], "verite": [-15,-35,-30,-5,-20,25],
            "neon": [25,50,10,10,-10,30]}
    def coh(p):
        d = min(math.sqrt(sum((a-b)**2 for a, b in zip(p, v)))/math.sqrt(6) for v in ARCH.values())
        return clamp(100 - 2.2*d, 0, 100)
    S = [coh([random.uniform(-50, 50) for _ in range(DIALS)]) for _ in range(20000)]
    print("\n  COHERENCE: random palettes mean %.0f, %.0f%% below 30   [targets 35-50, 10-25%%]"
          % (st.mean(S), 100*sum(1 for x in S if x < 30)/len(S)))
    odd = [-45, 40, 48, -30, 45, -40]
    print("  languid+saturated+epic+ambiguous -> coherence %.0f, variance x%.2f"
          % (coh(odd), 1 + 0.014*(100 - coh(odd))))

    print("\n  LANDMARK  P = clamp(0.02 + 0.00022*(60-coh)*(skill-70), 0, 0.20)")
    print("  %-11s %-9s %-9s %s" % ("coherence", "skill 72", "skill 85", "skill 95"))
    for c in (55, 45, 35, 25):
        r = [clamp(0.02 + 0.00022*(60-c)*(sk-70), 0, 0.20) if c < 60 and sk > 70 else 0
             for sk in (72, 85, 95)]
        print("  %-11d %-9s %-9s %s" % (c, *["%.0f%%" % (100*x) for x in r]))

    # --- actor: named positions, contrast budget, no solvable optimum ---
    import itertools
    DL = ["energy", "volume", "warmth", "speed"]; REL = ["with", "beneath", "beyond", "against"]
    COST = {"with": 0, "beneath": 1, "beyond": 2, "against": 3}
    SPIKY = {"with": 0.0, "beneath": 0.15, "beyond": 0.85, "against": 1.0}
    READ = {
      "energy": {"with": (0.5,1.5), "beneath": (2.5,1.0), "beyond": (1.0,-0.5), "against": (4.5,0.5)},
      "volume": {"with": (0.5,1.5), "beneath": (3.0,1.5), "beyond": (0.5,-1.5), "against": (3.5,0.0)},
      "warmth": {"with": (0.5,1.5), "beneath": (1.5,0.5), "beyond": (2.0,0.5), "against": (4.0,-0.5)},
      "speed":  {"with": (0.5,1.5), "beneath": (2.0,1.0), "beyond": (2.5,0.0), "against": (3.0,0.5)}}
    GB = {"drama":  {"energy":1.3,"volume":1.4,"warmth":1.1,"speed":0.8},
          "action": {"energy":0.7,"volume":0.8,"warmth":1.2,"speed":1.3},
          "comedy": {"energy":1.0,"volume":0.9,"warmth":1.2,"speed":1.6},
          "horror": {"energy":1.5,"volume":1.3,"warmth":1.0,"speed":0.7}}

    def resolve(combo, genre, presence, base=62):
        sp = st.mean(SPIKY[r] for r in combo); L = 9*sp
        b = [base - 0.65*L, base + 1.30*L, base - 0.65*L]
        n = sum(READ[d][r][0]*GB[genre][d] for d, r in zip(DL, combo))
        e = sum(READ[d][r][1] for d, r in zip(DL, combo))
        return 0.55*max(b) + 0.45*st.mean(b) + 0.10*presence + n, st.mean(b) - 4.0*sp + e

    print("\n  CONTRAST BUDGET = (Craft + DirectorCommand) / 28")
    for c, d, nm in ((45,45,"limited, no support"), (75,45,"skilled, neutral dir"),
                     (75,80,"skilled, dir with them"), (90,85,"great, dir with them")):
        b = (c+d)/28.0
        aff = ("1 against" if b < 4 else "1 against + 1 beneath" if b < 5
               else "1 against + 1 beyond" if b < 6 else "2 against")
        print("    %-24s budget %.1f  -> %s" % (nm, b, aff))

    print("\n  SHAPE — Notices reads the peak, Ensemble reads the mean")
    print("    %-26s %-9s %s" % ("allocation", "Notices", "Ensemble"))
    for nm, c in [("all with", ("with",)*4), ("two beneath (steady)", ("beneath","beneath","with","with")),
                  ("one against (shaped)", ("against","beneath","with","with")),
                  ("against+beyond (showy)", ("against","beyond","with","with"))]:
        n, e = resolve(c, "drama", 60)
        print("    %-26s %-9.1f %.1f" % (nm, n, e))
    print("    [shaped must beat showy on Notices, or showiness dominates]")

    print("\n  DOMINANCE TEST — is there one best allocation? (there must not be)")
    seen = {}
    for genre in GB:
        for craft, cmd, pres in ((45,45,40), (75,45,60), (75,80,60), (55,50,88)):
            B = (craft+cmd)/28.0; best = None
            for combo in itertools.product(REL, repeat=4):
                if sum(COST[r] for r in combo) > B: continue
                n, _ = resolve(combo, genre, pres)
                if best is None or n > best[0]: best = (n, combo)
            seen[best[1]] = seen.get(best[1], 0) + 1
    print("    distinct winners: %d / 16 build-genre pairs   [target >=6]" % len(seen))
    print("    most common wins %d/16 (%.0f%%)   [target <=50%%]"
          % (max(seen.values()), 100*max(seen.values())/16))


def leverage():
    """Part 6.4-6.5 — indispensability curve and the holdout gamble"""
    print("\n=== 6.4 INDISPENSABILITY / 6.5 THE HOLDOUT ===")
    def sig(x): return 1 / (1 + math.exp(-x))

    def indisp(cid, inst, sp_ratio, hold):
        return clamp(0.35*cid + 0.25*min(100, 22*inst)
                     + 0.20*clamp(50*sp_ratio, 0, 100) + 0.20*hold, 0, 100)

    print("  %-5s %-8s %-8s %-11s %s" % ("inst", "charID", "indisp", "recastCost", "studio view"))
    for n in range(1, 7):
        cid = clamp(18 + 15*(n-1), 0, 100)
        I = indisp(cid, n, 1.15, min(70, 8 + 12*n)); rc = 0.55*I
        v = ("recasts freely" if rc < 15 else "reluctant" if rc < 24 else
             "expensive" if rc < 34 else "unthinkable")
        print("  %-5d %-8.0f %-8.0f %-11.1f %s" % (n, cid, I, rc, v))

    print("\n  HOLDOUT (payoff in units of remaining franchise income)")
    print("  %-7s %-7s %-7s %-8s %-6s %-6s %s" % ("indisp","P(pay)","P(out)","P(delay)","raise","EV","play"))
    be = None
    for I in range(20, 101, 10):
        p = 0.85 * sig(0.085 * (I - 58))
        rest = 1 - p; po, pd = rest*0.65, rest*0.35
        mult = clamp(1.35 + 0.013*(I - 50), 1.35, 2.40)
        ev = p*mult + po*0.10 + pd*0.92
        if ev > 1.0 and be is None: be = I
        print("  %-7d %-7.2f %-7.2f %-8.2f %-6.2f %-6.2f %s" % (
            I, p, po, pd, mult, ev, "HOLD OUT" if ev > 1.0 else "sign"))
    print("  break-even Indispensability = %s   [target 65-75]" % be)
    print("  P(losing the role) at 90 = %.0f%%   [target >=10%%, never free money]"
          % (100 * (1 - 0.85*sig(0.085*32)) * 0.65))


def director():
    """Part 7.4 — tuned: base 0.16, momentum decay 0.96"""
    print("\n=== 7.4 DIRECTOR PIPELINE ===")
    BASE, DECAY = 0.16, 0.96
    def sig(x): return 1 / (1 + math.exp(-x))
    def difficulty(b): return 30 + 22 * math.log10(b + 1)

    def career(standing0, star_access, years=30):
        standing, films, dead, devlens, slots, busy = standing0, [], 0, [], [], 0
        for q in range(years * 4):
            while len(slots) < 3:
                budget = random.choice([4,12,30,30,60,170]) if standing > 55 else random.choice([4,4,12,12,30])
                slots.append([1.0, clamp(random.gauss(60 + 0.12*standing, 14), 0, 100), budget, 0])
            if busy > 0:
                busy -= 1
            else:
                for s in slots: s[3] += 1
                for i, s in enumerate(list(slots)):
                    mom, script, budget, age = s
                    sb = clamp(random.gauss(20 + 0.75*standing, 18), 0, 100) if random.random() < star_access else 15
                    pkg = 0.40*sb + 0.30*script + 0.30*standing
                    if random.random() < BASE * sig(0.10*(pkg - difficulty(budget))) * mom:
                        films.append(budget); devlens.append(age/4.0)
                        busy = {4:1, 12:2, 30:3, 60:4, 170:6}[budget]
                        slots.pop(i); standing = clamp(standing + random.gauss(6, 9), 0, 100); break
                    s[0] *= DECAY
                    if s[0] < 0.22: slots.pop(i); dead += 1; break
            standing = clamp(standing - 0.45, 0, 100)
        return len(films), (st.median(devlens) if devlens else None), dead

    print("  %-26s %-24s %-14s %s" % ("profile", "films/30yr", "med dev", "died in dev"))
    for lbl, s0, acc in [("newcomer (standing 18)", 18, 0.15),
                         ("working  (standing 45)", 45, 0.45),
                         ("A-list   (standing 75)", 75, 0.85)]:
        random.seed(4); n = 1200
        F, D, X = [], [], []
        for _ in range(n):
            f, d, x = career(s0, acc); F.append(f); X.append(x)
            if d: D.append(d)
        print("  %-26s med %2.0f (p10 %d p90 %2d)     %.1f yr         %.0f" % (
            lbl, st.median(F), sorted(F)[n//10], sorted(F)[9*n//10],
            st.median(D) if D else 0, st.median(X)))


def studio():
    """Part 8.2 — tuned: openingBase 0.80, scaleExp -0.10, tentpoleMktg 0.80, breakout 0.032"""
    print("\n=== 8.2 STUDIO ECONOMICS ===")
    random.seed(9)
    TIERS = {'micro': 4, 'lowbudget': 12, 'mid': 30, 'upper': 60, 'tentpole': 170}
    OB, SC, MT, BZ = 0.80, -0.10, 0.80, 0.032

    def mk(b):
        if b < 10: return 0.35 * b
        if b < 50: return 0.48 * b
        if b < 100: return 0.55 * b
        return MT * b

    def resolve(budget):
        csp = clamp(random.gauss(min(85, 35 + 0.19 * budget), 16), 0, 100)
        dem = clamp(random.gauss(min(78, 52 + 0.10 * budget), 13), 0, 100)
        script = clamp(random.gauss(62 - 0.020 * budget, 14), 0, 100)
        dsk = clamp(random.gauss(58, 16), 5, 100)
        perf = clamp(random.gauss(63.6, 14.6), 0, 100)
        ens = 0.80 * perf + 0.20 * clamp(random.gauss(60, 14), 0, 100)
        prod = clamp(random.gauss(40 + 22 * math.log10(budget + 1), 12), 0, 100)
        PQ = 0.31*script + 0.22*dsk + 0.29*ens + 0.08*prod + 0.10*random.gauss(52, 14)
        A = clamp(0.62*PQ + 0.17*dem + 0.11*csp + 0.06*(100-PQ) + random.gauss(0, 5.5), 0, 100)
        z = A + 0.5 * (dem - 50) + random.gauss(0, 12)
        op = budget * (OB + 0.004*csp + 0.005*dem) * ((budget / 30.0) ** SC)
        legs = clamp(1.7 + 0.048*(A-50) + BZ*max(0, z-70)**1.5, 1.15, 8.0)
        g, m = op * legs, mk(budget)
        return (0.62*g) / (budget+m), 0.62*g - (budget+m)

    print("%-11s %7s %7s %7s %8s" % ("tier", "budget", "medROI", "%prof", "P(>2x)"))
    for n, b in TIERS.items():
        roi = [resolve(b)[0] for _ in range(15000)]
        print("%-11s %7.0f %7.2f %6.0f%% %7.1f%%" % (n, b, st.median(roi),
              100*sum(1 for x in roi if x > 1)/len(roi),
              100*sum(1 for x in roi if x > 2)/len(roi)))
    print("  (micro is pre-distribution-gate; see 9.3 — ~30% never sell, ~56% effective)")
    print("\n  SLATES (4000 studio-years)")
    for lbl, mix in [("balanced (1 tent,2 upper,3 mid,4 low)", {'tentpole':1,'upper':2,'mid':3,'lowbudget':4}),
                     ("blockbuster (3 tent,4 upper,3 mid)", {'tentpole':3,'upper':4,'mid':3}),
                     ("indie (2 mid,4 low,4 micro)", {'mid':2,'lowbudget':4,'micro':4})]:
        ys = [sum(resolve(TIERS[k])[1] for k, v in mix.items() for _ in range(v)) for _ in range(4000)]
        cap = sum(TIERS[k]*v for k, v in mix.items())
        print("  %-38s med $%5.0fM  P(profit) %2.0f%%  p10 $%6.0fM  p90 $%5.0fM  cap $%4.0fM" % (
            lbl, st.median(ys), 100*sum(1 for y in ys if y > 0)/len(ys),
            sorted(ys)[400], sorted(ys)[3600], cap))


def genre():
    """Part 9.3 — tuned: heatGain 30, decay 0.88, saturation 2.0, recovery 0.045,
       greenlightResponse 1.2, releaseLag 8 quarters"""
    print("\n=== 9.3 GENRE CYCLES ===")
    HG, HD, DU, SAT, REC, BASE, BG, GK, LAG = 30, 0.88, 0.30, 2.0, 0.045, 58.0, 1.0, 1.2, 8

    def history(years, seed):
        random.seed(seed)
        heat, dem, pipe, out = 0.0, BASE, [BG] * (LAG + 1), []
        for q in range(years * 4):
            pipe.append(BG + GK * (heat / 25.0)); rel = pipe.pop(0)
            hits = 0
            for _ in range(int(round(rel))):
                A = clamp(random.gauss(50 + 0.40 * (dem - BASE), 9), 0, 100)
                if 0.95 * math.exp(0.020 * (A - 50) + random.gauss(0, 0.50)) > 2.5:
                    hits += 1
            heat = heat * HD + HG * hits
            dem += DU * heat / 4 - SAT * (rel - BG) + REC * (BASE - dem)
            dem = clamp(dem, 15, 95); out.append(dem)
        return out

    booms, busts, sds, share = [], [], [], []
    for s in range(400):
        d = history(60, s)
        yr = [st.mean(d[i*4:(i+1)*4]) for i in range(60)]
        booms.append(sum(1 for v in yr if v > 70))
        busts.append(sum(1 for v in yr if v < 48))
        sds.append(st.pstdev(d)); share.append(sum(1 for v in yr if v > 70) / 60)
    print("  400 genre-histories x 60 years:")
    print("    time in boom (demand>70)  %.0f%%       [target 4-8%%]" % (100 * st.mean(share)))
    print("    boom years per 60         %.0f" % st.median(booms))
    print("    bust years per 60         %.0f        [target 10-20]" % st.median(busts))
    print("    demand sd                 %.1f      [target 8-12]" % st.mean(sds))
    print("    genres booming at once    %.1f of 11 [target <1]" % (11 * st.mean(share)))
    print("\n  Sample traces (1 char = 1 year):")
    bars = " .:-=+*#%@"
    for s in (3, 11, 27):
        yr = [st.mean(history(60, s)[i*4:(i+1)*4]) for i in range(60)]
        print("    " + "".join(bars[min(9, max(0, int((v - 15) / 8)))] for v in yr))


def budget():
    """Part 0.2 — decision load per in-game year, v3 vs v4"""
    print("\n=== 0.2 DECISION BUDGET ===")
    rows = [("accept / decline offers", 3, 3), ("deal terms", 9, 1), ("palette / prep", 9, 2),
            ("on-set events", 12, 4), ("fame maintenance", 4, 0), ("rolodex upkeep", 4, 1),
            ("dev slate (if directing)", 12, 3), ("thematic intent (dir)", 0, 1),
            ("the edit (dir)", 0, 2), ("season / campaign", 2, 2)]
    print("  %-34s %7s %7s" % ("", "v3/yr", "v8/yr"))
    for k, a, b in rows: print("  %-34s %7d %7d" % (k, a, b))
    A, B = sum(r[1] for r in rows), sum(r[2] for r in rows)
    print("  %-34s %7d %7d" % ("TOTAL per year", A, B))
    print("  %-34s %7d %7d" % ("over a 40-year career", A * 40, B * 40))
    DIR = 3 + 1 + 2   # dev slate + thematic intent + the edit
    print("  actor-only: %d/yr, %d per career   [target <=15/yr]" % (B - DIR, (B - DIR) * 40))
    print("  reduction: %.0f%%" % (100 * (1 - B / A)))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name in ("reception","palette","leverage","director","studio","genre","budget"):
        if a in (name, "all"): globals()[name]()
