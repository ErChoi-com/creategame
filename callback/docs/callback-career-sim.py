"""
CALLBACK — end-to-end career simulation.

Wires §4.4 (casting) -> §4.7 (performance) -> §4.10 (reception) -> §4.3 (standing)
-> §11.6 (money) exactly as the design document specifies, and runs 4,000 complete
careers against the targets in §14.9.

This is the test the document never ran. It fails every target.
See callback-design-review.md section 1.

  python3 callback-career-sim.py
"""
import random, math, statistics as st
def clamp(x,a,b): return max(a,min(b,x))
def sig(x): return 1/(1+math.exp(-x))

def life(seed):
    random.seed(seed)
    A={k:clamp(random.gauss(45,16),5,95) for k in ("craft","instinct","presence","resilience")}
    G={"look":clamp(random.gauss(50,18),5,98),"voice":clamp(random.gauss(50,16),5,98),
       "physicality":clamp(random.gauss(52,16),5,98)}
    S={"heat":2.0,"prestige":3.0,"affection":2.0,"notoriety":0.0}
    age=18; credits=0; noms=0; wins=0; earn=0.0; peak_heat=0.0
    lead_years=0; active_years=0; last_work=0; floor=0.0; net=0.0
    leads_after_42=0
    while age<80:
        # --- Look ages ---
        if age>32: G["look"]=clamp(G["look"]-(0.9 if age<45 else 1.6 if age<60 else 2.2),5,98)
        sp=0.45*S["heat"]+0.30*S["affection"]+0.25*S["prestige"]
        # --- role availability by age band (the cliff) ---
        band=(1.30 if age<28 else 1.45 if age<39 else 1.05 if age<49 else 0.72 if age<61 else 0.42)
        n_off=max(0,int(round((1.2+sp/16)*band)))
        best=None
        for _ in range(n_off):
            billing=random.choices(["lead","supporting","bit"],[0.22,0.38,0.40])[0]
            diff={"lead":74,"supporting":58,"bit":36}[billing]
            fit=clamp(100-abs(random.gauss(0,16))-0.35*max(0,60-G["look"]),0,100)
            util=(0.40*(0.5*S["heat"]+0.3*S["prestige"]+0.2*S["affection"])+0.35*fit
                  +0.15*(0.6*A["craft"]+0.4*A["instinct"]))
            if random.random()<sig(0.11*(util-diff)):
                v={"lead":3,"supporting":2,"bit":1}[billing]
                if best is None or v>best[0]: best=(v,billing,fit)
        if best is None:
            age+=1
            if age-last_work>7 and age>34: break          # career quietly over
            S["heat"]*=0.80; S["affection"]*=0.93; S["prestige"]*=0.985
            floor*=0.92
            continue
        _,billing,fit=best
        active_years+=1; last_work=age; credits+=1
        if billing=="lead":
            lead_years+=1
            if age>=42: leads_after_42+=1
        bw={"lead":1.0,"supporting":0.55,"bit":0.2}[billing]
        # --- performance (4.7) ---
        cond=clamp(random.gauss(78,12),25,100); dsk=clamp(random.gauss(58,16),5,100)
        prep=clamp(random.gauss(58,18),0,100); chem=clamp(random.gauss(60,17),0,100)
        base=(0.28*A["craft"]+0.18*A["instinct"]+0.16*A["presence"]+0.16*fit
              +0.12*prep+0.10*chem+0.06*(dsk-50)*0.5)
        P=base*(0.86+0.0028*dsk)*(0.80+0.0020*cond)+random.gauss(0,16-0.09*A["craft"])
        if random.random()<A["instinct"]/320: P+=random.uniform(9,26)
        P=clamp(P,0,100)
        # --- reception (4.10) ---
        script=clamp(random.gauss(60,14),0,100)
        ens=0.80*P+0.20*clamp(random.gauss(60,14),0,100)
        PQ=0.31*script+0.22*dsk+0.29*ens+0.08*clamp(random.gauss(58,15),0,100)+0.10*random.gauss(52,14)
        FC=clamp(PQ+random.choice([4,-5,-4,-3,0,0])+random.gauss(0,5.5),0,100)
        YN=clamp(0.52*P+0.25*FC+0.13*(50+30*bw)+random.gauss(0,7),0,100)
        AUD=clamp(0.62*PQ+0.17*clamp(random.gauss(60,15),0,100)
                  +0.11*clamp(random.gauss(50,20),0,100)+0.06*(100-PQ)+random.gauss(0,5.5),0,100)
        budget=random.choice([5,12,30,30,60,160]); mkt=0.48*budget
        op=budget*(0.80+0.005*sp+0.005*60)*((budget/30.0)**-0.10)
        z=AUD+random.gauss(0,12); legs=clamp(1.7+0.048*(AUD-50)+0.032*max(0,z-70)**1.5,1.15,8.0)
        roi=(0.62*op*legs)/(budget+mkt)
        # --- standing (4.10) ---
        S["heat"]=clamp(S["heat"]+bw*(9*clamp(roi-1,-0.6,2.2)+0.16*(AUD-55)),0,100)
        S["prestige"]=clamp(S["prestige"]+bw*(0.11*(FC-60)+0.26*(YN-62)),0,100)
        S["affection"]=clamp(S["affection"]+bw*(0.10*(AUD-55)),0,100)
        peak_heat=max(peak_heat,S["heat"])
        # --- awards (4.11) ---
        if billing in ("lead","supporting"):
            buzz=0.34*YN+0.20*FC+0.12*S["prestige"]+random.gauss(0,9)
            if random.random()<clamp(sig(0.13*(buzz-72)),0,0.6):
                noms+=1
                if random.random()<0.24:
                    wins+=1; S["prestige"]=clamp(S["prestige"]+9,0,100); S["heat"]=clamp(S["heat"]+7,0,100)
        # --- money (9.6) ---
        quote=0.05*math.exp(0.052*clamp(0.60*S["heat"]+0.25*min(100,40*roi)+0.15*S["affection"],0,100))
        fee=quote*bw*random.uniform(0.7,1.3); earn+=fee
        net+=fee*0.55-floor; floor=max(floor*0.92, 0.55*fee)
        # --- craft grows from work ---
        A["craft"]=clamp(A["craft"]+random.uniform(0.5,2.0),5,99)
        A["presence"]=clamp(A["presence"]+(0.4 if age<45 else -0.5),5,99)
        # --- decay + age ---
        S["heat"]*=0.91; S["affection"]*=0.96; S["prestige"]*=0.985
        age+=1
    return dict(active=active_years,lead=lead_years,noms=noms,wins=wins,earn=earn,
                peak=peak_heat,net=net,credits=credits,leads42=leads_after_42,end=age)

R=[life(s) for s in range(4000)]
def q(k,p): return sorted(x[k] for x in R)[int(p*len(R))]
print("=== FULL CAREER SIMULATION — 4,000 careers ===\n")
print("%-46s %-14s %s"%("metric","target (14.9)","measured"))
rows=[
 ("Median career length (years active)","26",         "%.0f"%st.median([x["active"] for x in R])),
 ("Careers reaching Heat > 80","~18%",                "%.0f%%"%(100*sum(1 for x in R if x["peak"]>80)/len(R))),
 ("Careers with zero nominations","~55%",             "%.0f%%"%(100*sum(1 for x in R if x["noms"]==0)/len(R))),
 ("Award wins per 100 careers","21",                  "%.0f"%(100*sum(x["wins"] for x in R)/len(R))),
 ("Median lifetime earnings","$6-11M",                "$%.1fM"%st.median([x["earn"] for x in R])),
 ("Top-decile lifetime earnings","$90M+",             "$%.0fM"%q("earn",0.90)),
 ("Careers with a lead role after 42","~30%",         "%.0f%%"%(100*sum(1 for x in R if x["leads42"]>0)/len(R))),
]
for a,b,c in rows: print("%-46s %-14s %s"%(a,b,c))
print("\nextra shape:")
print("  median credits %.0f | p90 credits %d | median end-age %.0f"%(
    st.median([x["credits"] for x in R]),q("credits",0.9),st.median([x["end"] for x in R])))
print("  careers with 0 credits (never got started): %.0f%%"%(100*sum(1 for x in R if x["credits"]==0)/len(R)))
print("  median lead years %.0f | %.0f%% never played a lead"%(
    st.median([x["lead"] for x in R]),100*sum(1 for x in R if x["lead"]==0)/len(R)))
