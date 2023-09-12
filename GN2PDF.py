from PyQt6.QtWidgets import (QLabel, QWidget, QFileDialog, QApplication, QPushButton, QVBoxLayout)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from pathlib import Path
import shutil
import docker
import os
import sys

class MainWindow(QWidget):

    def __init__(self):

        super().__init__()
        self.client = docker.from_env()
        self.vbox = QVBoxLayout(self)
        self.initUI()

    def initUI(self):

        openFileButton = QPushButton("Select PDF")
        openFileButton.clicked.connect(self.showDialog)

        self.vbox.addWidget(openFileButton)

        self.setWindowTitle('')
        self.setWindowIcon(QIcon())
        self.show()


    def showDialog(self):

        waiting_label = QLabel(self)
        waiting_label.setText("Processing PDF, please wait.")
        self.vbox.addWidget(waiting_label)

        home_dir = str(Path.home())
        fname = QFileDialog.getOpenFileName(self, 'Open PDF', home_dir, "PDF (*.pdf)")

        if fname[0]:

            temp_dir = Path(os.getcwd()) / "temp_dir"
            os.makedirs(temp_dir, exist_ok=True)
            shutil.copy2(fname[0], temp_dir / "pdf_to_edit.pdf")

            pdfjam_c = self.client.containers.run("ubuntu_with_pdfjam", 
                                                  volumes={temp_dir: {"bind": "/pdfs/", "mode": "rw"}}, 
                                                  tty=True, 
                                                  detach=True,
                                                  remove=True,
                                                  command="/bin/bash")   

            _, name = pdfjam_c.exec_run("find . -name 'pdfjam*' -type d", stream=True)
            jam_folder_name = ""
            for n in name:
                jam_folder_name = n.decode()

            pdfjam_command = jam_folder_name.strip() + "/bin/pdfjam --outfile /pdfs/pdf_for_ps.pdf --paper a4paper /pdfs/pdf_to_edit.pdf"     
            _, pdfjam_output = pdfjam_c.exec_run(pdfjam_command, stream=True)
            
            for data in pdfjam_output:
                print(data.decode())

            pdf2ps_command = "pdf2ps /pdfs/pdf_for_ps.pdf /pdfs/ps.ps"
            _, pdf2ps_output = pdfjam_c.exec_run(pdf2ps_command, stream=True)

            for data in pdf2ps_output:
                print(data.decode())

            ps2pdf_command = "ps2pdf /pdfs/ps.ps /pdfs/final_pdf.pdf"
            _, ps2pdf_output = pdfjam_c.exec_run(ps2pdf_command, stream=True)

            for data in ps2pdf_output:
                print(data.decode())
            

            cleanup_command = "rm /pdfs/ps.ps && rm /pdfs/pdf_for_ps.pdf"
            pdfjam_c.exec_run(cleanup_command)

            pdfjam_c.stop()

            waiting_label.setText("PDF processed.")

def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()