from pathlib import Path
from make_workbooks import Book, M, H, W, PAPER, CREAM, INK, GOLD, MUTED, LINE, white, closing


def starter_planner():
    b = Book("free-weekly-planner.pdf", "Free Weekly Planner")
    b.cover("Free template 01  ·  Planning", "A calmer", "week.", "A one-page weekly planner with room for your three priorities, appointments, meals and one small thing that makes the week feel like yours.", ("plan", "gently"))
    b.page()
    b.eyebrow(H - 100, "This week")
    b.heading(H - 150, "Make space for", "what matters.", 34)
    b.text(M, H - 260, "Week of  __________________________", 11, MUTED)
    b.text(M, H - 315, "Three priorities", 15, INK, "PlayfairDisplay-Italic")
    for i in range(3):
        b.text(M, H - 350 - i * 30, f"{i + 1}.", 11, GOLD, "PlayfairDisplay")
        b.lines(M + 20, H - 353 - i * 30, W - 2 * M - 20, 1)
    b.text(M, H - 475, "The week at a glance", 15, INK, "PlayfairDisplay-Italic")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cw, ch = (W - 2 * M - 12) / 2, 92
    for i, day in enumerate(days):
        x, y = M + (i % 2) * (cw + 12), H - 510 - (i // 2) * (ch + 10)
        b.box(x, y, cw, ch, fill=white if i < 5 else CREAM)
        b.eyebrow(y - 15, day, x + 12, INK)
        b.lines(x + 12, y - 38, cw - 24, 2, 20)
    b.page(CREAM)
    b.eyebrow(H - 100, "A tiny reset")
    b.heading(H - 150, "Before Monday", "arrives.", 34)
    b.para(M, H - 250, "Choose the version of this week that feels kind and possible. You can print this page again next week — there is no perfect way to use it.", W - 2 * M, 11, INK, 1.7)
    for i, item in enumerate(["Clear one surface", "Check the calendar", "Choose three meals", "Put one thing on pause", "Name something to look forward to"]):
        b.check(M, H - 350 - i * 38, item, 11)
    b.text(M, 180, "One thing I want to remember this week:", 13, INK, "PlayfairDisplay-Italic")
    b.lines(M, 150, W - 2 * M, 5, 24)
    closing(b, "A good week", "can be simple.", "Print this planner whenever you need a reset. Keep the bar low enough to step over, and leave a little room for the unexpected good stuff.")
    b.save()


def moodboard():
    b = Book("free-brand-moodboard.pdf", "Free Brand Moodboard")
    b.cover("Free template 02  ·  Brand", "Find your", "visual voice.", "A simple moodboard worksheet for collecting the colours, textures and words that make your brand feel unmistakably yours.", ("make it", "yours"))
    b.page()
    b.eyebrow(H - 100, "Start here")
    b.heading(H - 150, "Three words", "to guide you.", 34)
    b.para(M, H - 250, "Choose words for the feeling, not the category. Think warm, precise, curious, grounded, luminous, playful, considered.", W - 2 * M, 11, INK, 1.7)
    for i in range(3):
        y = H - 350 - i * 85
        b.text(M, y, f"0{i + 1}", 20, GOLD, "PlayfairDisplay-Italic")
        b.lines(M + 55, y - 4, W - 2 * M - 55, 1)
        b.text(M + 55, y - 26, "Why this word?", 9, MUTED)
        b.lines(M + 55, y - 47, W - 2 * M - 55, 1)
    b.page()
    b.eyebrow(H - 100, "Collect")
    b.heading(H - 150, "Your visual", "ingredients.", 34)
    b.para(M, H - 250, "Tape in a photo, pull a colour from a favourite object, or write down a texture you want people to feel.", W - 2 * M, 11, INK, 1.7)
    labels = ["Colour 01", "Colour 02", "Texture", "Shape", "Image mood", "Type style"]
    for i, lab in enumerate(labels):
        x, y = M + (i % 2) * ((W - 2 * M) / 2 + 8), H - 330 - (i // 2) * 125
        cw = (W - 2 * M - 8) / 2
        b.box(x, y, cw, 92, fill=white)
        b.text(x + 14, y - 24, lab, 13, INK, "PlayfairDisplay-Italic")
        b.lines(x + 14, y - 49, cw - 28, 2, 20)
    b.page(CREAM)
    b.eyebrow(H - 100, "Bring it together")
    b.heading(H - 150, "My brand", "in one sentence.", 34)
    b.para(M, H - 250, "Complete this after you have collected your references:", W - 2 * M, 11, INK, 1.7)
    b.text(M, H - 340, "My brand feels", 15, INK, "PlayfairDisplay-Italic")
    b.lines(M, H - 370, W - 2 * M, 2, 24)
    b.text(M, H - 450, "It is for people who", 15, INK, "PlayfairDisplay-Italic")
    b.lines(M, H - 480, W - 2 * M, 2, 24)
    b.text(M, H - 560, "It should never feel", 15, INK, "PlayfairDisplay-Italic")
    b.lines(M, H - 590, W - 2 * M, 2, 24)
    closing(b, "Clarity first,", "decoration second.", "The strongest visual direction usually starts with a feeling. Keep this page near your desk when you make your next website, post or product.")
    b.save()


if __name__ == "__main__":
    OUT = Path(__file__).parent.parent / "backend" / "seed_files"
    OUT.mkdir(exist_ok=True)
    starter_planner(); moodboard()
    print("free templates created")
