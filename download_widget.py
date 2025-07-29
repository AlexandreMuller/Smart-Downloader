from PySide6.QtCore import QCoreApplication, QMetaObject
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QSpacerItem, QToolButton, QVBoxLayout

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(400, 227)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frame = QFrame(Form)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label = QLabel(self.frame)
        self.label.setObjectName(u"label")

        self.verticalLayout_2.addWidget(self.label)

        self.URL = QLineEdit(self.frame)
        self.URL.setObjectName(u"URL")

        self.verticalLayout_2.addWidget(self.URL)


        self.verticalLayout.addWidget(self.frame)

        self.frame_2 = QFrame(Form)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.frame_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_2 = QLabel(self.frame_2)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_3.addWidget(self.label_2)

        self.frame_3 = QFrame(self.frame_2)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.StyledPanel)
        self.frame_3.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.frame_3)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, -1, 0, -1)
        self.caminho = QLineEdit(self.frame_3)
        self.caminho.setObjectName(u"caminho")

        self.horizontalLayout.addWidget(self.caminho)

        self.caminho_explorar = QToolButton(self.frame_3)
        self.caminho_explorar.setObjectName(u"caminho_explorar")

        self.horizontalLayout.addWidget(self.caminho_explorar)


        self.verticalLayout_3.addWidget(self.frame_3)


        self.verticalLayout.addWidget(self.frame_2)

        self.frame_4 = QFrame(Form)
        self.frame_4.setObjectName(u"frame_4")
        self.frame_4.setFrameShape(QFrame.StyledPanel)
        self.frame_4.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.frame_4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.cancelar = QPushButton(self.frame_4)
        self.cancelar.setObjectName(u"cancelar")

        self.horizontalLayout_2.addWidget(self.cancelar)

        self.baixar = QPushButton(self.frame_4)
        self.baixar.setObjectName(u"baixar")

        self.horizontalLayout_2.addWidget(self.baixar)


        self.verticalLayout.addWidget(self.frame_4)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Baixar arquivo", None))
        self.label.setText(QCoreApplication.translate("Form", u"URL:", None))
        self.label_2.setText(QCoreApplication.translate("Form", u"Caminho:", None))
        self.caminho_explorar.setText(QCoreApplication.translate("Form", u"...", None))
        self.cancelar.setText(QCoreApplication.translate("Form", u"Cancelar", None))
        self.baixar.setText(QCoreApplication.translate("Form", u"Baixar", None))
    # retranslateUi

