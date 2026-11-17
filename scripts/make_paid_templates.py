from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).parent
OUT = ROOT.parent / "backend" / "seed_files"
FONT_DIR = ROOT / "fonts"
for n in ["PlayfairDisplay", "PlayfairDisplay-Italic", "DMSans"]:
    pdfmetrics.registerFont(TTFont(n, str(FONT_DIR / f"{n}.ttf")))

INK, PAPER, CREAM, GOLD, LINE, MUTED = [HexColor(x) for x in ["#29352f", "#f5f4ef", "#e9e8de", "#b58e3d", "#d9dbd2", "#7a857d"]]
W, H = A4
M = 54

TEMPLATES = [
("money-map", "Money Map Financial Tracker", "Finance", "A clear monthly system for knowing where your money goes and what it is helping you build.", 299, "Financial tracker", "photo-1554224155-6726b3ff858f", "bundle"),
("monthly-budget", "Monthly Budget Planner", "Finance", "A calm, practical budget with income, bills, sinking funds and weekly check-ins.", 199, "Budgeting", "photo-1554224154-22dec7ec8818", "bundle"),
("debt-payoff", "Debt Payoff Tracker", "Finance", "A motivating visual plan for choosing a payoff strategy and watching your balance shrink.", 249, "Finance", "photo-1450101499163-c8848c66ca85", "bundle"),
("savings-goals", "Savings Goals Planner", "Finance", "Turn big savings goals into small, visible milestones you can keep showing up for.", 149, "Finance", "photo-1579621970563-ebec7560ff3e", "pdf"),
("subscription-audit", "Subscription Audit", "Finance", "Find the quiet leaks in your monthly spending and make room for what you actually use.", 99, "Finance", "photo-1556742049-0cfed4f6a45d", "pdf"),
("income-invoice", "Income & Invoice Tracker", "Business", "A simple system for tracking paid work, open invoices, follow-ups and income by month.", 199, "Business", "photo-1554224155-8d04cb21cd6c", "bundle"),
("freelancer-finance", "Freelancer Finance Dashboard", "Business", "A practical money dashboard for irregular income, taxes, expenses and a steadier business.", 499, "Business", "photo-1556761175-b413da4baf72", "bundle"),
("content-batch", "Content Batch Planner", "Business", "Plan a full month of thoughtful content in a few focused sessions without becoming a content machine.", 199, "Planning", "photo-1499750310107-5fef28a66643", "bundle"),
("client-onboarding", "Client Onboarding Kit", "Business", "A warm, clear client journey with welcome notes, information gathering and next steps.", 299, "Business", "photo-1552664730-d307ca884978", "pdf"),
("project-scope", "Project Scope Planner", "Business", "Set kind boundaries, define deliverables and make the work easier to agree on before it begins.", 249, "Business", "photo-1454165804606-c3d57bc86b40", "pdf"),
("meeting-notes", "Meeting Notes System", "Planning", "A focused meeting page that turns conversation into decisions, owners and next actions.", 129, "Planning", "photo-1517245386807-bb43f82c33c4", "pdf"),
("job-search", "Job Search Tracker", "Career", "Keep applications, follow-ups, networking and interview notes in one calm, confidence-building system.", 199, "Career", "photo-1521737711867-e3b97375f902", "bundle"),
("meal-grocery", "Meal & Grocery Planner", "Home", "Plan flexible meals, use what you have and make the weekly shop feel lighter.", 149, "Home", "photo-1498837167922-ddd27525d352", "pdf"),
("home-reset", "Home Reset Planner", "Home", "A gentle room-by-room reset for creating a home that supports the way you actually live.", 99, "Home", "photo-1484101403633-562f891dc89a", "pdf"),
("self-care", "Self-Care Habit Tracker", "Wellbeing", "A soft, no-pressure tracker for small rituals that help you feel more like yourself.", 129, "Wellbeing", "photo-1515377905703-c4788e51af15", "pdf"),
]

class PDF:
    def __init__(self, path, title):
        self.c = Canvas(str(path), pagesize=A4); self.c.setTitle(title); self.title = title; self.page_no = 0
    def text(self, x, y, s, size=10, color=INK, font="DMSans", align="left"):
        self.c.setFillColor(color); self.c.setFont(font, size)
        if align == "center": x -= pdfmetrics.stringWidth(s, font, size) / 2
        if align == "right": x -= pdfmetrics.stringWidth(s, font, size)
        self.c.drawString(x, y, s)
    def page(self, bg=PAPER, footer=True):
        if self.page_no: self.c.showPage()
        self.page_no += 1; self.c.setFillColor(bg); self.c.rect(0, 0, W, H, fill=1, stroke=0)
        if footer:
            self.text(M, 28, f"MORROW MARKET  ·  {self.title.upper()}", 7, MUTED); self.text(W-M, 28, f"{self.page_no:02d}", 8, MUTED, align="right")
    def eyebrow(self, y, s, x=M, color=MUTED): self.text(x, y, s.upper(), 7.5, color, align="left")
    def heading(self, y, a, b="", size=35):
        self.text(M, y, a, size, INK, "PlayfairDisplay"); self.text(M, y-size*1.03, b, size, GOLD, "PlayfairDisplay-Italic") if b else None
    def para(self, x, y, s, width, size=10, color=MUTED, lead=1.6):
        line=""
        for word in s.split():
            trial=(line+" "+word).strip()
            if pdfmetrics.stringWidth(trial,"DMSans",size)>width:
                self.text(x,y,line,size,color); y-=size*lead; line=word
            else: line=trial
        if line:self.text(x,y,line,size,color)
        return y-size*lead
    def line(self,x,y,w,color=LINE): self.c.setStrokeColor(color); self.c.setLineWidth(.65); self.c.line(x,y,x+w,y)
    def box(self,x,y,w,h,fill=white,stroke=LINE): self.c.setFillColor(fill);self.c.setStrokeColor(stroke);self.c.rect(x,y-h,w,h,fill=1,stroke=1)
    def cover(self, subtitle):
        self.page(INK,False); self.c.setFillColor(GOLD);self.c.circle(W-120,H-155,76,fill=1,stroke=0)
        self.text(W-120,H-150,"useful",13,INK,"PlayfairDisplay","center");self.text(W-120,H-168,"in real life",13,INK,"PlayfairDisplay-Italic","center")
        self.c.setFillColor(PAPER);self.c.rect(M,H-M,22,22,fill=1,stroke=0);self.text(M+6,H-M-16,"M",13,INK,"PlayfairDisplay-Italic");self.text(M+34,H-M-15,"Morrow market",11,PAPER,"PlayfairDisplay")
        self.eyebrow(H*.47,subtitle,color=GOLD); self.heading(H*.47-58,self.title.split(" ")[0]," ".join(self.title.split(" ")[1:]),48)
        self.para(M,H*.47-180,self.desc,W-2*M,11,HexColor("#c9cfc8"),1.7)
        self.line(M,90,W-2*M,HexColor("#4a5850"));self.text(M,68,"A DIGITAL TEMPLATE",7.5,HexColor("#c9cfc8"));self.text(W-M,68,"PRINT IT  ·  FILL IT  ·  RETURN TO IT",7.5,HexColor("#c9cfc8"),align="right")
    def standard_page(self, section, intro, prompts, bg=PAPER):
        self.page(bg);self.eyebrow(H-90,section);self.heading(H-135,prompts[0],prompts[1],30);self.para(M,H-225,intro,W-2*M,10.5,INK,1.7)
        y=H-320
        for i,label in enumerate(prompts[2:]):
            self.text(M,y,f"{i+1:02d}",17,GOLD,"PlayfairDisplay-Italic");self.text(M+44,y+1,label,12,INK,"PlayfairDisplay");self.line(M+44,y-22,W-2*M-44);self.line(M+44,y-45,W-2*M-44);y-=76
    def table_page(self, section, cols, rows=8):
        self.page();self.eyebrow(H-90,section);self.heading(H-135,"Keep it", "visible.",30);self.text(M,H-220,"Month  ______________________",10,MUTED);top=H-260;cw=(W-2*M)/len(cols)
        for j,col in enumerate(cols): self.box(M+j*cw,top,cw,34,CREAM);self.text(M+j*cw+8,top-22,col,8,INK)
        for i in range(rows):
            y=top-34-i*42
            for j in range(len(cols)): self.box(M+j*cw,y,cw,42,white)
    def closing(self, a,b, body):
        self.page(CREAM);self.eyebrow(H-180,"A last note");self.heading(H-235,a,b,38);self.para(M,H-340,body,W-2*M,11,INK,1.8);self.text(M,H-500,"With care,",12,INK,"PlayfairDisplay-Italic");self.text(M,H-522,"Morrow Market",12,INK,"PlayfairDisplay")
    def save(self): self.c.save()


def make_pdf(meta, path):
    pid,title,cat,desc,price,tag,img,kind=meta;b=PDF(path,title);b.desc=desc;b.title=title;b.cover(f"{tag}  ·  {cat}")
    if pid in {"money-map","monthly-budget","debt-payoff","savings-goals","subscription-audit","income-invoice","freelancer-finance"}:
        b.table_page("The dashboard", ["Date","Description","Category","In","Out","Balance"], 9)
        b.standard_page("The plan", "Use this page at the start of the month. Pick one clear intention, then give every rupee a job that supports it.", ["Money with intention", "this month.", "My money intention", "Income I can count on", "Bills and essentials", "Goals I am funding", "One thing I can simplify"])
        b.table_page("Weekly check-in", ["Week","In","Out","Saved","Note"], 5)
    elif pid in {"content-batch","job-search"}:
        b.table_page("The overview", ["Date","Focus","Next action","Status"], 8)
        b.standard_page("The rhythm", "Small, repeatable actions beat a dramatic burst of effort. Choose a rhythm you can keep on an ordinary week.", ["Make it doable", "one step at a time.", "This week's focus", "Three actions", "People to follow up with", "A win to record", "Next week starts with"])
    else:
        b.standard_page("Start here", desc, ["A clearer next step", "make room for it.", "What is true right now", "What needs deciding", "What would make this easier", "The kind boundary", "My next small action"])
        b.standard_page("Use the page", "Return to this template whenever you need it. The goal is not to fill every box. The goal is to make the next thing easier.", ["A simple system", "you can return to.", "Today", "This week", "Later", "Not now", "Done is enough"])
    b.closing("Useful beats", "perfect.", "Keep this template close to the moment it is useful. Print another copy when the page is full, and let the system get better as your life changes.")
    b.save()


def make_xlsx(meta, pdf_path):
    pid,title,*_=meta;wb=Workbook();ws=wb.active;ws.title="Dashboard";ws.sheet_view.showGridLines=False
    dark="29352F"; gold="B58E3D"; cream="E9E8DE"; thin=Side(style="thin",color="D9DBD2")
    ws["A1"]=title;ws["A1"].font=Font(name="Aptos Display",size=22,bold=True,color=dark);ws.merge_cells("A1:F1")
    ws["A2"]="Add your numbers below. Totals update as you fill the sheet.";ws["A2"].font=Font(size=10,color="7A857D");ws.merge_cells("A2:F2")
    headers=["Date","Description","Category","Planned","Actual","Notes"]
    for c,h in enumerate(headers,1):
        cell=ws.cell(4,c,h);cell.font=Font(bold=True,color="FFFFFF");cell.fill=PatternFill("solid",fgColor=dark);cell.alignment=Alignment(vertical="center")
    for r in range(5,25):
        for c in range(1,7): ws.cell(r,c).border=Border(bottom=thin)
        ws.cell(r,4).number_format='₹#,##0';ws.cell(r,5).number_format='₹#,##0'
    ws["C26"]="TOTAL";ws["C26"].font=Font(bold=True,color=dark);ws["D26"]="=SUM(D5:D24)";ws["E26"]="=SUM(E5:E24)"
    for cell in [ws["D26"],ws["E26"]]:cell.number_format='₹#,##0';cell.font=Font(bold=True,color=gold)
    for col,width in {"A":14,"B":28,"C":18,"D":14,"E":14,"F":28}.items():ws.column_dimensions[col].width=width
    readme=wb.create_sheet("How to use");readme["A1"]="A softer way to stay on top of it";readme["A1"].font=Font(size=18,bold=True,color=dark);readme["A3"]="1. Add one row per transaction or task.\n2. Keep categories simple.\n3. Review the totals once a week.\n4. Use the PDF pages when you want to think on paper.";readme["A3"].alignment=Alignment(wrap_text=True,vertical="top");readme.column_dimensions["A"].width=80;readme.row_dimensions[3].height=90
    xlsx=OUT/f"{pid}.xlsx";wb.save(xlsx);return xlsx

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for meta in TEMPLATES:
        pid=meta[0];pdf=OUT/f"{pid}.pdf";make_pdf(meta,pdf)
        if meta[-1]=="bundle":
            xlsx=make_xlsx(meta,pdf);zip_path=OUT/f"{pid}-bundle.zip"
            with ZipFile(zip_path,"w",ZIP_DEFLATED) as z:z.write(pdf,pdf.name);z.write(xlsx,xlsx.name)
            pdf.unlink();xlsx.unlink()
    print("created",len(TEMPLATES),"products")
