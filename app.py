import flet as ft
import sqlite3
import os
import shutil
from fpdf import FPDF
from datetime import datetime

NOM_BOUTIQUE = "NAS-GUTI-HAZ GALADIMA"
TEL_BOUTIQUE = "Tel : 98883878"

BASE_DIR = os.path.expanduser("~/Documents/GaladimaManager")
DB_PATH = os.path.join(BASE_DIR, "atelier.db")
FACTURES_DIR = os.path.join(BASE_DIR, "factures")
RECUS_DIR = os.path.join(BASE_DIR, "recus")
SAUVEGARDES_DIR = os.path.join(BASE_DIR, "sauvegardes")

BLEU = "#1E3A5F"
OR = "#D4AF37"
GRIS = "#F5F7FA"

def connecter():
    return sqlite3.connect(DB_PATH)

def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(FACTURES_DIR, exist_ok=True)
    os.makedirs(RECUS_DIR, exist_ok=True)
    os.makedirs(SAUVEGARDES_DIR, exist_ok=True)
    conn = connecter()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS vendeurs (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, telephone TEXT, cni TEXT, adresse TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, telephone TEXT, adresse TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS appareils (id INTEGER PRIMARY KEY AUTOINCREMENT, imei TEXT UNIQUE, marque TEXT, modele TEXT, etat TEXT, prix_achat INTEGER, vendeur_id INTEGER, date_achat TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS reparations (id INTEGER PRIMARY KEY AUTOINCREMENT, appareil_id INTEGER, description TEXT, cout_pieces INTEGER, cout_main_oeuvre INTEGER, date_debut TEXT, date_fin TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS ventes (id INTEGER PRIMARY KEY AUTOINCREMENT, appareil_id INTEGER, client_id INTEGER, prix_vente INTEGER, date_vente TEXT, garantie_mois INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS mouvements (id INTEGER PRIMARY KEY AUTOINCREMENT, appareil_id INTEGER, type TEXT, date TEXT, notes TEXT)")
    conn.commit()
    conn.close()

def pdf_facture(client_nom, client_tel, marque, modele, imei, prix, date_v, garantie):
    p = FPDF(orientation="P", unit="mm", format=(58, 150))
    p.add_page()
    p.set_margins(2, 2, 2)
    p.set_font("Helvetica", "B", 10)
    p.cell(0, 5, NOM_BOUTIQUE, ln=True, align="C")
    p.set_font("Helvetica", "", 8)
    p.cell(0, 5, TEL_BOUTIQUE, ln=True, align="C")
    p.cell(0, 5, "FACTURE DE VENTE", ln=True, align="C")
    p.ln(2)
    p.cell(0, 5, "-" * 26, ln=True, align="C")
    p.ln(2)
    p.cell(0, 5, f"Date : {date_v}", ln=True)
    p.cell(0, 5, f"Client : {client_nom}", ln=True)
    p.cell(0, 5, f"Tel : {client_tel}", ln=True)
    p.ln(2)
    p.cell(0, 5, f"Appareil : {marque} {modele}", ln=True)
    p.cell(0, 5, f"IMEI : {imei}", ln=True)
    p.ln(2)
    p.cell(0, 5, "-" * 26, ln=True, align="C")
    p.ln(2)
    p.set_font("Helvetica", "B", 10)
    p.cell(0, 5, f"Prix : {prix} FCFA", ln=True)
    p.set_font("Helvetica", "", 8)
    p.cell(0, 5, f"Garantie : {garantie} mois", ln=True)
    p.ln(5)
    p.cell(0, 5, "Merci pour votre confiance !", ln=True, align="C")
    p.output(os.path.join(FACTURES_DIR, f"facture_{imei}.pdf"))

def pdf_recu(marque, modele, imei, panne, pieces, main):
    total = int(pieces) + int(main)
    p = FPDF(orientation="P", unit="mm", format=(58, 150))
    p.add_page()
    p.set_margins(2, 2, 2)
    p.set_font("Helvetica", "B", 10)
    p.cell(0, 5, NOM_BOUTIQUE, ln=True, align="C")
    p.set_font("Helvetica", "", 8)
    p.cell(0, 5, TEL_BOUTIQUE, ln=True, align="C")
    p.cell(0, 5, "RECU DE REPARATION", ln=True, align="C")
    p.ln(2)
    p.cell(0, 5, "-" * 26, ln=True, align="C")
    p.ln(2)
    p.cell(0, 5, f"Appareil : {marque} {modele}", ln=True)
    p.cell(0, 5, f"IMEI : {imei}", ln=True)
    p.ln(2)
    p.cell(0, 5, f"Panne : {panne}", ln=True)
    p.ln(2)
    p.cell(0, 5, "-" * 26, ln=True, align="C")
    p.ln(2)
    p.cell(0, 5, f"Pieces : {pieces} FCFA", ln=True)
    p.cell(0, 5, f"Main d'oeuvre : {main} FCFA", ln=True)
    p.set_font("Helvetica", "B", 10)
    p.cell(0, 5, f"TOTAL : {total} FCFA", ln=True)
    p.output(os.path.join(RECUS_DIR, f"recu_{imei}.pdf"))

def main(page: ft.Page):
    page.title = NOM_BOUTIQUE
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = GRIS
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    def snack(msg, color="green"):
        page.open(ft.SnackBar(ft.Text(msg, color="white"), bgcolor=color))

    def champ(label, **kw):
        return ft.TextField(label=label, border_color=BLEU, focused_border_color=OR, **kw)

    # --- FORMULAIRES ---
    def form_vendeur(e):
        n, t, c, a = champ("Nom", autofocus=True), champ("Téléphone"), champ("N° CNI"), champ("Adresse")
        def save(e):
            if not n.value: return snack("Le nom est obligatoire", "red")
            conn = connecter(); cur = conn.cursor()
            cur.execute("INSERT INTO vendeurs (nom, telephone, cni, adresse) VALUES (?,?,?,?)", (n.value, t.value, c.value, a.value))
            conn.commit(); conn.close()
            page.close(dlg); snack(f"Vendeur {n.value} ajouté")
        dlg = ft.AlertDialog(title=ft.Text("Nouveau vendeur"),
            content=ft.Column([n, t, c, a], tight=True, width=320, spacing=10),
            actions=[ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                     ft.FilledButton("Enregistrer", on_click=save, bgcolor=BLEU)])
        page.open(dlg)

    def form_client(e):
        n, t, a = champ("Nom", autofocus=True), champ("Téléphone"), champ("Adresse")
        def save(e):
            if not n.value: return snack("Le nom est obligatoire", "red")
            conn = connecter(); cur = conn.cursor()
            cur.execute("INSERT INTO clients (nom, telephone, adresse) VALUES (?,?,?)", (n.value, t.value, a.value))
            conn.commit(); conn.close()
            page.close(dlg); snack(f"Client {n.value} ajouté")
        dlg = ft.AlertDialog(title=ft.Text("Nouveau client"),
            content=ft.Column([n, t, a], tight=True, width=320, spacing=10),
            actions=[ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                     ft.FilledButton("Enregistrer", on_click=save, bgcolor=BLEU)])
        page.open(dlg)

    def form_achat(e):
        im = champ("IMEI"); ma = champ("Marque"); mo = champ("Modèle")
        et = champ("État (brut/pret/vendu)", value="brut")
        pr = champ("Prix d'achat (FCFA)", keyboard_type=ft.KeyboardType.NUMBER)
        vi = champ("ID du vendeur", keyboard_type=ft.KeyboardType.NUMBER)
        def save(e):
            if not im.value or not ma.value: return snack("IMEI et Marque obligatoires", "red")
            try:
                conn = connecter(); cur = conn.cursor()
                cur.execute("INSERT INTO appareils (imei, marque, modele, etat, prix_achat, vendeur_id, date_achat) VALUES (?,?,?,?,?,?,date('now'))",
                            (im.value, ma.value, mo.value, et.value, pr.value, vi.value))
                app_id = cur.lastrowid
                cur.execute("INSERT INTO mouvements (appareil_id, type, date, notes) VALUES (?, 'achat', date('now'), 'Achat')", (app_id,))
                conn.commit(); conn.close()
                page.close(dlg); snack(f"{ma.value} {mo.value} ajouté au stock")
            except Exception as ex:
                snack(f"Erreur : {ex}", "red")
        dlg = ft.AlertDialog(title=ft.Text("Nouveau téléphone (achat)"),
            content=ft.Column([im, ma, mo, et, pr, vi], tight=True, width=320, spacing=10, scroll=ft.ScrollMode.AUTO),
            actions=[ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                     ft.FilledButton("Enregistrer", on_click=save, bgcolor=BLEU)])
        page.open(dlg)

    def form_vente(e):
        ap = champ("ID du téléphone", keyboard_type=ft.KeyboardType.NUMBER)
        cl = champ("ID du client", keyboard_type=ft.KeyboardType.NUMBER)
        pv = champ("Prix de vente (FCFA)", keyboard_type=ft.KeyboardType.NUMBER)
        ga = champ("Garantie (mois)", keyboard_type=ft.KeyboardType.NUMBER, value="3")
        def save(e):
            conn = connecter(); cur = conn.cursor()
            cur.execute("SELECT a.marque, a.modele, a.imei, c.nom, c.telephone FROM appareils a, clients c WHERE a.id=? AND c.id=?", (ap.value, cl.value))
            infos = cur.fetchone()
            if not infos:
                conn.close(); return snack("ID téléphone ou client introuvable", "red")
            marque, modele, imei, cn, ct = infos
            cur.execute("INSERT INTO ventes (appareil_id, client_id, prix_vente, date_vente, garantie_mois) VALUES (?,?,?,date('now'),?)",
                        (ap.value, cl.value, pv.value, ga.value))
            cur.execute("UPDATE appareils SET etat='vendu' WHERE id=?", (ap.value,))
            cur.execute("INSERT INTO mouvements (appareil_id, type, date, notes) VALUES (?, 'vente', date('now'), 'Vente')", (ap.value,))
            conn.commit(); conn.close()
            date_v = datetime.now().strftime("%d/%m/%Y")
            pdf_facture(cn, ct, marque, modele, imei, pv.value, date_v, ga.value)
            page.close(dlg); snack(f"Vente enregistrée. Facture générée.")
        dlg = ft.AlertDialog(title=ft.Text("Vendre un téléphone"),
            content=ft.Column([ap, cl, pv, ga], tight=True, width=320, spacing=10),
            actions=[ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                     ft.FilledButton("Valider la vente", on_click=save, bgcolor=BLEU)])
        page.open(dlg)

    def form_reparation(e):
        ap = champ("ID du téléphone", keyboard_type=ft.KeyboardType.NUMBER)
        de = champ("Panne décrite")
        cp = champ("Coût des pièces (FCFA)", keyboard_type=ft.KeyboardType.NUMBER)
        cm = champ("Main d'œuvre (FCFA)", keyboard_type=ft.KeyboardType.NUMBER)
        def save(e):
            conn = connecter(); cur = conn.cursor()
            cur.execute("SELECT marque, modele, imei FROM appareils WHERE id=?", (ap.value,))
            infos = cur.fetchone()
            if not infos:
                conn.close(); return snack("ID téléphone introuvable", "red")
            ma, mo, im = infos
            cur.execute("INSERT INTO reparations (appareil_id, description, cout_pieces, cout_main_oeuvre, date_debut) VALUES (?,?,?,?,date('now'))",
                        (ap.value, de.value, cp.value, cm.value))
            cur.execute("UPDATE appareils SET etat='en reparation' WHERE id=?", (ap.value,))
            cur.execute("INSERT INTO mouvements (appareil_id, type, date, notes) VALUES (?, 'reparation', date('now'), 'Reparation')", (ap.value,))
            conn.commit(); conn.close()
            pdf_recu(ma, mo, im, de.value, cp.value, cm.value)
            page.close(dlg); snack(f"Réparation enregistrée. Reçu généré.")
        dlg = ft.AlertDialog(title=ft.Text("Nouvelle réparation"),
            content=ft.Column([ap, de, cp, cm], tight=True, width=320, spacing=10),
            actions=[ft.TextButton("Annuler", on_click=lambda e: page.close(dlg)),
                     ft.FilledButton("Enregistrer", on_click=save, bgcolor=BLEU)])
        page.open(dlg)

    # --- LISTES ---
    def liste_generique(titre, requete, entetes):
        conn = connecter(); cur = conn.cursor()
        cur.execute(requete); rows = cur.fetchall(); conn.close()
        rows_ui = [ft.DataRow(cells=[ft.DataCell(ft.Text(str(c))) for c in r]) for r in rows]
        table = ft.DataTable(columns=[ft.DataColumn(ft.Text(h, weight=ft.FontWeight.BOLD)) for h in entetes],
                             rows=rows_ui, border=ft.border.all(1, BLEU), border_radius=8)
        dlg = ft.AlertDialog(title=ft.Text(titre),
            content=ft.Container(content=ft.Column([table], scroll=ft.ScrollMode.AUTO), width=380, height=400),
            actions=[ft.TextButton("Fermer", on_click=lambda e: page.close(dlg))])
        page.open(dlg)

    def voir_vendeurs(e):
        liste_generique("Vendeurs", "SELECT id, nom, telephone FROM vendeurs", ["ID", "Nom", "Téléphone"])

    def voir_clients(e):
        liste_generique("Clients", "SELECT id, nom, telephone FROM clients", ["ID", "Nom", "Téléphone"])

    def voir_stock(e):
        liste_generique("Stock téléphones",
            "SELECT a.id, a.marque, a.modele, a.etat, a.prix_achat FROM appareils a",
            ["ID", "Marque", "Modèle", "État", "Prix"])

    def voir_reparations(e):
        liste_generique("Réparations",
            "SELECT r.id, a.marque, a.modele, r.description, r.date_debut FROM reparations r JOIN appareils a ON r.appareil_id=a.id",
            ["ID", "Marque", "Modèle", "Panne", "Date"])

    def voir_ventes(e):
        liste_generique("Ventes",
            "SELECT v.id, a.marque, a.modele, c.nom, v.prix_vente FROM ventes v JOIN appareils a ON v.appareil_id=a.id JOIN clients c ON v.client_id=c.id",
            ["ID", "Marque", "Modèle", "Client", "Prix"])

    def sauvegarder(e):
        if not os.path.exists(DB_PATH): return snack("Aucune base de données", "red")
        dh = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nom = os.path.join(SAUVEGARDES_DIR, f"atelier_{dh}.db")
        shutil.copy(DB_PATH, nom)
        snack(f"Sauvegarde créée")

    # --- CARTES D'ACTION ---
    def carte(icone, titre, sous_titre, action, couleur=BLEU):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icone, size=36, color=couleur),
                ft.Text(titre, size=15, weight=ft.FontWeight.BOLD, color=BLEU, text_align=ft.TextAlign.CENTER),
                ft.Text(sous_titre, size=10, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            width=160, height=130, bgcolor="white", border_radius=15,
            alignment=ft.alignment.center, on_click=action, ink=True,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black")),
        )

    # --- MISE EN PAGE ---
    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.STORE, size=50, color=OR),
            ft.Column([
                ft.Text(NOM_BOUTIQUE, size=18, weight=ft.FontWeight.BOLD, color=BLEU),
                ft.Text(TEL_BOUTIQUE, size=12, color=ft.Colors.GREY_700),
                ft.Text("Gestion d'atelier & ventes", size=11, color=OR, italic=True),
            ], spacing=2),
        ], spacing=15),
        padding=15, bgcolor="white", border_radius=12,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.with_opacity(0.1, "black")),
    )

    grille = ft.Column([
        ft.Row([carte(ft.Icons.ADD_BUSINESS, "ACHAT", "Ajouter un vendeur", form_vendeur),
                carte(ft.Icons.PERSON_ADD, "CLIENT", "Ajouter un client", form_client)], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Row([carte(ft.Icons.PHONE_ANDROID, "NOUVEAU", "Ajouter au stock", form_achat),
                carte(ft.Icons.SELL, "VENTE", "Vendre + facture", form_vente)], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Row([carte(ft.Icons.BUILD, "RÉPARER", "Nouvelle réparation", form_reparation),
                carte(ft.Icons.INVENTORY, "STOCK", "Voir les téléphones", voir_stock)], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Row([carte(ft.Icons.PEOPLE, "VENDEURS", "Voir la liste", voir_vendeurs),
                carte(ft.Icons.PERSON, "CLIENTS", "Voir la liste", voir_clients)], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Row([carte(ft.Icons.HISTORY, "RÉPARATIONS", "Voir l'historique", voir_reparations),
                carte(ft.Icons.RECEIPT_LONG, "VENTES", "Voir l'historique", voir_ventes)], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
        ft.Row([carte(ft.Icons.SAVE, "SAUVEGARDER", "Protéger les données", sauvegarder, OR),
                carte(ft.Icons.EXIT_TO_APP, "QUITTER", "Fermer l'application", lambda e: page.window_close(), "#C0392B")], alignment=ft.MainAxisAlignment.CENTER, spacing=15),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    page.add(header, ft.Container(height=10), grille)

if __name__ == "__main__":
    init_db()
    ft.app(target=main)
