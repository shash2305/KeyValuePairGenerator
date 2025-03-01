from fpdf import FPDF

# Create PDF instance
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", size=12)

# Add title
pdf.set_font("Arial", style='B', size=16)
pdf.cell(200, 10, "Sample PDF Document", ln=True, align='C')
pdf.ln(10)

# Add text content
sample_text = """Ceci est un fichier PDF d'exemple pour tester l'extraction de texte.
Il contient plusieurs lignes de texte et différents formats.

Paires clé-valeur :
Nom : John Doe
Âge : 30
Profession : Ingénieur logiciel
Entreprise : OpenAI
"""

pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, sample_text)

# Save PDF file
pdf.output("test_document.pdf")

print("Test PDF created: test_document.pdf")
