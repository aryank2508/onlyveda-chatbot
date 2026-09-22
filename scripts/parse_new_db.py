"""Parse the new disease/treatment Excel and display all unique diseases + products."""
import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\aryan\Desktop\onlyveda_chatbot\disease and treatment database (2).xlsx')
ws = wb['Sheet1']

rows = []
for row in ws.iter_rows(min_row=2, values_only=True):
    if any(cell is not None and str(cell).strip() for cell in row):
        rows.append(row)

print(f"Total data rows: {len(rows)}")

diseases = {}
for row in rows:
    cat = str(row[0] or '').strip().rstrip('\xa0')
    disease = str(row[1] or '').strip().rstrip('\xa0')
    product = str(row[3] or '').strip()
    dose = str(row[4] or '').strip() if row[4] else ''
    if not disease:
        continue
    if disease not in diseases:
        diseases[disease] = {'category': cat, 'products': []}
    if product:
        diseases[disease]['products'].append({'product': product, 'dose': dose})

print(f"Unique diseases: {len(diseases)}")
for d, info in diseases.items():
    prods = [p['product'] + ' (' + p['dose'] + ')' for p in info['products']]
    print(f"  [{info['category']}] {d}:")
    for p in prods:
        print(f"    -> {p}")
