import sys
from PyQt5 import QtWidgets

class MaFenetre(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setFixedSize(600, 400)
        self.setWindowTitle("APP TEST")

        fenetre_container = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(fenetre_container)

        for i in range(30):  ### utilisation du scroll
            layout.addRow(f"Champ {i}", QtWidgets.QLineEdit())

        # Zone de scroll
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(fenetre_container)
        scroll.setWidgetResizable(True)

        # layout du scroll
        layout_principal = QtWidgets.QVBoxLayout(self)
        layout_principal.addWidget(scroll)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mw = MaFenetre()
    mw.show()
    sys.exit(app.exec_())