import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import bcrypt
from PIL import Image, ImageTk
import os
import pathlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class AdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Administration Parking OACA")
        self.root.geometry("1200x800")
        
        # Configurer la fenêtre
        self.root.configure(bg='white')
        self.root.minsize(800, 600)
        
        # Définir les couleurs du thème
        self.colors = {
            'primary': '#1e3d8f',    # Bleu OACA
            'secondary': '#ffffff',  # Blanc
            'accent': '#f8f9fa',    # Gris très clair
            'text': '#2c3e50',      # Gris foncé
            'error': '#dc3545',     # Rouge
            'border': '#dee2e6',    # Gris clair pour bordures
            'hover': '#0056b3'      # Bleu hover
        }
        
        # Charger le logo OACA
        try:
            script_dir = pathlib.Path(__file__).parent.absolute()
            logo_path = os.path.join(script_dir, 'assets', 'logo_oaca.png')
            self.logo_image = Image.open(logo_path)
            # Redimensionner le logo
            self.logo_image = self.logo_image.resize((100, 50), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(self.logo_image)
        except Exception as e:
            print(f"Erreur lors du chargement du logo: {e}")
            self.logo_photo = None
        
        # Configurer le style
        self.setup_styles()
        
        # Variables pour le login
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        # Créer les frames
        self.login_frame = ttk.Frame(root, style='Card.TFrame')
        self.main_frame = ttk.Frame(root, style='Main.TFrame')
        
        # Initialiser l'interface de login
        self.setup_login_interface()
        
    def setup_styles(self):
        style = ttk.Style()
        
        # Configuration des styles généraux
        style.configure('Main.TFrame', background='white')
        style.configure('Card.TFrame', background='white')
        
        # Labels
        style.configure('Title.TLabel',
                      background='white',
                      foreground=self.colors['primary'],
                      font=('Helvetica', 24, 'bold'))
        style.configure('Label.TLabel',
                      background='white',
                      foreground=self.colors['text'],
                      font=('Helvetica', 12))
        style.configure('Error.TLabel',
                      background=self.colors['accent'],
                      foreground=self.colors['error'],
                      font=('Helvetica', 12))
        
        # Treeview pour l'historique
        style.configure('Treeview',
                      background='white',
                      fieldbackground='white',
                      foreground=self.colors['text'],
                      rowheight=30,
                      font=('Helvetica', 10))
        style.configure('Treeview.Heading',
                      background=self.colors['primary'],
                      foreground='white',
                      relief='flat',
                      font=('Helvetica', 10, 'bold'))
        style.map('Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
        
        # Style des boutons
        style.configure('Primary.TButton',
                      background=self.colors['primary'],
                      foreground=self.colors['secondary'],
                      padding=(20, 10),
                      font=('Helvetica', 12))
        
        # Style du Treeview
        style.configure('Treeview',
                      background=self.colors['secondary'],
                      foreground=self.colors['text'],
                      rowheight=25,
                      fieldbackground=self.colors['secondary'])
        style.configure('Treeview.Heading',
                      background=self.colors['primary'],
                      foreground=self.colors['secondary'],
                      font=('Helvetica', 10, 'bold'))
        
    def setup_login_interface(self):
        # Configuration du frame de login
        self.login_frame.place(relx=0.5, rely=0.5, anchor='center',
                             width=400, height=500)
        self.login_frame.configure(style='Card.TFrame')
        
        # Frame pour le logo et le titre
        logo_frame = ttk.Frame(self.login_frame, style='Card.TFrame')
        logo_frame.pack(fill='x', pady=(20, 0))
        
        # Ajouter le logo s'il est disponible
        if self.logo_photo:
            logo_label = ttk.Label(logo_frame, image=self.logo_photo, background='white')
            logo_label.pack(pady=(0, 10))
        
        # En-tête avec logo OACA
        header_frame = ttk.Frame(self.login_frame, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Titre
        title = ttk.Label(header_frame, 
                         text="Administration Parking OACA",
                         style='Title.TLabel')
        title.pack(pady=20)
        
        # Sous-titre
        subtitle = ttk.Label(header_frame,
                           text="Bienvenue • مرحبا • Welcome",
                           style='Header.TLabel')
        subtitle.pack(pady=(0, 20))
        
        # Message de connexion
        login_message = ttk.Label(self.login_frame, 
                                text="Please log in to access this page.",
                                style='Error.TLabel')
        login_message.pack(pady=10, padx=20)
        
        # Frame pour le formulaire
        form_frame = ttk.Frame(self.login_frame, style='Card.TFrame')
        form_frame.pack(fill='x', padx=20, pady=10)
        
        # Conteneur intérieur avec padding
        inner_frame = ttk.Frame(form_frame, style='Card.TFrame')
        inner_frame.pack(fill='x', padx=20, pady=20)
        
        # Username
        ttk.Label(inner_frame, text="Nom d'utilisateur",
                 style='Label.TLabel').pack(fill='x', pady=(0, 5))
        username_entry = ttk.Entry(inner_frame,
                                 textvariable=self.username_var,
                                 font=('Helvetica', 12))
        username_entry.pack(fill='x', pady=(0, 15))
        username_entry.configure(background='white')
        
        # Password
        ttk.Label(inner_frame, text="Mot de passe",
                 style='Label.TLabel').pack(fill='x', pady=(0, 5))
        password_entry = ttk.Entry(inner_frame,
                                 textvariable=self.password_var,
                                 show="•",
                                 font=('Helvetica', 12))
        password_entry.pack(fill='x', pady=(0, 20))
        password_entry.configure(background='white')
        
        # Bouton de connexion
        login_button = tk.Button(inner_frame,
                             text="Se connecter",
                             command=self.login,
                             font=('Helvetica', 12),
                             bg=self.colors['primary'],
                             fg='white',
                             cursor='hand2',
                             relief='flat',
                             width=20)
        login_button.pack(pady=(10, 20))
        
        # Effet hover sur le bouton
        def on_enter(e):
            login_button['background'] = self.colors['hover']
        def on_leave(e):
            login_button['background'] = self.colors['primary']
        
        login_button.bind('<Enter>', on_enter)
        login_button.bind('<Leave>', on_leave)
        
        # Message d'erreur
        self.error_label = ttk.Label(form_frame, text="", foreground="red")
        self.error_label.pack(pady=10)
        
        # Afficher le frame de login
        self.login_frame.pack(fill='both', expand=True)
        
    def setup_main_interface(self):
        # Cacher le frame de login
        self.login_frame.pack_forget()
        
        # Style
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Helvetica', 24, 'bold'))
        
        # Frame principal avec notebook pour les onglets
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Onglet Historique
        self.historique_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.historique_frame, text='Historique')
        
        # Onglet Statistiques
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='Statistiques')
        
        # Setup des onglets
        self.setup_historique_tab()
        self.setup_stats_tab()
        
        # Afficher le frame principal
        self.main_frame.pack(fill='both', expand=True)
        
    def setup_historique_tab(self):
        # Frame principal avec padding et fond blanc
        main_container = ttk.Frame(self.historique_frame, style='Card.TFrame')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre de la section
        title_frame = ttk.Frame(main_container, style='Card.TFrame')
        title_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(title_frame, text="Historique des Stationnements",
                 style='Title.TLabel').pack(side='left')
        
        # Frame pour les filtres avec style moderne
        filter_frame = ttk.Frame(main_container, style='Card.TFrame')
        filter_frame.pack(fill='x', pady=(0, 20))
        
        # Filtres rapides
        ttk.Button(filter_frame, text="Aujourd'hui", 
                  command=lambda: self.filter_date('today')).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Cette semaine", 
                  command=lambda: self.filter_date('week')).pack(side='left', padx=5)
        ttk.Button(filter_frame, text="Ce mois", 
                  command=lambda: self.filter_date('month')).pack(side='left', padx=5)
        
        # Séparateur
        ttk.Label(filter_frame, text="  |  ").pack(side='left', padx=5)
        
        # Date de début
        ttk.Label(filter_frame, text="Du:").pack(side='left', padx=5)
        self.date_debut = DateEntry(filter_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.date_debut.pack(side='left', padx=5)
        
        # Date de fin
        ttk.Label(filter_frame, text="Au:").pack(side='left', padx=5)
        self.date_fin = DateEntry(filter_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.date_fin.pack(side='left', padx=5)
        
        # Bouton de recherche
        ttk.Button(filter_frame, text="Rechercher", 
                  command=self.rechercher).pack(side='left', padx=20)
        
        # Treeview pour l'historique
        self.tree = ttk.Treeview(self.historique_frame, columns=(
            "id", "plaque", "place", "temps_entree", "temps_sortie",
            "duree_minutes", "montant", "status_paiement"
        ), show='headings')
        
        # Définir les en-têtes
        self.tree.heading("id", text="ID")
        self.tree.heading("plaque", text="N° Plaque")
        self.tree.heading("place", text="Place")
        self.tree.heading("temps_entree", text="Entrée")
        self.tree.heading("temps_sortie", text="Sortie")
        self.tree.heading("duree_minutes", text="Durée (min)")
        self.tree.heading("montant", text="Montant (DT)")
        self.tree.heading("status_paiement", text="Statut")
        
        # Définir les largeurs des colonnes
        self.tree.column("id", width=50)
        self.tree.column("plaque", width=150)
        self.tree.column("place", width=80)
        self.tree.column("temps_entree", width=150)
        self.tree.column("temps_sortie", width=150)
        self.tree.column("duree_minutes", width=100)
        self.tree.column("montant", width=100)
        self.tree.column("status_paiement", width=100)
        
        # Ajouter une scrollbar
        scrollbar = ttk.Scrollbar(self.historique_frame, orient="vertical", 
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Placer le treeview et la scrollbar
        self.tree.pack(side='left', fill='both', expand=True, padx=20, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)
    
    def setup_stats_tab(self):
        # Frame principal pour les statistiques
        main_stats_frame = ttk.Frame(self.stats_frame, style='Card.TFrame')
        main_stats_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre
        title_frame = ttk.Frame(main_stats_frame, style='Card.TFrame')
        title_frame.pack(fill='x', pady=(0, 20))
        ttk.Label(title_frame, text="Tableau de Bord",
                 style='Title.TLabel').pack(side='left')
        
        # Frame pour les cartes de statistiques
        cards_frame = ttk.Frame(main_stats_frame, style='Card.TFrame')
        cards_frame.pack(fill='x', pady=(0, 20))
        
        # Création des cartes de statistiques
        self.create_stat_card(cards_frame, "Véhicules Total", "0", 0)
        self.create_stat_card(cards_frame, "Revenu Total (DT)", "0.00", 1)
        self.create_stat_card(cards_frame, "Durée Moyenne (min)", "0", 2)
        
        # Frame pour les graphiques
        graphs_frame = ttk.Frame(main_stats_frame, style='Card.TFrame')
        graphs_frame.pack(fill='both', expand=True)
        
        # Création des graphiques
        self.create_graphs(graphs_frame)
        
        # Bouton pour rafraîchir
        refresh_frame = ttk.Frame(main_stats_frame, style='Card.TFrame')
        refresh_frame.pack(fill='x', pady=20)
        ttk.Button(refresh_frame, 
                  text="Rafraîchir les statistiques",
                  command=self.update_stats,
                  style='Primary.TButton').pack()
    
    def create_stat_card(self, parent, title, value, position):
        # Créer une carte pour une statistique
        card = ttk.Frame(parent, style='Card.TFrame')
        card.grid(row=0, column=position, padx=10, sticky='nsew')
        
        # Configurer le grid
        parent.grid_columnconfigure(position, weight=1)
        
        # Ajouter un style de bordure
        card_inner = ttk.Frame(card, style='Card.TFrame')
        card_inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Titre de la carte
        title_label = ttk.Label(card_inner, 
                              text=title,
                              style='Label.TLabel')
        title_label.pack()
        
        # Valeur
        if title == "Véhicules Total":
            self.total_vehicules_label = ttk.Label(card_inner,
                text=value,
                font=('Helvetica', 24, 'bold'),
                foreground=self.colors['primary'])
            self.total_vehicules_label.pack(pady=10)
        elif title == "Revenu Total (DT)":
            self.revenu_total_label = ttk.Label(card_inner,
                text=value,
                font=('Helvetica', 24, 'bold'),
                foreground=self.colors['primary'])
            self.revenu_total_label.pack(pady=10)
        else:
            self.duree_moyenne_label = ttk.Label(card_inner,
                text=value,
                font=('Helvetica', 24, 'bold'),
                foreground=self.colors['primary'])
            self.duree_moyenne_label.pack(pady=10)
    
    def create_graphs(self, parent):
        # Frame pour les graphiques
        graphs_container = ttk.Frame(parent, style='Card.TFrame')
        graphs_container.pack(fill='both', expand=True)
        
        # Créer deux colonnes pour les graphiques
        left_frame = ttk.Frame(graphs_container, style='Card.TFrame')
        left_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        right_frame = ttk.Frame(graphs_container, style='Card.TFrame')
        right_frame.pack(side='right', fill='both', expand=True, padx=10)
        
        # Graphique circulaire pour la répartition des places
        self.pie_figure = Figure(figsize=(6, 4))
        self.pie_canvas = FigureCanvasTkAgg(self.pie_figure, left_frame)
        self.pie_canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Graphique en barres pour les revenus
        self.bar_figure = Figure(figsize=(6, 4))
        self.bar_canvas = FigureCanvasTkAgg(self.bar_figure, right_frame)
        self.bar_canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def update_stats(self):
        try:
            # Connexion à MySQL
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='parking_db'
            )
            cursor = conn.cursor()
            
            # Nombre total de véhicules
            cursor.execute("SELECT COUNT(*) FROM historique_stationnement")
            total_vehicules = cursor.fetchone()[0]
            
            # Revenu total
            cursor.execute("SELECT SUM(montant) FROM historique_stationnement")
            revenu_total = cursor.fetchone()[0] or 0
            
            # Durée moyenne
            cursor.execute("SELECT AVG(duree_minutes) FROM historique_stationnement")
            duree_moyenne = cursor.fetchone()[0] or 0
            
            # Mettre à jour les cartes
            self.total_vehicules_label.config(text=str(total_vehicules))
            self.revenu_total_label.config(text=f"{revenu_total:.2f}")
            self.duree_moyenne_label.config(text=f"{duree_moyenne:.1f}")
            
            # Mise à jour du graphique circulaire
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN status_paiement = 'Payé' THEN 'Payé'
                        ELSE 'Non Payé'
                    END as status,
                    COUNT(*) as count
                FROM historique_stationnement
                GROUP BY status_paiement
            """)
            status_data = cursor.fetchall()
            
            # Préparation des données pour le graphique circulaire
            labels = [row[0] for row in status_data]
            sizes = [row[1] for row in status_data]
            
            # Création du graphique circulaire
            self.pie_figure.clear()
            ax = self.pie_figure.add_subplot(111)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#2ecc71', '#e74c3c'])
            ax.set_title('Répartition des Paiements')
            
            # Mise à jour du graphique en barres
            cursor.execute("""
                SELECT DATE(temps_entree) as date, SUM(montant) as total
                FROM historique_stationnement
                WHERE temps_entree >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(temps_entree)
                ORDER BY date
            """)
            revenue_data = cursor.fetchall()
            
            # Préparation des données pour le graphique en barres
            dates = [row[0].strftime('%d/%m') for row in revenue_data]
            revenues = [float(row[1]) for row in revenue_data]
            
            # Création du graphique en barres
            self.bar_figure.clear()
            ax = self.bar_figure.add_subplot(111)
            bars = ax.bar(dates, revenues, color=self.colors['primary'])
            ax.set_title('Revenus des 7 derniers jours')
            ax.set_xlabel('Date')
            ax.set_ylabel('Revenu (DT)')
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Ajout des valeurs sur les barres
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}',
                        ha='center', va='bottom')
            
            # Ajuster la mise en page
            self.bar_figure.tight_layout()
            
            # Rafraîchir les graphiques
            self.pie_canvas.draw()
            self.bar_canvas.draw()
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour des statistiques: {str(e)}")
    
    def filter_date(self, period):
        today = datetime.now().date()
        if period == 'today':
            self.date_debut.set_date(today)
            self.date_fin.set_date(today)
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            self.date_debut.set_date(start)
            self.date_fin.set_date(today)
        elif period == 'month':
            start = today.replace(day=1)
            self.date_debut.set_date(start)
            self.date_fin.set_date(today)
        self.rechercher()
    
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        # Vérifier les credentials (à remplacer par votre logique d'authentification)
        if username == "admin" and password == "admin":  # À remplacer par une vraie vérification
            self.setup_main_interface()
        else:
            self.error_label.config(text="Nom d'utilisateur ou mot de passe incorrect")
    
    def rechercher(self):
        try:
            # Vider le treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Connexion à MySQL
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='root',
                database='parking_db'
            )
            cursor = conn.cursor()
            
            # Récupérer les données
            cursor.execute('''
            SELECT id, plaque, place, temps_entree, temps_sortie,
                   duree_minutes, montant, status_paiement
            FROM historique_stationnement
            WHERE date(temps_entree) BETWEEN date(?) AND date(?)
            ORDER BY temps_entree DESC
            ''', (self.date_debut.get_date(), self.date_fin.get_date()))
            
            # Ajouter les données au treeview
            for row in cursor.fetchall():
                # Formater les dates
                temps_entree = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y %H:%M')
                temps_sortie = datetime.strptime(row[4], '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y %H:%M')
                
                self.tree.insert('', 'end', values=(
                    row[0], row[1], row[2], temps_entree, temps_sortie,
                    f"{row[5]:.1f}", f"{row[6]:.2f}", row[7]
                ))
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AdminDashboard(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors du démarrage de l'application: {str(e)}") 