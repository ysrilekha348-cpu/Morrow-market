"""Generates the three Morrow Market seed workbooks into backend/seed_files/."""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE = Path(__file__).parent
OUT = HERE.parent / "backend" / "seed_files"
for n in ["PlayfairDisplay", "PlayfairDisplay-Italic", "DMSans"]:
    pdfmetrics.registerFont(TTFont(n, str(HERE / "fonts" / f"{n}.ttf")))

INK, PAPER, CREAM, GOLD, LINE, MUTED = (HexColor(x) for x in ["#29352f", "#f5f4ef", "#e9e8de", "#b58e3d", "#d9dbd2", "#7a857d"])
W, H = A4
M = 56


class Book:
    def __init__(self, filename, title):
        self.c = Canvas(str(OUT / filename), pagesize=A4)
        self.c.setTitle(title)
        self.c.setAuthor("Morrow Market")
        self.title, self.n = title, 0

    def page(self, bg=PAPER, footer=True):
        if self.n:
            self.c.showPage()
        self.n += 1
        self.c.setFillColor(bg)
        self.c.rect(0, 0, W, H, stroke=0, fill=1)
        if footer:
            self.text(M, 30, f"MORROW MARKET  ·  {self.title.upper()}", 7, MUTED, space=1.4)
            self.text(W - M, 30, f"{self.n:02d}", 8, MUTED, align="right")

    def text(self, x, y, s, size=10, color=INK, font="DMSans", align="left", space=0):
        c = self.c
        c.setFillColor(color)
        c.setFont(font, size)
        if align == "right":
            x -= pdfmetrics.stringWidth(s, font, size) + space * len(s)
        elif align == "center":
            x -= (pdfmetrics.stringWidth(s, font, size) + space * len(s)) / 2
        t = c.beginText(x, y)
        t.setFont(font, size)
        t.setCharSpace(space)
        t.textLine(s)
        c.drawText(t)

    def eyebrow(self, y, s, x=M, color=MUTED):
        self.text(x, y, s.upper(), 7.5, color, space=1.8)

    def heading(self, y, plain, italic="", size=34, x=M, color=INK):
        self.text(x, y, plain, size, color, "PlayfairDisplay")
        if italic:
            self.text(x, y - size * 1.02, italic, size, GOLD, "PlayfairDisplay-Italic")

    def para(self, x, y, s, width, size=10, color=MUTED, lead=1.6, font="DMSans"):
        words, line = s.split(), ""
        for w in words:
            trial = f"{line} {w}".strip()
            if pdfmetrics.stringWidth(trial, font, size) > width:
                self.text(x, y, line, size, color, font)
                y -= size * lead
                line = w
            else:
                line = trial
        if line:
            self.text(x, y, line, size, color, font)
        return y - size * lead

    def lines(self, x, y, width, count, gap=22, color=LINE):
        self.c.setStrokeColor(color)
        self.c.setLineWidth(0.6)
        for i in range(count):
            self.c.line(x, y - i * gap, x + width, y - i * gap)
        return y - count * gap

    def box(self, x, y, w, h, fill=None, stroke=LINE):
        if stroke:
            self.c.setStrokeColor(stroke)
        self.c.setLineWidth(0.7)
        if fill:
            self.c.setFillColor(fill)
        self.c.rect(x, y - h, w, h, stroke=1 if stroke else 0, fill=1 if fill else 0)

    def check(self, x, y, label, size=10):
        self.box(x, y + 8, 9, 9)
        self.text(x + 18, y, label, size, INK)

    def cover(self, eyebrow, plain, italic, blurb, note, bg=INK):
        self.page(bg, footer=False)
        c = self.c
        c.setFillColor(GOLD)
        c.circle(W - 120, H - 170, 78, stroke=0, fill=1)
        self.text(W - 120, H - 165, note[0], 13, INK, "PlayfairDisplay", "center")
        self.text(W - 120, H - 182, note[1], 13, INK, "PlayfairDisplay-Italic", "center")
        self.box(M, H - M, 22, 22, fill=PAPER, stroke=None)
        self.text(M + 6, H - M - 16, "M", 13, INK, "PlayfairDisplay-Italic")
        self.text(M + 32, H - M - 15, "Morrow market", 11, PAPER, "PlayfairDisplay")
        self.eyebrow(H * 0.47, eyebrow, color=GOLD)
        self.heading(H * 0.47 - 62, plain, italic, size=56, color=PAPER)
        self.para(M, H * 0.47 - 190, blurb, 330, 11, HexColor("#c9cfc8"), 1.7)
        c.setStrokeColor(HexColor("#4a5850"))
        c.line(M, 90, W - M, 90)
        self.text(M, 68, "A DIGITAL WORKBOOK", 7.5, HexColor("#c9cfc8"), space=1.8)
        self.text(W - M, 68, "PRINT IT  ·  FILL IT  ·  RETURN TO IT", 7.5, HexColor("#c9cfc8"), align="right", space=1.8)

    def save(self):
        self.c.save()


def closing(b, plain, italic, s):
    b.page(CREAM)
    b.eyebrow(H - 200, "A last note")
    b.heading(H - 260, plain, italic, 40)
    b.para(M, H - 370, s, 360, 11, INK, 1.8)
    b.text(M, H - 520, "With care,", 12, INK, "PlayfairDisplay-Italic")
    b.text(M, H - 540, "Morrow Market", 12, INK, "PlayfairDisplay")


# ---------------------------------------------------------------- Weekly Reset
def weekly_reset():
    b = Book("the-weekly-reset.pdf", "The Weekly Reset")
    b.cover("Workbook 01  ·  Planning", "The Weekly", "Reset.",
            "A gentle planning system for people who want their weeks to feel lighter, not louder. Four weeks of reset pages, reflections and a monthly look back.",
            ("lighter", "weeks"))

    b.page()
    b.eyebrow(H - 110, "Before you begin")
    b.heading(H - 160, "How to use", "this workbook.")
    y = b.para(M, H - 250, "Most planners ask you to do more. This one asks you to notice more. Set aside 30 unhurried minutes at the end of each week, ideally with something warm to drink, and move through the pages in order.", 400, 11, INK, 1.8)
    steps = [("01", "Clear", "Empty your head onto the brain-dump page. Nothing is too small."),
             ("02", "Look back", "Answer the reflection prompts honestly. No grades."),
             ("03", "Choose", "Pick only three priorities. Everything else is a bonus."),
             ("04", "Shape", "Sketch your week loosely. Leave white space on purpose."),
             ("05", "Close", "Finish the Sunday checklist and call the week done.")]
    y -= 30
    for num, t, d in steps:
        b.text(M, y, num, 22, GOLD, "PlayfairDisplay-Italic")
        b.text(M + 60, y + 6, t, 15, INK, "PlayfairDisplay")
        b.para(M + 60, y - 12, d, 360, 10)
        y -= 70

    b.page()
    b.eyebrow(H - 110, "The ritual")
    b.heading(H - 160, "Sunday reset", "checklist.")
    groups = [("Space", ["Clear my desk and bag", "Do one load of laundry", "Reset the kitchen", "Open the windows for ten minutes"]),
              ("Mind", ["Brain-dump everything on my mind", "Check the calendar for the next 14 days", "Reply to the messages I've been avoiding", "Write tomorrow's first task on a sticky note"]),
              ("Body", ["Plan three simple meals", "Lay out tomorrow's clothes", "Step outside for a slow walk", "Be in bed 30 minutes earlier tonight"])]
    y = H - 270
    for g, items in groups:
        b.text(M, y, g, 16, INK, "PlayfairDisplay-Italic")
        y -= 28
        for it in items:
            b.check(M, y, it)
            y -= 24
        y -= 22

    for week in range(1, 5):
        b.page()
        b.eyebrow(H - 90, f"Week {week:02d}  ·  Brain dump")
        b.heading(H - 135, "Empty your", "head first.", 30)
        b.box(M, H - 210, W - 2 * M, H - 300, fill=white)
        b.lines(M + 18, H - 245, W - 2 * M - 36, 21, 24)

        b.page()
        b.eyebrow(H - 90, f"Week {week:02d}  ·  The plan")
        b.text(M, H - 130, "Dates  ________________________", 10, MUTED)
        b.text(M, H - 175, "Three priorities", 15, INK, "PlayfairDisplay-Italic")
        for i in range(3):
            y = H - 205 - i * 30
            b.text(M, y, f"{i + 1}.", 11, GOLD, "PlayfairDisplay")
            b.lines(M + 20, y - 3, W - 2 * M - 20, 1)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        cw, ch, top = (W - 2 * M - 12) / 2, 88, H - 310
        for i, d in enumerate(days[:6]):
            x, y = M + (i % 2) * (cw + 12), top - (i // 2) * (ch + 10)
            b.box(x, y, cw, ch, fill=white)
            b.eyebrow(y - 16, d, x + 12, INK)
            b.lines(x + 12, y - 38, cw - 24, 3, 18)
        y = top - 3 * (ch + 10)
        b.box(M, y, cw, ch, fill=CREAM, stroke=None)
        b.eyebrow(y - 16, "Sunday · rest", M + 12, INK)
        b.lines(M + 12, y - 38, cw - 24, 3, 18, HexColor("#cfcfc2"))
        x = M + cw + 12
        b.box(x, y, cw, ch, fill=white)
        b.eyebrow(y - 16, "Energy this week", x + 12, INK)
        for i, lab in enumerate(["M", "T", "W", "T", "F", "S", "S"]):
            cx = x + 22 + i * ((cw - 44) / 6)
            b.c.setStrokeColor(LINE)
            b.c.circle(cx, y - 52, 9, stroke=1, fill=0)
            b.text(cx, y - 77, lab, 8, MUTED, align="center")

        b.page()
        b.eyebrow(H - 90, f"Week {week:02d}  ·  Reflection")
        b.heading(H - 135, "Looking", "back, kindly.", 30)
        prompts = ["What felt good this week?", "What drained me, and what can I change?", "One thing I'm proud of, however small:",
                   "Something I want to carry into next week:", "Something I'm ready to let go of:"]
        y = H - 250
        for p in prompts:
            b.text(M, y, p, 12, INK, "PlayfairDisplay")
            y = b.lines(M, y - 22, W - 2 * M, 3, 22) - 18

    b.page()
    b.eyebrow(H - 90, "End of month")
    b.heading(H - 135, "The monthly", "look back.", 30)
    labels = ["Highlights", "Lessons", "Habits that stuck", "Next month's focus"]
    cw, ch = (W - 2 * M - 14) / 2, 250
    for i, lab in enumerate(labels):
        x, y = M + (i % 2) * (cw + 14), H - 230 - (i // 2) * (ch + 14)
        b.box(x, y, cw, ch, fill=white)
        b.text(x + 14, y - 26, lab, 14, INK, "PlayfairDisplay-Italic")
        b.lines(x + 14, y - 52, cw - 28, 9, 21)

    closing(b, "Small resets,", "big shifts.", "You don't need a perfect week to have a good one. Come back to these pages every Sunday, and in a few months you'll see a quieter, steadier rhythm. Print as many weekly pages as you like. This workbook is yours to reuse.")
    b.save()


# ---------------------------------------------------------------- Quiet Brand Kit
def quiet_brand():
    b = Book("quiet-brand-kit.pdf", "Quiet Brand Kit")
    b.cover("Kit 02  ·  Templates", "Quiet", "Brand Kit.",
            "A considered visual direction kit for small brands ready to look like themselves. Worksheets, palettes, type pairings and templates you can use today.",
            ("look like", "yourself"))

    b.page()
    b.eyebrow(H - 110, "Part one")
    b.heading(H - 160, "Brand", "foundations.")
    qs = [("Why do you exist?", "Finish the sentence: I help ______ to ______ so that ______."),
          ("Who is it for?", "Describe one real person you'd love to serve. What keeps them up at night?"),
          ("What do you believe?", "Three values you won't compromise on."),
          ("How should people feel?", "Pick three feelings someone should have after meeting your brand.")]
    y = H - 260
    for q, hint in qs:
        b.text(M, y, q, 15, INK, "PlayfairDisplay")
        b.text(M, y - 16, hint, 9, MUTED)
        y = b.lines(M, y - 40, W - 2 * M, 3, 22) - 22

    b.page()
    b.eyebrow(H - 110, "Part two")
    b.heading(H - 160, "Voice &", "tone.")
    b.para(M, H - 250, "A quiet brand has a clear voice. Fill in both columns, then keep this page next to you whenever you write a caption, an email or a product description.", 420, 10.5, INK, 1.7)
    cw = (W - 2 * M - 16) / 2
    for i, (lab, ex) in enumerate([("We are...", ["warm, not gushing", "clear, not clinical", "confident, not loud"]),
                                   ("We are never...", ["pushy or urgent", "full of jargon", "trying to be everyone"])]):
        x = M + i * (cw + 16)
        b.box(x, H - 320, cw, 330, fill=white if i == 0 else CREAM, stroke=LINE if i == 0 else None)
        b.text(x + 16, H - 350, lab, 16, INK, "PlayfairDisplay-Italic")
        b.eyebrow(H - 375, "For example", x + 16)
        for j, e in enumerate(ex):
            b.text(x + 16, H - 395 - j * 16, f"·  {e}", 9.5, MUTED)
        b.eyebrow(H - 465, "Yours", x + 16)
        b.lines(x + 16, H - 490, cw - 32, 6, 24)
    y = H - 690
    b.text(M, y, "Words we love", 12, INK, "PlayfairDisplay")
    b.lines(M + 110, y - 2, W - 2 * M - 110, 1)
    b.text(M, y - 32, "Words we avoid", 12, INK, "PlayfairDisplay")
    b.lines(M + 110, y - 34, W - 2 * M - 110, 1)

    b.page()
    b.eyebrow(H - 110, "Part three")
    b.heading(H - 160, "Three quiet", "palettes.")
    b.para(M, H - 250, "Each palette pairs one dominant neutral, one deep anchor and one accent used sparingly. Copy the hex codes straight into Canva, Figma or your website builder.", 420, 10.5, INK, 1.7)
    palettes = [("Morning Linen", "calm, editorial, trustworthy", ["#F5F4EF", "#E9E8DE", "#29352F", "#B58E3D"]),
                ("Clay Studio", "warm, handmade, grounded", ["#F3EDE4", "#D9B8A0", "#6E4B3A", "#2E2A27"]),
                ("Sea Glass", "fresh, gentle, modern", ["#EEF2EF", "#A9C2B8", "#3E6259", "#1F2D2A"])]
    y = H - 330
    for name, mood, cols in palettes:
        b.text(M, y, name, 16, INK, "PlayfairDisplay")
        b.text(M, y - 16, mood, 9, MUTED)
        sw = (W - 2 * M - 30) / 4
        for i, hx in enumerate(cols):
            x = M + i * (sw + 10)
            b.box(x, y - 30, sw, 80, fill=HexColor(hx), stroke=LINE)
            b.text(x, y - 125, hx, 9, INK)
        y -= 170

    b.page()
    b.eyebrow(H - 110, "Part four")
    b.heading(H - 160, "Type pairings", "that whisper.")
    pairs = [("Playfair Display + DM Sans", "Editorial and elegant. Great for coaches, writers and boutique studios."),
             ("Fraunces + Inter Tight", "Soft and characterful. Lovely for food, craft and wellness brands."),
             ("Cormorant Garamond + Work Sans", "Refined and airy. Suits photographers, stylists and stationery."),
             ("DM Serif Display + Manrope", "Bold but friendly. Good for educators and product makers.")]
    y = H - 260
    for i, (p, d) in enumerate(pairs):
        b.box(M, y + 18, W - 2 * M, 100, fill=white if i % 2 == 0 else CREAM, stroke=None)
        b.text(M + 20, y - 14, "Aa", 30, GOLD, "PlayfairDisplay-Italic")
        b.text(M + 80, y - 8, p, 14, INK, "PlayfairDisplay")
        b.para(M + 80, y - 28, d, 360, 9.5)
        y -= 116
    b.para(M, y - 10, "All of these are free on Google Fonts. Rule of thumb: use the serif for headings only, the sans for everything else, and never more than two weights of each.", 420, 9.5)

    b.page()
    b.eyebrow(H - 110, "Part five")
    b.heading(H - 160, "Logo &", "mark checklist.")
    items = ["Works in one colour (black on white, and white on black)", "Still readable at 32 px wide, the size of a profile picture",
             "Has a simple mark or monogram version for small spaces", "Doesn't rely on a trend you'll be tired of in a year",
             "Saved as SVG, PNG with a transparent background, and a high-res JPG", "Clear-space rule set: leave the height of one letter around it",
             "Never stretched, outlined, drop-shadowed or rotated", "Tested next to your palette and fonts on a real product photo"]
    y = H - 260
    for it in items:
        b.check(M, y, it, 10.5)
        y -= 34

    b.page()
    b.eyebrow(H - 90, "Part six")
    b.heading(H - 135, "Social post", "templates.", 30)
    b.para(M, H - 210, "Three layouts to recreate in Canva at 1080 × 1350. Consistency beats novelty, so rotate these and let your content do the talking.", 420, 10, INK, 1.7)
    tw, th, ty = (W - 2 * M - 28) / 3, 210, H - 270
    names = [("The Quote", "big serif line, small credit"), ("The Product", "photo top, name and price below"), ("The Tip", "number, headline, three short lines")]
    for i, (n, d) in enumerate(names):
        x = M + i * (tw + 14)
        b.box(x, ty, tw, th, fill=white)
        if i == 0:
            b.text(x + tw / 2, ty - 90, "\u201cLess, but", 15, INK, "PlayfairDisplay", "center")
            b.text(x + tw / 2, ty - 110, "better.\u201d", 15, GOLD, "PlayfairDisplay-Italic", "center")
            b.text(x + tw / 2, ty - 170, "@YOURBRAND", 6.5, MUTED, align="center", space=1.2)
        elif i == 1:
            b.box(x + 12, ty - 12, tw - 24, 120, fill=CREAM, stroke=None)
            b.text(x + 14, ty - 158, "Product name", 11, INK, "PlayfairDisplay")
            b.text(x + 14, ty - 174, "₹499  ·  link in bio", 8, MUTED)
        else:
            b.text(x + 14, ty - 50, "03", 26, GOLD, "PlayfairDisplay-Italic")
            b.text(x + 14, ty - 80, "A headline tip", 12, INK, "PlayfairDisplay")
            b.lines(x + 14, ty - 105, tw - 28, 3, 18)
        b.text(x, ty - th - 22, n, 12, INK, "PlayfairDisplay")
        b.text(x, ty - th - 37, d, 8.5, MUTED)

    b.page(CREAM)
    b.eyebrow(H - 90, "Part seven")
    b.heading(H - 135, "Your brand", "on one page.", 30)
    fields = ["Brand name", "One-line promise", "Who it's for", "Three values", "Three feelings", "Voice in three words", "Palette (hex codes)", "Heading font / body font", "Signature phrase"]
    y = H - 230
    for f in fields:
        b.text(M, y, f, 11, INK, "PlayfairDisplay")
        b.lines(M + 160, y - 2, W - 2 * M - 160, 1, color=HexColor("#cfcfc2"))
        y -= 48

    closing(b, "Quiet is", "a strategy.", "You don't need to shout to be remembered. You need to be consistent and unmistakably yourself. Keep this kit open while you design, and come back to the one-page summary whenever something new feels off-brand.")
    b.save()


# ---------------------------------------------------------------- Slow Content Calendar
PROMPTS = [
    ("Story", ["The moment you knew you wanted to start this", "A mistake that taught you something useful", "What a normal working day looks like for you",
               "The first thing you ever sold, and how it felt", "Someone who shaped the way you work", "A small win from this week",
               "Something you changed your mind about", "Where you were a year ago versus today"]),
    ("Teach", ["One tip you wish you'd learned sooner", "A myth in your field you want to gently correct", "Your simplest process, in three steps",
               "The tool you'd keep if you could only keep one", "A beginner question you hear often, answered", "A before-and-after with what changed in between",
               "The checklist you actually use", "How to start with almost no budget"]),
    ("Invite", ["Ask your audience: what are you working on this week?", "This or that: two options, and they choose", "Share a work-in-progress and ask for thoughts",
                "Ask what they'd love you to make next", "Celebrate a customer or community member", "A gentle reminder of what you offer and who it's for",
                "Answer a question someone sent you"]),
    ("Pause", ["Your workspace, as it really is", "Something beautiful you noticed today", "A book, song or idea you keep coming back to",
               "What rest looks like for you", "A thank-you note to your audience", "What you're looking forward to next month",
               "One sentence about why you keep going"]),
]


def slow_content():
    b = Book("slow-content-calendar.pdf", "Slow Content Calendar")
    b.cover("Planner 03  ·  Planning", "Slow Content", "Calendar.",
            "30 thoughtful prompts to keep showing up without becoming a content machine. A monthly grid, a batching planner and space to reflect.",
            ("show up", "gently"))

    b.page()
    b.eyebrow(H - 110, "The philosophy")
    b.heading(H - 160, "Post less,", "mean more.")
    y = b.para(M, H - 250, "You don't need to post every day. You need to post things that sound like you, often enough that people remember you. These 30 prompts fall into four gentle themes. Rotate through them and your feed will feel balanced without you having to think about strategy.", 410, 11, INK, 1.8)
    y -= 20
    for name, desc in [("Story", "Build connection by sharing the human behind the work."), ("Teach", "Build trust by giving away something useful."),
                       ("Invite", "Build community by asking, listening and celebrating."), ("Pause", "Build warmth by showing the quiet in-between moments.")]:
        b.box(M, y, 6, 36, fill=GOLD, stroke=None)
        b.text(M + 20, y - 14, name, 15, INK, "PlayfairDisplay-Italic")
        b.text(M + 20, y - 30, desc, 9.5, MUTED)
        y -= 62
    b.para(M, y - 10, "Suggested rhythm: three posts a week, spending about one hour on Sunday batching them.", 410, 10, INK)

    day = 1
    for theme, items in PROMPTS:
        b.page()
        b.eyebrow(H - 90, f"Theme  ·  {theme}")
        b.heading(H - 135, f"{theme}", "prompts.", 30)
        y = H - 240
        for p in items:
            b.text(M, y, f"{day:02d}", 18, GOLD, "PlayfairDisplay-Italic")
            b.text(M + 42, y + 2, p, 11, INK, "PlayfairDisplay")
            b.lines(M + 42, y - 18, W - 2 * M - 42, 2, 18)
            b.box(W - M - 9, y + 12, 9, 9)
            y -= 66
            day += 1

    b.page()
    b.eyebrow(H - 90, "Month at a glance")
    b.text(M, H - 130, "Month  ________________________", 10, MUTED)
    cols, rows = 7, 5
    cw, ch, top = (W - 2 * M) / cols, 110, H - 170
    for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        b.eyebrow(top, d, M + i * cw + 6, INK)
    for r in range(rows):
        for col in range(cols):
            x, y = M + col * cw, top - 12 - r * ch
            b.box(x, y, cw, ch, fill=white if col < 5 else CREAM)
            b.text(x + 5, y - 13, "___", 7, MUTED)
    b.text(M, top - 12 - rows * ch - 22, "Tip: write the prompt number in the box, then tick it off once it's posted.", 8.5, MUTED)

    b.page()
    b.eyebrow(H - 90, "Sunday batching")
    b.heading(H - 135, "One hour,", "three posts.", 30)
    y = H - 250
    for i in range(3):
        b.box(M, y, W - 2 * M, 165, fill=white)
        b.text(M + 16, y - 26, f"Post {i + 1}", 14, INK, "PlayfairDisplay-Italic")
        for j, f in enumerate(["Prompt #", "Day", "Format"]):
            b.text(M + 120 + j * 120, y - 24, f"{f}  ______", 8.5, MUTED)
        b.eyebrow(y - 52, "Hook  ·  first line", M + 16)
        b.lines(M + 16, y - 72, W - 2 * M - 32, 1)
        b.eyebrow(y - 92, "Caption notes", M + 16)
        b.lines(M + 16, y - 112, W - 2 * M - 32, 2, 20)
        b.check(M + 16, y - 152, "Visual ready", 9)
        b.check(M + 140, y - 152, "Scheduled", 9)
        b.check(M + 250, y - 152, "Replied to comments", 9)
        y -= 185

    b.page()
    b.eyebrow(H - 90, "End of month")
    b.heading(H - 135, "What", "resonated?", 30)
    prompts = ["The post people responded to most, and why I think that is:", "The post I enjoyed making most:", "A theme I want more of next month:",
               "Something I'll stop doing:", "How I felt about showing up this month:"]
    y = H - 250
    for p in prompts:
        b.text(M, y, p, 12, INK, "PlayfairDisplay")
        y = b.lines(M, y - 22, W - 2 * M, 3, 22) - 18

    closing(b, "Consistency", "over intensity.", "The people who grow online aren't the loudest. They're the ones who keep quietly showing up. Thirty prompts will carry you through a month. Run through them again next month and you'll be surprised how differently you answer.")
    b.save()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    weekly_reset()
    quiet_brand()
    slow_content()
    print("done", sorted(p.name for p in OUT.iterdir()))
