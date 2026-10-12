"""Boîte de dialogue minimale affichant le log et la progression d'une QgsTask."""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QProgressBar, QTextBrowser,
    QPushButton, QSpacerItem, QSizePolicy,
)
from qgis.core import QgsTask


class ProgressDialog(QDialog):
    """
    Boîte de dialogue minimale de suivi d'une ``QgsTask``.

    Attend deux signaux sur ``task`` :
      - ``log(str, str)`` : ``(niveau, message)``.
      - ``progress(int)`` : pourcentage 0-100 (peut être émis
        plusieurs fois de 0 à 100, une fois par étape du traitement).
      - ``subprogress(int)`` : (optionnel) avancement global.

    Cycle de vie des boutons :
      - Tâche en cours      : « Annuler » actif (demande l'annulation), « OK » grisé.
      - Tâche réussie       : « OK » actif -> ``accept()``, « Annuler » grisé.
      - Tâche échouée /
        annulée             : « OK » grisé, « Fermer » actif -> ``reject()``.

    Le résultat de la boîte (``accepted`` / ``rejected``) reflète donc l'issue
    de la tâche, via les signaux natifs ``taskCompleted`` / ``taskTerminated``.
    """

    LEVEL_COLORS = {
        "info": "#222222",
        "warning": "#e67e00",
        "error": "#cc0000",
        "success": "#007a00",
        "debug": "#848484",
    }

    def __init__(self, task: QgsTask, parent=None, **kwargs) -> None:
        """
        :param task: La ``QgsTask`` à suivre.
        :param parent: Widget parent.
        """
        super().__init__(parent)
        show_subprogressbar = kwargs.get("show_subprogressbar", False)
        self.setWindowTitle("Traitement en cours")

        self._task_done = False  # True dès que la tâche est terminée (succès, échec ou annulation)
        self.error_count = 0  # nombre de logs de niveau "error" reçus

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)

        self.tb_logs = QTextBrowser(self)

        self.subbar = QProgressBar(self)
        self.subbar.setRange(0, 100)

        # --- Boutons ---
        self.pb_cancel = QPushButton("Annuler", self)
        self.pb_cancel.setObjectName("pb_cancel")
        self.pb_ok = QPushButton("OK", self)
        self.pb_ok.setObjectName("pb_ok")
        self.pb_ok.setEnabled(False)  # activé seulement quand la tâche a réussi

        buttons_layout = QHBoxLayout()
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        buttons_layout.addWidget(self.pb_cancel)
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        buttons_layout.addWidget(self.pb_ok)
        buttons_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout = QVBoxLayout(self)
        layout.addWidget(self.tb_logs)
        layout.addWidget(self.bar)
        if show_subprogressbar:
            layout.addWidget(self.subbar)
        layout.addLayout(buttons_layout)

        # --- Connexions ---
        self.task = task
        self.task.log.connect(self.add_log)
        self.task.progress.connect(self.bar.setValue)
        if show_subprogressbar:
            self.task.subprogress.connect(self.subbar.setValue)

        # Signaux natifs de QgsTask : émis dans le thread principal, après finished()
        self.task.taskCompleted.connect(self._on_task_completed)  # run() a retourné True
        self.task.taskTerminated.connect(self._on_task_terminated)  # run() a retourné False / annulation

        self.pb_cancel.clicked.connect(self.reject)
        self.pb_ok.clicked.connect(self.accept)

    # ------------------------------------------------------------------ logs
    def add_log(self, level: str, message: str) -> None:
        """
        Ajoute une ligne colorée au journal.

        :param level: ``info`` / ``warning`` / ``error`` / ``success`` / ``debug``.
        :param message: Message à afficher.
        """
        print('add_log')
        if level == "error":
            self.error_count += 1
        color = self.LEVEL_COLORS.get(level, "#222222")
        self.tb_logs.append(f'<span style="color:{color};">[{level.upper()}] {message}</span>')

    # ------------------------------------------------------- fin de la tâche
    def _on_task_completed(self) -> None:
        """La tâche s'est terminée avec succès : on autorise « OK »."""
        self._task_done = True
        self.setWindowTitle("Traitement terminé")
        self.bar.setValue(100)
        self.pb_cancel.setEnabled(False)
        self.pb_ok.setEnabled(True)
        self.pb_ok.setFocus()

    def _on_task_terminated(self) -> None:
        """La tâche a échoué ou a été annulée : seul « Fermer » reste possible."""
        self._task_done = True
        self.setWindowTitle("Traitement interrompu")
        self.pb_ok.setEnabled(False)
        self.pb_cancel.setEnabled(True)
        self.pb_cancel.setText("Fermer")

    # ------------------------------------------------------------ fermeture
    def reject(self) -> None:
        """Annule (ou ferme) la boîte.

        Appelée par « Annuler / Fermer », par Échap et par la croix de la
        fenêtre. Si la tâche tourne encore, on demande son annulation et on
        reste ouvert jusqu'à ``taskTerminated`` (l'annulation est coopérative :
        elle n'est prise en compte qu'au prochain ``isCanceled()`` du ``run()``).
        """
        if not self._task_done:
            self.task.cancel()
            self.pb_cancel.setEnabled(False)
            self.add_log("warning", "Annulation demandée, en attente de l'arrêt du traitement...")
            return
        super().reject()