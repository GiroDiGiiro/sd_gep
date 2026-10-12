"""Enchaînement « Terrain -> Bureau » : lance les traitements dans un ordre précis.

Principe : chaque traitement garde son propre formulaire (inchangé). Cette
fenêtre ne fait que :

1. afficher la liste ordonnée des étapes (cochables) ;
2. ouvrir les formulaires des étapes cochées, l'un après l'autre ;
3. attendre la fin des traitements asynchrones (QgsTask) avant de passer
   à l'étape suivante, pour respecter les dépendances.

Pour ajouter une fonctionnalité : écrire son formulaire comme d'habitude,
puis ajouter UNE ligne ``Step(...)`` dans ``STEPS``.
"""
from dataclasses import dataclass
from typing import List, Optional, Type

from PyQt5.QtCore import Qt, QEventLoop
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout, QDialogButtonBox,
)
from gep_sd.form.AddBvToEntities import AddBvToEntities
from gep_sd.form.AddGestionnaireToEntities import AddGestionnaireToEntities
from gep_sd.form.AddSourceToEntities import AddSourceToEntities
from gep_sd.form.AddSsbvToEntities import AddSsbvToEntities
from gep_sd.form.GenerateCode import GenerateCode
from gep_sd.form.GenerateSsbvName import GenerateSsbvName
from gep_sd.form.GetAndVerifCanalisastion import GetAndVerifCanalisation
from gep_sd.form.GetStreetAndTown import GetStreetAndTown
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsTask


@dataclass(frozen=True)
class Step:
    """Une étape de l'enchaînement.

    Attributes:
        label: Libellé affiché dans la liste.
        dialog_cls: Classe du formulaire (signature ``(interface, parent)``).
        tooltip: Explication affichée au survol (dépendances, rôle...).
    """

    label: str
    dialog_cls: Type[QDialog]
    tooltip: str = ""


# L'ORDRE DE CETTE LISTE EST L'ORDRE D'EXÉCUTION (dépendances comprises).
STEPS: List[Step] = [
    Step("Générer les codes", GenerateCode,
         "Doit passer en premier : les noms de sous-bassins utilisent le code des regards."),
    Step("Générer les noms de sous-bassins versants", GenerateSsbvName,
         "Dépend des codes des regards (étape 1)."),
    Step("Associer les bassins versants aux entités", AddBvToEntities,
         "Traitement asynchrone."),
    Step("Associer les sous-bassins versants aux entités", AddSsbvToEntities,
         "Traitement asynchrone."),
    Step("Récupérer et vérifier les canalisations", GetAndVerifCanalisation,
         "Renseigne regard amont / aval des canalisations."),
    Step("Renseigner le gestionnaire", AddGestionnaireToEntities),
    Step("Renseigner la source", AddSourceToEntities),
    Step("Rues et communes (WFS)", GetStreetAndTown,
         "Traitement asynchrone, nécessite internet."),
]


class TerrainToBureau(QDialog):
    """Fenêtre de sélection et d'enchaînement des traitements Terrain -> Bureau."""

    def __init__(self, interface, parent: Optional[QDialog] = None) -> None:
        """
        Args:
            interface: Interface QGIS (``QgisInterface``).
            parent: Widget parent (optionnel).
        """
        super().__init__(parent)
        self.interface = interface
        self.setWindowTitle("Terrain -> Bureau")
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        """Construit la fenêtre (liste des étapes + boutons), sans fichier .ui."""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Cochez les traitements à lancer. Ils seront exécutés dans l'ordre "
            "affiché ; chaque étape ouvre son propre formulaire."))

        self.lw_steps = QListWidget(self)
        for index, step in enumerate(STEPS):
            item = QListWidgetItem(step.label)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setCheckState(Qt.Checked)
            item.setToolTip(step.tooltip)
            item.setData(Qt.UserRole, index)  # index dans STEPS
            self.lw_steps.addItem(item)
        layout.addWidget(self.lw_steps)

        buttons = QHBoxLayout()
        buttons.addStretch()
        self.pb_cancel = QPushButton("Annuler")
        self.pb_ok = QPushButton("Lancer")
        buttons.addWidget(self.pb_cancel)
        buttons.addWidget(self.pb_ok)
        layout.addLayout(buttons)

        self.pb_cancel.clicked.connect(self.reject)
        self.pb_ok.clicked.connect(self._on_ok)

    def _selected_steps(self) -> List[Step]:
        """Retourne les étapes cochées, dans l'ordre de ``STEPS``."""
        steps: List[Step] = []
        for row in range(self.lw_steps.count()):
            item = self.lw_steps.item(row)
            if item.checkState() == Qt.Checked:
                steps.append(STEPS[item.data(Qt.UserRole)])
        return steps

    def _show_batch_summary(self, step_interrompue = None, faits= None, non_faits=None):
        """Affiche le bilan du traitement avec les icônes SVG."""

        dialog = QDialog(self.interface.mainWindow())
        dialog.setWindowTitle("Récapitulatif du traitement par lot")
        dialog.setWindowIcon(self.windowIcon())
        dialog.setMinimumWidth(450)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        if step_interrompue is not None:
            dialog.setWindowTitle("Arrêt du traitement par lot")
            # Message d'interruption
            message = QLabel(
                f"Le traitement a été interrompu à l'étape : "
                f"{step_interrompue}"
            )

            message.setWordWrap(True)
            layout.addWidget(message)

        def ajouter_section(titre, etapes, chemin_icone):
            titre_label = QLabel(f"<b>{titre}</b>")
            layout.addWidget(titre_label)

            if not etapes:
                label_vide = QLabel("Aucun")
                label_vide.setContentsMargins(24, 0, 0, 0)
                layout.addWidget(label_vide)
                return

            for nom in etapes:
                ligne = QHBoxLayout()
                ligne.setSpacing(8)

                icone_label = QLabel()
                pixmap = QIcon(chemin_icone).pixmap(18, 18)
                icone_label.setPixmap(pixmap)
                icone_label.setFixedSize(18, 18)
                icone_label.setAlignment(Qt.AlignCenter)

                nom_label = QLabel(nom)
                nom_label.setWordWrap(True)

                ligne.addWidget(icone_label, 0, Qt.AlignTop)
                ligne.addWidget(nom_label, 1)

                layout.addLayout(ligne)

        # Traitements réalisés
        ajouter_section("Traitements réalisés :",faits,":/img/img/ok.svg")

        # Traitements non réalisés
        if non_faits is not None:
            ajouter_section("Traitements non réalisés :",non_faits,":/img/img/not_ok.svg")

        # Bouton OK, comme dans QMessageBox.information()
        boutons = QDialogButtonBox(QDialogButtonBox.Ok)
        boutons.accepted.connect(dialog.accept)
        layout.addWidget(boutons)

        dialog.exec_()

    # ------------------------------------------------------------ exécution
    def _on_ok(self) -> None:
        """Lance les étapes cochées l'une après l'autre."""
        steps = self._selected_steps()
        if not steps:
            QMessageBox.warning(self, "Terrain -> Bureau", "Aucun traitement coché.")
            return
        error = None
        self.hide()  # on masque la fenêtre pendant que les formulaires défilent
        for i, step in enumerate(steps, start=1):
            ok = self._run_step(step)
            if not ok and i < len(steps):
                answer = QMessageBox.question(
                    self.interface.mainWindow(), "Terrain -> Bureau",
                    f"L'étape « {step.label} » a échoué ou été interrompue.\n"
                    "Continuer avec les étapes suivantes ?")
                if answer != QMessageBox.Yes:
                    # Étapes terminées avant l'étape interrompue
                    faits = [s.label for s in steps[:i - 1]]
                    # Étapes restant à exécuter après l'étape interrompue
                    non_faits = [s.label for s in steps[i:]]
                    self._show_batch_summary(step.label,faits,non_faits)
                    error = True
                    break

        if error:
            self.reject()
            return
        self._show_batch_summary(faits= [s.label for s in steps])
        self.accept()

    def _run_step(self, step: Step) -> bool:
        """Ouvre le formulaire d'une étape et attend la fin de son éventuel traitement.

        Les formulaires asynchrones déposent leur ``QgsTask`` dans
        ``interface.gep_sd_task`` et leur ``ProgressDialog`` dans
        ``interface.gep_sd_progress`` : si de nouveaux objets apparaissent
        après la fermeture du formulaire, on attend la fin de la tâche puis
        la fermeture de la fenêtre de progression.

        Contrat avec les formulaires : ``accept()`` après avoir lancé le
        traitement, ``reject()`` pour annuler (jamais ``close()``, qui
        équivaut à ``reject()``).

        Returns:
            ``False`` si le formulaire est annulé ou si la tâche échoue,
            ``True`` sinon.
        """
        previous_task = getattr(self.interface, "gep_sd_task", None)
        previous_progress = getattr(self.interface, "gep_sd_progress", None)

        dialog = step.dialog_cls(self.interface, self.interface.mainWindow())
        # modal : revient quand le formulaire est fermé.
        # Accepted = l'utilisateur a validé (OK), Rejected = il a annulé.
        if dialog.exec_() != QDialog.Accepted:
            return False

        task = getattr(self.interface, "gep_sd_task", None)
        if task is None or task is previous_task:
            return True  # traitement synchrone : déjà terminé

        progress = getattr(self.interface, "gep_sd_progress", None)
        if progress is previous_progress:
            progress = None  # pas de ProgressDialog propre à cette étape
        return self._wait_for_task(task, progress)

    @staticmethod
    def _wait_for_task(task: QgsTask, progress: Optional[QDialog] = None) -> bool:
        """Attend la fin d'une ``QgsTask`` ET la fermeture de son ``ProgressDialog``.

        1. On attend que la tâche soit terminée (succès ou échec).
        2. Si un ``ProgressDialog`` est affiché, on attend que l'utilisateur
           le ferme (OK / Fermer), pour qu'il puisse lire le journal avant
           que l'étape suivante n'apparaisse.

        L'interface reste réactive pendant l'attente (boucles d'événements locales).

        Returns:
            ``True`` si la tâche s'est terminée avec succès, ``False`` sinon
            (indépendamment du bouton utilisé pour fermer la fenêtre).
        """
        finished_states = (QgsTask.Complete, QgsTask.Terminated)
        if task.status() not in finished_states:
            loop = QEventLoop()
            task.taskCompleted.connect(loop.quit)
            task.taskTerminated.connect(loop.quit)
            loop.exec_()

        if progress is not None and progress.isVisible():
            loop = QEventLoop()
            progress.finished.connect(loop.quit)  # émis par accept() / reject()
            loop.exec_()
            return progress.result() == QDialog.Accepted

        return task.status() == QgsTask.Complete