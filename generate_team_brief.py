"""
generate_team_brief.py — one-page Team Publication Strategy brief (PDF) to hand to the group.
Run: python generate_team_brief.py  -> BDS-SMC2_Team_Publication_Brief.pdf
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER
import os

OUT = os.path.join(os.path.dirname(__file__), "BDS-SMC2_Team_Publication_Brief.pdf")
NAVY=colors.HexColor("#1a3a5c"); BLUE=colors.HexColor("#2e5fa3"); GREEN=colors.HexColor("#2d7a3a")
GOLD=colors.HexColor("#b07d1a"); LGRAY=colors.HexColor("#f4f7fb"); DGRAY=colors.HexColor("#555555"); WHITE=colors.white

def st(n,**k): return ParagraphStyle(n,**k)
TITLE=st("T",fontSize=16,textColor=NAVY,alignment=TA_CENTER,fontName="Helvetica-Bold",spaceAfter=2)
SUB  =st("S",fontSize=9.5,textColor=BLUE,alignment=TA_CENTER,fontName="Helvetica",spaceAfter=8)
H2   =st("H2",fontSize=10.5,textColor=NAVY,fontName="Helvetica-Bold",spaceBefore=8,spaceAfter=3)
BODY =st("B",fontSize=8.5,textColor=colors.black,fontName="Helvetica",leading=11,spaceAfter=3)
NOTE =st("N",fontSize=7.5,textColor=DGRAY,fontName="Helvetica-Oblique",spaceAfter=2)
CELL =st("C",fontSize=8,textColor=colors.black,fontName="Helvetica",leading=10)
CELLH=st("CH",fontSize=8,textColor=DGRAY,fontName="Helvetica-Bold",leading=10)
FOOT =st("F",fontSize=7,textColor=DGRAY,alignment=TA_CENTER)

def P(t,s=BODY): return Paragraph(t,s)
def tbl(data,w,header=colors.HexColor("#dce6f1")):
    t=Table(data,colWidths=w)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),header),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LGRAY,WHITE]),
        ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#cccccc")),
        ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
        ("LEFTPADDING",(0,0),(-1,-1),5),("VALIGN",(0,0),(-1,-1),"TOP")]))
    return t

doc=SimpleDocTemplate(OUT,pagesize=A4,leftMargin=1.5*cm,rightMargin=1.5*cm,topMargin=1.3*cm,bottomMargin=1.3*cm)
s=[]
s+=[P("UAV Emergency Rescue — Team Publication Strategy",TITLE),
    P("Turning Objectives 1–5 into publishable papers · prepared by Student 5 (BeiDou Short Message)",SUB)]

# Principle box
pb=Table([[P("<b>The principle:</b> the base method is NOT the contribution. We all use established tools "
             "(RTKLIB, PX4/QGC, vision detection, RRT*). A Q1 reviewer rejects “we applied known method X.” "
             "Our publishable angle is the <b>disaster-rescue gap the standard method does not cover.</b> Find that gap.",
             BODY)]],colWidths=[18*cm])
pb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#fff8e1")),
    ("BOX",(0,0),(-1,-1),0.6,GOLD),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7)]))
s+=[pb,Spacer(1,6)]

s.append(P("Per-objective publishable angles",H2))
s.append(tbl([
    [P("<b>Obj (owner)</b>",CELLH),P("<b>Publishable argument — the disaster-rescue gap</b>",CELLH),P("<b>Realistic</b>",CELLH)],
    [P("1 RTK positioning",CELL),P("RTK reliability under compound-disaster GNSS degradation + a viability-gating scheme for safe autonomous landing (the Level-3 total-failure scenarios ARE the novelty — not RTKLIB)",CELL),P("Q1/Q2",CELL)],
    [P("2 QGC / mission",CELL),P("Autonomous precision-landing decision framework gated on real-time RTK viability (land / hold / re-converge / abort)",CELL),P("Q2/Q3 or joint",CELL)],
    [P("3 Target detection",CELL),P("Detection-TO-geolocation pipeline (aerial detection → rescue coordinate), OR a disaster-survivor dataset, OR detection under rubble/occlusion/aerial viewpoint",CELL),P("Q2/Q3",CELL)],
    [P("4 Path planning",CELL),P("Uncertainty-aware planning to a survivor REGION defined by the rescue search-radius R — not a point (RRT* alone will not publish)",CELL),P("Q2/Q3",CELL)],
    [P("5 BeiDou SMC",CELL),P("Field-measured BDS-SMC rescue link + complete 112-bit payload (Paper 1); real-hardware GCS + operations layer (Paper 2)",CELL),P("Q1 / Q1-Q2",CELL)],
],[3*cm,12.5*cm,2.5*cm]))

s.append(P("Cross-objective papers — often stronger than the parts",H2))
s.append(tbl([
    [P("<b>Combination</b>",CELLH),P("<b>Why it is novel</b>",CELLH)],
    [P("Obj1 RTK viability → Obj2 landing",CELL),P("Position-confidence-gated autonomous landing (closed safety loop)",CELL)],
    [P("Obj5 uncertainty R → Obj4 planning",CELL),P("Uncertainty-aware planning to a survivor region, not a point",CELL)],
    [P("Obj3 detect → Obj5 coord → Obj4 path",CELL),P("Detection-confirmed rescue retargeting",CELL)],
],[6*cm,12*cm]))

# Recommendation box
rb=Table([[P("<b>Recommended strategy:</b> NOT five separate papers. Target <b>1–2 strong solo papers</b> "
             "(Obj 5, and Obj 1) <b>+ ONE joint flagship system paper</b> where every member is an author. "
             "Quality over a forced paper each. A few publishable papers beat many unpublishable ones.<br/>"
             "<b>Realistic Q1:</b> Obj 5 (Paper 1) and the joint system paper if we manage one real flight. "
             "The rest are credible Q2/Q3 or strengthen the joint paper.",BODY)]],colWidths=[18*cm])
rb.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#eafaf1")),
    ("BOX",(0,0),(-1,-1),0.8,GREEN),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ("LEFTPADDING",(0,0),(-1,-1),7),("RIGHTPADDING",(0,0),(-1,-1),7)]))
s+=[Spacer(1,4),rb,Spacer(1,4)]

s.append(P("One real flight (one drone to one real BeiDou-transmitted coordinate) is the single highest-value "
           "addition — it converts the joint paper from 'simulation-validated' to 'demonstrated system' and "
           "unlocks better venues.",NOTE))
s+=[Spacer(1,4),HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#cccccc")),
    P("BDS-SMC2 Team Publication Strategy  |  prepared by Letsoalo Maile  |  June 2026  |  discussion document",FOOT)]

doc.build(s)
print(f"[SAVED] {OUT}")
