## Catalogue PyQt5 branché sur l'API FastAPI d'app-db-config.

import json
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"
DEFAULT_API_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 5.0
COLONNES = ["Nom", "Marque", "Catégorie", "Prix", "Stock"]


def charger_configuration() -> dict:
    """Lit config.json, avec des valeurs par défaut si le fichier manque."""
    configuration = {
        "api_base_url": DEFAULT_API_URL,
        "timeout_seconds": DEFAULT_TIMEOUT,
    }
    try:
        contenu = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return configuration

    if not isinstance(contenu, dict):
        return configuration

    url = contenu.get("api_base_url")
    if isinstance(url, str) and url.strip():
        configuration["api_base_url"] = url.strip().rstrip("/")

    timeout = contenu.get("timeout_seconds")
    if (
        isinstance(timeout, (int, float))
        and not isinstance(timeout, bool)
        and timeout > 0
    ):
        configuration["timeout_seconds"] = float(timeout)

    return configuration


def normaliser(texte: str) -> str:
    """Minuscules sans accents, pour une recherche tolérante."""
    decompose = unicodedata.normalize("NFKD", texte)
    return "".join(
        caractere
        for caractere in decompose
        if not unicodedata.combining(caractere)
    ).casefold()


def formater_prix(valeur: float) -> str:
    """1199.0 -> '1 199,00 €'."""
    return f"{valeur:,.2f} €".replace(",", " ").replace(".", ",")


class ApiWorker(QThread):
    """Récupère les produits dans un thread pour ne pas figer la fenêtre."""

    produits_recus = pyqtSignal(list)
    erreur = pyqtSignal(str)

    def __init__(self, url: str, timeout: float, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.timeout = timeout

    def run(self) -> None:
        try:
            requete = urllib.request.Request(
                self.url, headers={"Accept": "application/json"}
            )
            with urllib.request.urlopen(requete, timeout=self.timeout) as reponse:
                corps = reponse.read().decode("utf-8")

            donnees = json.loads(corps)
            produits = (
                donnees.get("produits", []) if isinstance(donnees, dict) else donnees
            )
            if not isinstance(produits, list):
                raise ValueError("la réponse ne contient pas de liste de produits")

            self.produits_recus.emit(produits)
        except urllib.error.HTTPError as exc:
            self.erreur.emit(f"erreur HTTP {exc.code} ({exc.reason})")
        except TimeoutError:
            self.erreur.emit(f"délai dépassé ({self.timeout:.0f} s)")
        except urllib.error.URLError as exc:
            self.erreur.emit(f"API injoignable ({exc.reason})")
        except (json.JSONDecodeError, ValueError) as exc:
            self.erreur.emit(f"réponse invalide ({exc})")
        except Exception as exc:  # filet de sécurité pour ne pas tuer le thread
            self.erreur.emit(f"erreur inattendue ({exc})")


class FenetreProduits(QMainWindow):
    def __init__(self, configuration: dict) -> None:
        super().__init__()
        self.configuration = configuration
        self.produits: list[dict] = []
        self._worker: ApiWorker | None = None

        self.setWindowTitle("Catalogue ordinateurs")
        self.resize(980, 640)
        self.setMinimumSize(720, 480)

        self._construire_interface()
        self._appliquer_styles()

        self.recherche.textChanged.connect(self.appliquer_filtre)
        self.bouton_actualiser.clicked.connect(self.charger_produits)
        QTimer.singleShot(0, self.charger_produits)

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _construire_interface(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 14)
        layout.setSpacing(10)

        titre = QLabel("Catalogue ordinateurs")
        titre.setObjectName("titre")
        layout.addWidget(titre)

        self.sous_titre = QLabel(
            f"Données servies par l'API · {self.configuration['api_base_url']}"
        )
        self.sous_titre.setObjectName("sousTitre")
        layout.addWidget(self.sous_titre)

        barre = QHBoxLayout()
        barre.setSpacing(8)

        self.recherche = QLineEdit()
        self.recherche.setPlaceholderText(
            "Rechercher un nom, une marque, une catégorie…"
        )
        self.recherche.setClearButtonEnabled(True)

        self.bouton_actualiser = QPushButton("Actualiser")
        self.bouton_actualiser.setShortcut("F5")
        self.bouton_actualiser.setCursor(Qt.PointingHandCursor)
        self.bouton_actualiser.setToolTip("Recharger les données depuis l'API (F5)")

        barre.addWidget(self.recherche, 1)
        barre.addWidget(self.bouton_actualiser)
        layout.addLayout(barre)

        self.table = QTableWidget(0, len(COLONNES))
        self.table.setHorizontalHeaderLabels(COLONNES)
        for colonne in range(len(COLONNES)):
            entete_item = self.table.horizontalHeaderItem(colonne)
            if colonne == 3:
                entete_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            elif colonne == 4:
                entete_item.setTextAlignment(Qt.AlignCenter)
            else:
                entete_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setSortingEnabled(False)

        entete = self.table.horizontalHeader()
        entete.setHighlightSections(False)
        entete.setSectionResizeMode(0, QHeaderView.Stretch)
        entete.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        entete.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        entete.setSectionResizeMode(3, QHeaderView.Fixed)
        entete.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 90)

        layout.addWidget(self.table, 1)

        self.statut = QLabel("Prêt.")
        self.statut.setObjectName("statut")
        layout.addWidget(self.statut)

    def _appliquer_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f4f6f9;
                color: #1f2937;
                font-size: 13px;
            }
            QLabel#titre {
                font-size: 21px;
                font-weight: 600;
            }
            QLabel#sousTitre {
                color: #64748b;
                font-size: 12px;
            }
            QLineEdit {
                padding: 7px 10px;
                border: 1px solid #cfd6df;
                border-radius: 6px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #2563eb;
            }
            QPushButton {
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                background: #2563eb;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #94a3b8;
            }
            QTableWidget {
                background: white;
                border: 1px solid #dce1e8;
                border-radius: 8px;
                selection-background-color: #dbeafe;
                selection-color: #1e3a8a;
            }
            QHeaderView::section {
                background: #eef2f7;
                color: #475569;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
            QLabel#statut {
                color: #64748b;
                font-size: 12px;
            }
            """
        )

    # ------------------------------------------------------------------
    # Chargement des données
    # ------------------------------------------------------------------

    def charger_produits(self) -> None:
        if self._worker is not None:
            return

        self.bouton_actualiser.setEnabled(False)
        self.bouton_actualiser.setText("Chargement…")
        self.statut.setStyleSheet("color: #64748b;")
        self.statut.setText("Chargement des produits…")

        url = f"{self.configuration['api_base_url']}/produits"
        worker = ApiWorker(
            url, self.configuration["timeout_seconds"], parent=self
        )
        self._worker = worker
        worker.produits_recus.connect(self.afficher_produits)
        worker.erreur.connect(self.afficher_erreur)
        worker.finished.connect(self._thread_termine)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def afficher_produits(self, produits: list) -> None:
        self.produits = produits
        self.table.setUpdatesEnabled(False)
        self.table.clearContents()
        self.table.setRowCount(len(produits))

        for ligne, produit in enumerate(produits):
            if not isinstance(produit, dict):
                continue

            try:
                prix = float(produit.get("prix_eur") or 0)
            except (TypeError, ValueError):
                prix = 0.0

            try:
                stock = int(produit.get("stock") or 0)
            except (TypeError, ValueError):
                stock = 0

            valeurs = [
                str(produit.get("nom") or "—"),
                str(produit.get("marque") or "—"),
                str(produit.get("categorie") or "—"),
                formater_prix(prix),
                str(stock) if stock > 0 else "Rupture",
            ]

            for colonne, valeur in enumerate(valeurs):
                item = QTableWidgetItem(valeur)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)

                if colonne == 3:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif colonne == 4:
                    item.setTextAlignment(Qt.AlignCenter)
                    if stock <= 0:
                        item.setForeground(QBrush(QColor("#c0392b")))
                        police = item.font()
                        police.setBold(True)
                        item.setFont(police)

                self.table.setItem(ligne, colonne, item)

        self.table.setUpdatesEnabled(True)
        self.appliquer_filtre()

        heure = datetime.now().strftime("%H:%M")
        self.statut.setStyleSheet("color: #15803d;")
        self.statut.setText(
            f"{len(produits)} produit(s) chargé(s) · dernière mise à jour à {heure}"
        )

    def afficher_erreur(self, message: str) -> None:
        self.statut.setStyleSheet("color: #b91c1c;")
        self.statut.setText(f"Impossible de charger les produits : {message}")

    def _thread_termine(self) -> None:
        self._worker = None
        self.bouton_actualiser.setEnabled(True)
        self.bouton_actualiser.setText("Actualiser")

    # ------------------------------------------------------------------
    # Recherche locale et fermeture
    # ------------------------------------------------------------------

    def appliquer_filtre(self) -> None:
        terme = normaliser(self.recherche.text().strip())

        for ligne in range(self.table.rowCount()):
            if not terme:
                self.table.setRowHidden(ligne, False)
                continue

            morceaux = []
            for colonne in (0, 1, 2):
                item = self.table.item(ligne, colonne)
                if item is not None:
                    morceaux.append(item.text())

            contenu = normaliser(" ".join(morceaux))
            self.table.setRowHidden(ligne, terme not in contenu)

    def closeEvent(self, event) -> None:
        worker = self._worker
        if worker is not None:
            try:
                if worker.isRunning():
                    worker.quit()
                    if not worker.wait(6000):
                        worker.terminate()
                        worker.wait(1000)
            except RuntimeError:
                pass
        super().closeEvent(event)


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    application = QApplication(sys.argv)
    application.setApplicationName("app-db-config")

    fenetre = FenetreProduits(charger_configuration())
    fenetre.show()
    return application.exec_()


if __name__ == "__main__":
    sys.exit(main())