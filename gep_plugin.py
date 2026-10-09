# -*- coding: utf-8 -*-

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from gep_sd.form.InsertFromOrigin import InsertFromOrigin
from gep_sd.form.GenerateSsbvName import GenerateSsbvName
from gep_sd.form.AddBvToEntities import AddBvToEntities
from gep_sd.form.AddGestionnaireToEntities import AddGestionnaireToEntities
from gep_sd.form.AddSourceToEntities import AddSourceToEntities
from gep_sd.form.AddSsbvToEntities import AddSsbvToEntities
from gep_sd.form.CreateSD import CreateSD
from gep_sd.form.GenerateCode import GenerateCode
from gep_sd.form.GetAndVerifCanalisastion import GetAndVerifCanalisation
from gep_sd.form.GetStreetAndTown import GetStreetAndTown
from gep_sd.form.PostCanoeToGep import PostCanoeToGep


# from 'PluginName'.form.ui import ressources_rc

class GepSDPlugin:
    def __init__(self, iface):
        self.interface = iface

    def initGui(self):
        # Création des actions
        # Créer un projet
        self.create_sd = QAction(QIcon(":/img/img/icon.svg"), u"Créer un Schéma Directeur", self.interface.mainWindow())
        self.create_sd.triggered.connect(self.on_click_create_sd)

        # Insérer des entitiées depuis une couche d'origine
        self.insert_from_origin = QAction(QIcon(":/img/img/icon.svg"), u"Insérer des entitées depuis une couche",
                                         self.interface.mainWindow())
        self.insert_from_origin.triggered.connect(self.on_click_insert_from_origin)

        # Passer de la tablette vers le bureau
        self.terrain_to_bureau = QAction(QIcon(":/img/img/icon.svg"), u"Tablette Vers Bureau",
                                         self.interface.mainWindow())
        self.terrain_to_bureau.triggered.connect(self.on_click_terrain_to_bureau)

        # générer les codes d'identification
        self.generate_code = QAction(QIcon(":/img/img/icon.svg"), u"Générer les Codes d'identifications",
                                     self.interface.mainWindow())
        self.generate_code.triggered.connect(self.on_generate_code)

        # Vérifier les canalisations et associer les regards
        self.get_and_verif_canalisation = QAction(QIcon(":/img/img/icon.svg"), u"Vérifier les canalisations",
                                                  self.interface.mainWindow())
        self.get_and_verif_canalisation.triggered.connect(self.on_click_get_and_verif_canalisation)

        # Généré les nom des SSBV
        self.generate_ssbv_name = QAction(QIcon(":/img/img/icon.svg"), u"Générer les noms des sous bassins versant",
                                            self.interface.mainWindow())
        self.generate_ssbv_name.triggered.connect(self.on_click_generate_ssbv_name)


        # Associer les Bassins Versant
        self.add_bv_to_entities = QAction(QIcon(":/img/img/icon.svg"), u"Associer les Bassins Versant aux entitées",
                                            self.interface.mainWindow())
        self.add_bv_to_entities.triggered.connect(self.on_click_add_bv_to_entities)

        # Associer les Sous Bassins Versant
        self.add_ssbv_to_entities = QAction(QIcon(":/img/img/icon.svg"), u"Associer les Sous Bassins Versant aux entitées",
                                            self.interface.mainWindow())
        self.add_ssbv_to_entities.triggered.connect(self.on_click_add_ssbv_to_entities)

        # Ajouter le nom des rues et le code insee
        self.get_street_and_town = QAction(QIcon(":/img/img/icon.svg"), u"Récupérer le nom des rues et des communes",
                                           self.interface.mainWindow())
        self.get_street_and_town.triggered.connect(self.on_click_get_street_and_town)

        # Ajouter le nom des gestionnaires aux entitées
        self.add_gestionnaire_to_entities = QAction(QIcon(":/img/img/icon.svg"),
                                                    u"Ajouter le gestionnaires aux entitées du projets",
                                                    self.interface.mainWindow())
        self.add_gestionnaire_to_entities.triggered.connect(self.on_click_add_gestionnaire_to_entities)

        # Ajouter le nom de la source aux entitées
        self.add_source_to_entities = QAction(QIcon(":/img/img/icon.svg"),
                                              u"Ajouter le sources aux entitées du projets",
                                              self.interface.mainWindow())
        self.add_source_to_entities.triggered.connect(self.on_click_add_source_to_entities)

        # Traitement à effectuer après le résultat de canoe
        self.post_canoe = QAction(QIcon(":/img/img/post_canoe.svg"), u"Post Canoe -> Couche GEP",
                                  self.interface.mainWindow())
        self.post_canoe.triggered.connect(self.on_click_post_canoe)
        # Ajouter les autres actions ici

        # Création menu du plugin pour ouvrir les dialogs
        self.menu = QMenu(u"Unima[GEP] - Schema Directeur")  # Ajouté Le nom du plugin
        self.menu.setIcon(QIcon(":/img/img/geopal_to_unima.svg"))
        self.menu.addAction(self.create_sd)
        self.menu.addAction(self.insert_from_origin)
        self.menu.addAction(self.terrain_to_bureau)
        self.menu.addAction(self.generate_code)
        self.menu.addAction(self.generate_ssbv_name)
        self.menu.addAction(self.add_bv_to_entities)
        self.menu.addAction(self.add_ssbv_to_entities)
        self.menu.addAction(self.get_and_verif_canalisation)
        self.menu.addAction(self.get_street_and_town)
        self.menu.addAction(self.add_gestionnaire_to_entities)
        self.menu.addAction(self.add_source_to_entities)
        self.menu.addAction(self.post_canoe)
        # Ajouter les autres actions ou sous menu ici
        self.interface.pluginMenu().addMenu(self.menu)

        # Création toolbar du plugin pour ouvrir les dialogs
        self.toolbar = self.interface.addToolBar(u"GepSDPlugin")  # Ajouté Le nom du plugin
        self.toolbar.setObjectName("Toolbar_GepSDPlugin")  # Ajouté Le nom du plugin
        self.toolbar.addAction(self.create_sd)
        self.toolbar.addAction(self.post_canoe)
        # Ajouter les autres actions ici

    def unload(self):
        self.interface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        self.interface.mainWindow().removeToolBar(self.toolbar)

    def on_click_create_sd(self):
        dlg = CreateSD(self.interface)  # Class à importer
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_insert_from_origin(self):
        dlg = InsertFromOrigin(self.interface)  # Class à importer
        dlg.show()
        result = dlg.exec_()
        if result:
            pass


    def on_click_terrain_to_bureau(self):
        # dlg = TerrainToBureau(self.interface)  # Class à importer
        # dlg.show()
        # result = dlg.exec_()
        # if result:
        pass

    def on_generate_code(self):
        dlg = GenerateCode(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_get_and_verif_canalisation(self):
        dlg = GetAndVerifCanalisation(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_generate_ssbv_name(self):
        dlg = GenerateSsbvName(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_add_bv_to_entities(self):
        dlg = AddBvToEntities(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass


    def on_click_add_ssbv_to_entities(self):
        dlg = AddSsbvToEntities(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_get_street_and_town(self):
        dlg = GetStreetAndTown(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_add_gestionnaire_to_entities(self):

        dlg = AddGestionnaireToEntities(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_add_source_to_entities(self):

        dlg = AddSourceToEntities(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass

    def on_click_post_canoe(self):

        dlg = PostCanoeToGep(self.interface)
        dlg.show()
        result = dlg.exec_()
        if result:
            pass
