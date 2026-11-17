from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from make_paid_templates import TEMPLATES, PDF, OUT, make_xlsx

VARIATIONS = {
    "money-map": ("Cash flow", "My money,", "mapped.", "Give every rupee a place, then check whether your spending is moving you toward the life you want.", ["Income streams", "Fixed essentials", "Flexible spending", "Future me", "A money decision I am proud of"]),
    "monthly-budget": ("Budgeting", "A budget that", "breathes.", "Start with what is real, not what a perfect month looks like. Use this for bills, flexible spending and sinking funds.", ["Income this month", "Must-pay bills", "Flexible categories", "Sinking funds", "One kind adjustment"]),
    "debt-payoff": ("Finance", "Make the", "plan visible.", "Choose your payoff method, list each balance and celebrate every small reduction.", ["Balances and rates", "Payoff strategy", "This month's payment", "A milestone to celebrate", "What I will do with the freed-up money"]),
    "savings-goals": ("Finance", "Small steps", "add up.", "Name the goal, choose a date and turn the distance into milestones you can actually see.", ["The goal", "Why it matters", "Milestones", "This month's transfer", "A reward that costs nothing"]),
    "subscription-audit": ("Finance", "Keep what", "serves you.", "Review renewals without guilt. Keep the tools you use, cancel the quiet leaks and redirect the difference.", ["What renewed", "What I actually use", "Keep, pause or cancel", "Annual cost", "Where the savings will go"]),
    "income-invoice": ("Business", "Money in", "motion.", "Track the work that has been promised, invoiced, paid and needs a gentle follow-up.", ["Client / project", "Invoice date", "Due date", "Follow-up date", "Payment received"]),
    "freelancer-finance": ("Business", "A steadier", "business.", "Irregular income needs a simple rhythm. Track your runway, tax reserve, business costs and next invoice.", ["Income forecast", "Tax reserve", "Business expenses", "Runway", "Next offer or follow-up"]),
    "content-batch": ("Planning", "Create once,", "share calmly.", "Choose a theme, turn one idea into a week of useful posts and leave room to be a person online.", ["The week's theme", "One idea to expand", "Three formats", "A story to tell", "The call to action"]),
    "client-onboarding": ("Business", "Start with", "clarity.", "A good client experience begins before the work. Set expectations, collect context and make the first week feel held.", ["What they need", "What I need from them", "Scope and boundaries", "First milestone", "Welcome note"]),
    "project-scope": ("Business", "Kind", "boundaries.", "A clear scope protects the quality of the work and gives everyone a calmer way to make decisions.", ["The outcome", "Included", "Not included", "Feedback rounds", "Change request plan"]),
    "meeting-notes": ("Planning", "Meetings that", "move things.", "Capture the decision, name the owner and leave with the next action visible.", ["The decision", "Context worth keeping", "Owner", "Due date", "Next meeting needed?"]),
    "job-search": ("Career", "A search with", "direction.", "Keep the practical details together so you can spend more energy on the conversations that matter.", ["Role and company", "Why it fits", "Contact", "Next follow-up", "What I learned"]),
    "meal-grocery": ("Home", "Feed the", "week gently.", "Plan around the life you have: a few reliable meals, a flexible shop and less food wasted.", ["Use what we have", "Three easy meals", "Fresh list", "Pantry restock", "One meal to look forward to"]),
    "home-reset": ("Home", "A home that", "supports you.", "Choose one room, one timer and one small finish line. Progress is allowed to look ordinary.", ["Room to reset", "Keep", "Move", "Donate", "The one surface that changes the room"]),
    "self-care": ("Wellbeing", "Tiny rituals", "count.", "Track the things that help you return to yourself without turning care into another performance.", ["A ritual for my body", "A ritual for my mind", "A boundary", "A person to reach out to", "How I want to feel"]),
}

def main():
    for meta in TEMPLATES:
        pid,title,cat,desc,price,tag,img,kind=meta
        if pid not in VARIATIONS: continue
        section, first, second, intro, prompts=VARIATIONS[pid]
        pdf=OUT/f"{pid}.pdf";b=PDF(pdf,title);b.desc=desc;b.title=title;b.cover(f"{tag}  ·  {cat}")
        b.standard_page(section,intro,[first,second,*prompts])
        b.table_page("The tracker", ["Date", "Focus", "Planned", "Actual", "Notes"], 9)
        b.standard_page("The review", "Use the final page to notice what worked, what felt heavy and what you want to carry forward.",["Keep the useful", "leave the rest.", "What worked", "What surprised me", "What I will change", "What I want to repeat", "Next small step"])
        b.closing("Useful beats", "perfect.", "Keep this template close to the moment it is useful. Print another copy when the page is full, and let the system get better as your life changes.")
        b.save()
        if kind == "bundle":
            xlsx=make_xlsx(meta,pdf);zip_path=OUT/f"{pid}-bundle.zip"
            with ZipFile(zip_path,"w",ZIP_DEFLATED) as z:z.write(pdf,pdf.name);z.write(xlsx,xlsx.name)
            pdf.unlink();xlsx.unlink()

if __name__ == "__main__": main()
