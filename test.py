import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel, QMessageBox

class MenuDeroulant(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menu déroulant PyQt5")
        self.setGeometry(200, 200, 300, 150)

        # Layout vertical
        layout = QVBoxLayout()

        # Label pour afficher la sélection
        self.label = QLabel("Sélectionnez une option :", self)

        # Création du menu déroulant
        self.combo = QComboBox(self)
        self.combo.setEditable(False)  # Empêche la saisie libre

        # Ajout d'éléments au menu
        options = ["Option 1", "Option 2", "Option 3", "Option 4"]
        self.combo.addItems(options)

        # Connexion du signal de changement
        self.combo.currentIndexChanged.connect(self.on_selection_change)

        # Ajout des widgets au layout
        layout.addWidget(self.label)
        layout.addWidget(self.combo)

        self.setLayout(layout)

    def on_selection_change(self, index):
        try:
            choix = self.combo.itemText(index)
            self.label.setText(f"Vous avez choisi : {choix}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Problème lors de la sélection : {e}")

# Point d'entrée du programme
if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenetre = MenuDeroulant()
    fenetre.show()
    sys.exit(app.exec_())