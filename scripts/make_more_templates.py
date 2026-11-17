from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from make_paid_templates import OUT, PDF, make_xlsx

MORE = [
("study-planner", "Study Sprint Planner", "Education", "A focused study system for turning a big syllabus into calm, trackable sessions.", 149, "Education", "photo-1434030216411-0b793f4b4173", "pdf"),
("reading-journal", "Reading Journal", "Lifestyle", "A beautiful place to collect ideas, favourite lines and the books that stay with you.", 99, "Lifestyle", "photo-1512820790803-83ca734da794", "pdf"),
("wedding-planner", "Wedding Planning Budget", "Finance", "Keep the joy in the planning with a practical budget, vendor list and payment calendar.", 299, "Finance", "photo-1519741497674-611481863552", "bundle"),
("travel-planner", "Travel Itinerary Planner", "Travel", "Map the details without overplanning the magic: stays, routes, reservations and room to wander.", 199, "Travel", "photo-1488646953014-85cb44e25828", "pdf"),
("moving-home", "Moving Home Checklist", "Home", "A room-by-room move plan for packing, changing addresses and settling in without the scramble.", 149, "Home", "photo-1600585154340-be6161a56a0c", "pdf"),
("pet-care", "Pet Care Tracker", "Home", "Keep routines, appointments, medications and the little details of caring for your companion together.", 129, "Home", "photo-1450778869180-41d0601e046e", "pdf"),
("fitness-log", "Gentle Fitness Log", "Wellbeing", "Track movement, energy and recovery without turning your body into a performance report.", 149, "Wellbeing", "photo-1534438327276-14e5300c3a48", "pdf"),
("digital-detox", "Digital Detox Planner", "Wellbeing", "A thoughtful reset for your attention, notifications and the parts of your day you want back.", 99, "Wellbeing", "photo-1516321318423-f06f85e504b3", "pdf"),
("gift-planner", "Gift Planning List", "Lifestyle", "Remember birthdays, ideas, budgets and the thoughtful details that make gifts feel personal.", 99, "Lifestyle", "photo-1513885535751-8b9238bd345a", "pdf"),
("course-launch", "Course Launch Planner", "Business", "Turn your knowledge into a clear launch plan with lessons, emails, content and a kinder timeline.", 299, "Business", "photo-1523240795612-9a054b0db644", "bundle"),
]

def build(meta):
    pid,title,cat,desc,price,tag,img,kind=meta
    pdf=OUT/f"{pid}.pdf";b=PDF(pdf,title);b.desc=desc;b.title=title;b.cover(f"{tag}  ·  {cat}")
    b.standard_page("Start here",desc,["Make it useful","one clear step at a time.","What matters most","What I know already","What needs a decision","The next small action","A note to future me"])
    b.table_page("Keep it visible",["Date","Focus","Next action","Status","Notes"],8)
    b.standard_page("The review","Use this page at the end of the week to keep what worked and change what did not.",["Keep the useful","leave the rest.","What worked","What felt heavy","What I want to repeat","What I will simplify","Next week begins with"])
    b.closing("Useful beats","perfect.","Return to this template whenever the details feel noisy. A good system should give your attention back to the thing you care about.")
    b.save()
    if kind=="bundle":
        xlsx=make_xlsx(meta,pdf);zip_path=OUT/f"{pid}-bundle.zip"
        with ZipFile(zip_path,"w",ZIP_DEFLATED) as z:z.write(pdf,pdf.name);z.write(xlsx,xlsx.name)
        pdf.unlink();xlsx.unlink()

if __name__=="__main__":
    OUT.mkdir(exist_ok=True)
    for item in MORE: build(item)
    print("created",len(MORE),"more templates")
