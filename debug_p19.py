import pdfplumber

pdf = pdfplumber.open(r"C:\Users\David\Downloads\Crime_In_Karnataka_2025.pdf")
page = pdf.pages[18]
words = page.extract_words()
mysuru_tops = sorted({round(w["top"], 1) for w in words if w["text"] == "Mysuru"})
print("Mysuru tops:", mysuru_tops)
for t in mysuru_tops:
    band = sorted(
        (w for w in words if abs(w["top"] - t) < 12),
        key=lambda w: w["x0"],
    )
    print(f"--- band top~{t} ---")
    for w in band:
        print(f"  {w['text']!r} top={w['top']:.1f} x0={w['x0']:.1f}")
pdf.close()
