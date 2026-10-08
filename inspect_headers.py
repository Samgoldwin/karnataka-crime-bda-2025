import pdfplumber

pdf = pdfplumber.open(r"C:\Users\David\Downloads\Crime_In_Karnataka_2025.pdf")

for pno in [38, 42, 46, 251, 272, 331]:
    page = pdf.pages[pno]
    words = page.extract_words()
    print(f"=== p{pno+1} ===")
    # print header-area words (top < 150)
    hdr = [w for w in words if w["top"] < 160]
    for w in sorted(hdr, key=lambda w: (round(w["top"]), w["x0"])):
        print(f"  y={w['top']:.0f} x={w['x0']:.0f}-{w['x1']:.0f} {w['text']!r}")
    print()
pdf.close()
