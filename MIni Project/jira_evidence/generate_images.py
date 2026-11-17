import json, datetime as dt, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.dates as md
IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
def d(s): return dt.datetime.fromisoformat(s).astimezone(IST)
# key, summary, pts, owner, sprints, done-at
I=[("RLRS-1","Project skeleton, database setup and CI",3,"Mahipal Singh","1,2","2026-11-05T14:40:41+05:30"),
("RLRS-2","User sign-in/sign-out with role-based access",5,"Deepesh M","1,2","2026-11-11T11:11:04+05:30"),
("RLRS-3","Lab and equipment management",5,"Deepesh M","1,2","2026-11-11T11:18:15+05:30"),
("RLRS-4","Scheduling engine: conflict detection",8,"Lakshya Budhauliya","1,2","2026-11-11T10:59:25+05:30"),
("RLRS-5","Scheduling engine: booking rules validation",5,"Lakshya Budhauliya","1,2","2026-11-11T11:00:09+05:30"),
("RLRS-6","Create reservation API, concurrency-safe",5,"Lakshya Budhauliya","2","2026-11-11T11:00:40+05:30"),
("RLRS-7","Availability calendar UI (day and week views)",8,"Deepesh M","2","2026-11-11T11:19:27+05:30"),
("RLRS-8","Booking form, My Reservations, cancellation",5,"Deepesh M","2","2026-11-11T11:20:12+05:30"),
("RLRS-9","Confirmation and cancellation emails",3,"Deepesh M","2","2026-11-11T11:20:47+05:30"),
("RLRS-10","Reminder emails: background worker and retry",8,"Mahipal Singh","2","2026-11-05T14:40:45+05:30"),
("RLRS-11","Approval workflow for restricted equipment",3,"Lakshya Budhauliya","2","2026-11-11T11:01:12+05:30"),
("RLRS-12","Maintenance blocks, auto-cancel and notify",5,"Mahipal Singh","2","2026-11-05T14:40:46+05:30"),
("RLRS-13","Attendance marking and audit log",3,"Mahipal Singh","2","2026-11-05T14:40:48+05:30"),
("RLRS-14","Utilisation and no-show report",3,"Mahipal Singh","2","2026-11-05T14:40:49+05:30"),
("RLRS-15","Integration testing, evidence, doc alignment",5,"Mahipal Singh","2","2026-11-11T11:21:25+05:30")]
I=[(k,s,p,o,sp,d(t)) for k,s,p,o,sp,t in I]
NAVY="#0B3C49"; TEAL="#1C6E7D"; AMB="#F2A541"; GREY="#8A9BA0"
def table(title,sub,rows,cols,widths,fn):
    h=0.45*len(rows)+1.9
    fig=plt.figure(figsize=(13,h)); ax=fig.add_axes([0,0,1,1]); ax.axis("off")
    ax.text(.02,1-.5/h,title,fontsize=17,weight="bold",color=NAVY,va="top",transform=ax.transAxes)
    ax.text(.02,1-.95/h,sub.replace("  ","\n"),fontsize=10,color=GREY,va="top",transform=ax.transAxes)
    t=ax.table(cellText=rows,colLabels=cols,colWidths=widths,loc="center",cellLoc="left",bbox=[.02,.02,.96,1-1.85/h])
    t.auto_set_font_size(False); t.set_fontsize(10.5)
    for (r,c),cell in t.get_celld().items():
        cell.set_edgecolor("#D5DEE0")
        if r==0: cell.set_facecolor(NAVY); cell.get_text().set_color("white"); cell.get_text().set_weight("bold")
        else: cell.set_facecolor("#F4F7F8" if r%2 else "white")
    fig.savefig(fn,dpi=150); plt.close(fig)
SRC="Source: Jira project RLRS (board 36), read via Jira API on 17 Nov 2026 (IST). Rendered from live data, not a browser screenshot."
cols=["Key","Summary","Pts","Assignee","Status"]
rows=[[k,s,p,o,"Done"] for k,s,p,o,sp,t in I]+[[k,s,"-","Mahipal Singh" if k!="RLRS-19" else "Unassigned","Done"] for k,s in [("RLRS-16","Sprint 1: SRS v1.0 drafted and uploaded"),("RLRS-17","Sprint 1: SAD v1.0 drafted and uploaded"),("RLRS-18","Sprint 1: Software Test Plan v1.0 uploaded"),("RLRS-19","Sprint 1: core logic, 37 unit tests, UML, handoff")]]
table("Product Backlog (RLRS)",SRC+"  15 stories = 74 story points; RLRS-16..19 are unpointed Sprint 1 task records.",rows,cols,[.09,.52,.06,.19,.14],"02_product_backlog.png")
s1=[[k,s,p,o,"Carried over (not Done at sprint close)"] for k,s,p,o,sp,t in I if "1" in sp.split(",")]
table("Sprint 1 - Foundation (27-31 Oct 2026, CLOSED)",SRC+"  Committed 26 pts; 0 pts completed when closed on 31 Oct; all 5 stories carried into Sprint 2.",s1,["Key","Summary","Pts","Assignee","Outcome at sprint close"],[.09,.41,.06,.17,.27],"03_sprint1_backlog.png")
s2=[[k,s,p,o,"Done "+t.strftime("%d %b")] for k,s,p,o,sp,t in I if "2" in sp.split(",")]
table("Sprint 2 - Build and Test (2-7 Nov 2026)",SRC+"  Scope 74 pts (includes 26 pts carried over). Sprint was never formally closed in Jira (state: active).",s2,["Key","Summary","Pts","Assignee","Completed"],[.09,.46,.06,.19,.2],"04_sprint2_backlog.png")
# burndown
def burn(name,scope,start,end,items,fn,xmax=None):
    fig,ax=plt.subplots(figsize=(11,5.2))
    ax.plot([start,end],[scope,0],"--",color=GREY,label="Ideal")
    ev=sorted(items,key=lambda x:x[1]); xs=[start]; ys=[scope]; r=scope
    for p,t in ev:
        xs+=[t,t]; ys+=[r,r-p]; r-=p
    last=xmax or max(end,xs[-1]); xs.append(last); ys.append(r)
    ax.step(xs,ys,where="post",color=TEAL,lw=2.5,label="Remaining (actual)")
    ax.axvline(end,color=AMB,lw=2,label="Sprint end"); ax.set_ylim(0,scope*1.1)
    ax.set_ylabel("Story points remaining"); ax.xaxis.set_major_formatter(md.DateFormatter("%d %b")); ax.legend(loc="upper right")
    ax.set_title(name,color=NAVY,weight="bold",loc="left"); ax.grid(alpha=.3)
    fig.text(.01,.01,SRC,fontsize=8,color=GREY); fig.tight_layout(rect=[0,.03,1,1]); fig.savefig(fn,dpi=150); plt.close(fig)
s1s,s1e=dt.datetime(2026,10,27,9,0,tzinfo=IST),dt.datetime(2026,10,31,23,0,tzinfo=IST)
burn("Burndown - Sprint 1 - Foundation (26 pts committed, 0 completed)",26,s1s,s1e,[],"05_burndown_sprint1.png")
s2s,s2e=dt.datetime(2026,11,2,1,47,tzinfo=IST),dt.datetime(2026,11,7,23,0,tzinfo=IST)
burn("Burndown - Sprint 2 - Build and Test (74 pts scope)",74,s2s,s2e,[(p,t) for k,s,p,o,sp,t in I],"06_burndown_sprint2.png",xmax=dt.datetime(2026,11,12,tzinfo=IST))
# progress
fig,ax=plt.subplots(figsize=(10,4.5))
lab=["Sprint 1\n(26 pts)","Sprint 2\n(74 pts)"]
ax.barh(lab,[0,74],color=TEAL,label="Done"); ax.barh(lab,[26,0],left=[0,74],color="#C9D6D9",label="Not done at close")
ax.barh(["Sprint 2\n(74 pts)"],[22],color=AMB,label="Done by sprint end (5 Nov): 22 pts") if False else None
ax.text(13,0,"0 done / 26",ha="center",va="center"); ax.text(37,1,"74 / 74 Done (22 pts by 5 Nov, 52 pts on 11 Nov)",ha="center",va="center",color="white",weight="bold")
ax.set_xlim(0,80); ax.set_xlabel("Story points"); ax.legend(loc="lower right"); ax.set_title("Sprint progress",color=NAVY,weight="bold",loc="left")
fig.text(.01,.01,SRC,fontsize=8,color=GREY); fig.tight_layout(rect=[0,.04,1,1]); fig.savefig("07_sprint_progress.png",dpi=150); plt.close(fig)
# dashboard
fig,axs=plt.subplots(1,3,figsize=(13,4.8))
axs[0].pie([19,0],labels=None,colors=[TEAL,"#C9D6D9"],startangle=90,wedgeprops=dict(width=.4)); axs[0].text(0,0,"19/19\nDone",ha="center",va="center",fontsize=16,weight="bold",color=NAVY); axs[0].set_title("Work items by status",color=NAVY)
own={}
for k,s,p,o,sp,t in I: own[o]=own.get(o,0)+p
axs[1].bar([o.split()[0] for o in own],list(own.values()),color=[NAVY,TEAL,AMB]); axs[1].set_title("Story points by assignee",color=NAVY)
for i,v in enumerate(own.values()): axs[1].text(i,v+.5,str(v),ha="center")
axs[2].bar(["5 Nov","11 Nov"],[22,52],color=TEAL); axs[2].set_title("Story points completed per day",color=NAVY)
for i,v in enumerate([22,52]): axs[2].text(i,v+.8,str(v),ha="center")
fig.suptitle("Jira Dashboard - RLRS (Remote Lab Reservation System), Team 11",color=NAVY,weight="bold",x=.02,ha="left",fontsize=16)
fig.text(.01,.01,SRC,fontsize=8,color=GREY); fig.tight_layout(rect=[0,.04,1,.93]); fig.savefig("01_jira_dashboard.png",dpi=150); plt.close(fig)
