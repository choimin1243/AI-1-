import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QInputDialog, QLabel, QMessageBox, QLineEdit, QFormLayout, QDialogButtonBox, QDialog
from PIL import Image, ImageDraw, ImageFont
import os
import urllib.parse
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, insert, select
from sqlalchemy import update
import requests
import openai
from PyQt5.QtGui import QImage, QPixmap, QFontDatabase
from PyQt5.QtCore import Qt
from sqlalchemy.orm import Session
from PyQt5.QtGui import QFontDatabase, QImage, QPixmap, QFont
import shutil

class StartWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        GPT_API = QPushButton('GPT API 새로 넣기', self)
        Edit_button = QPushButton('GPT API 값 수정하기', self)
        AI_button = QPushButton('공익광고 AI포스터 만들기', self)
        start_button = QPushButton('공익광고 홍보영상 만들기', self)
        start_button.clicked.connect(self.open_main_window)
        Edit_button.clicked.connect(self.Edit)
        AI_button.clicked.connect(self.AIPICTURE)
        GPT_API.clicked.connect(self.GPT)
        layout.addWidget(GPT_API)
        layout.addWidget(Edit_button)
        layout.addWidget(start_button)
        layout.addWidget(AI_button)
        self.setLayout(layout)
        self.setWindowTitle('시작하기')
        self.resize(300, 200)
        self.show()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        font_path = 'unz.ttf'
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("폰트를 로드하는 데 실패했습니다.")
            return
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print("폰트 패밀리 이름을 가져오는 데 실패했습니다.")
            return
        font_family = font_families[0]
        qss = f"""
        QWidget {{
            background-color: #E0FFFF;
            color: #333333;
            font-family: '{font_family}', Arial, sans-serif;
        }}
        QPushButton {{
            background-color: #1ebdbb;
            border: 2px solid #87CEEB;
            color: #FFFFFF;
            padding: 5px;
            font-size: 35px;
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: #0000CD;
        }}
        QPushButton:pressed {{
            background-color: #FF8C00;
        }}
        QTextEdit {{
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #FFD700;
            padding: 12px;
            font-size: 18px;
            border-radius: 10px;
        }}
        """
        self.setStyleSheet(qss)

    def Edit(self):
        self.main_window_edit = MainEdit()
        self.main_window_edit.show()

    def GPT(self):
        self.main_window = Mainstart()
        self.main_window.show()

    def AIPICTURE(self):
        self.main_window = AIPICTURE()
        self.main_window.show()

    def open_main_window(self):
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()

DATABASE_URL = "postgresql://postgres.cfqlbtuujqfsgimdzaig:choiminseuck@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"

class ApiKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("API Key 입력")
        self.resize(300, 100)

        layout = QFormLayout(self)

        self.codenumber = QLineEdit(self)
        self.text = QLineEdit(self)
        layout.addRow("참여코드:", self.codenumber)
        layout.addRow("명화만들기:", self.text)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

    def accept(self):
        codenumber = self.codenumber.text()
        prompt = self.text.text()
        super().accept()

        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        example_table = Table('example_table', metadata, autoload_with=engine)

        with engine.connect() as connection:
            with Session(engine) as session:
                stmt_id = select(example_table).where(example_table.c.password == codenumber)
                result_id = session.execute(stmt_id).fetchone()

        if result_id:
            openai.api_key = result_id[3]
            response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size='1024x1024'
            )
            image_url = response['data'][0]['url']
            if image_url:
                save_path = os.path.join(os.getcwd(), 'generated_image.png')
                self.download_image(image_url, save_path)
                self.parent.display_image(save_path)
        else:
            QMessageBox.warning(self, "Error", "아이디가 없습니다.")

    def download_image(self, url, save_path):
        try:
            response = requests.get(url)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
            QMessageBox.information(self, "Success", f"Image successfully downloaded: {save_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error downloading image: {e}")

class AIPICTURE(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.apply_stylesheet()
        self.rect_start = None
        self.rect_end = None
        self.current_image_path = None
        self.current_image = None
        self.drawing = False
        self.font_path = 'unz.ttf'  # 폰트 경로를 저장
        self.temp_image = None  # 직사각형을 그릴 임시 이미지를 저장

    def initUI(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        button0 = QPushButton("AI 그림생성하기", self)
        button1 = QPushButton('글자넣기', self)
        button2 = QPushButton('도형넣기', self)
        button3 = QPushButton('이미지 저장하기', self)

        button0.setFixedSize(200, 70)
        button1.setFixedSize(200, 70)
        button2.setFixedSize(200, 70)
        button3.setFixedSize(200, 70)
        right_layout = QVBoxLayout()
        right_layout.addWidget(button0)
        right_layout.addWidget(button1)
        right_layout.addWidget(button2)
        right_layout.addWidget(button3)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap('gongik.png')
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.image_label, 3)
        main_layout.addLayout(right_layout, 1)
        button0.clicked.connect(self.AIDRAW)
        button1.clicked.connect(self.add_draw)
        button2.clicked.connect(self.add_text_mode)
        button3.clicked.connect(self.save)
        self.setWindowTitle('미술프로그램')
        self.resize(1200, 800)

    def save(self):
        if self.image_label.pixmap() is not None:
            # 파일 저장 대화상자를 통해 저장할 경로를 선택합니다.
            save_path, _ = QFileDialog.getSaveFileName(self, "이미지 저장", "", "PNG Files (*.png);;All Files (*)")
            if save_path:
                # QLabel의 QPixmap을 QImage로 변환합니다.
                qimage = self.image_label.pixmap().toImage()

                # QImage를 PIL 이미지로 변환합니다.
                buffer = qimage.bits().asstring(qimage.width() * qimage.height() * qimage.depth() // 8)
                pil_image = Image.frombuffer("RGBA", (qimage.width(), qimage.height()), buffer, "raw", "BGRA", 0, 1)

                # PIL 이미지를 저장합니다.
                pil_image.save(save_path)
                QMessageBox.information(self, "저장 완료", "이미지가 성공적으로 저장되었습니다.")
        else:
            QMessageBox.warning(self, "저장 실패", "저장할 이미지가 없습니다.")

    def add_draw(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Error", "먼저 이미지를 로드하십시오.")
            return
        self.image_label.setCursor(Qt.CrossCursor)
        self.image_label.mousePressEvent = self.start_drawing
        self.image_label.mouseMoveEvent = self.update_drawing
        self.image_label.mouseReleaseEvent = self.end_drawings

    def AIDRAW(self):
        self.api_key_dialog = ApiKeyDialog(self)
        self.api_key_dialog.exec_()

    def display_image(self, image_path):
        self.current_image_path = image_path
        self.current_image = cv2.imread(image_path)
        self.temp_image = self.current_image.copy()  # 임시 이미지 초기화
        self.update_label()

    def update_label(self):
        if self.temp_image is not None:
            height, width, channel = self.temp_image.shape
            bytes_per_line = 3 * width
            q_img = QImage(self.temp_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap)
            self.image_label.setScaledContents(True)

    def add_text_mode(self):
        if self.current_image is None:
            QMessageBox.warning(self, "Error", "먼저 이미지를 로드하십시오.")
            return
        self.image_label.setCursor(Qt.CrossCursor)
        self.image_label.mousePressEvent = self.start_drawing
        self.image_label.mouseMoveEvent = self.update_drawing
        self.image_label.mouseReleaseEvent = self.end_drawing

    def start_drawing(self, event):
        self.rect_start = (event.pos().x(), event.pos().y())
        self.drawing = True

    def update_drawing(self, event):
        if self.drawing:
            self.rect_end = (event.pos().x(), event.pos().y())
            self.temp_image = self.current_image.copy()
            cv2.rectangle(self.temp_image, self.rect_start, self.rect_end, (255, 0, 0), 2)  # 파란색 직사각형
            self.update_label()

    def end_drawing(self, event):
        if not self.drawing:
            return
        self.rect_end = (event.pos().x(), event.pos().y())
        self.drawing = False
        self.image_label.setCursor(Qt.ArrowCursor)
        print("hello12")
        self.draw_rectangle_on_image()

    def draw_rectangle_on_image(self):
        if self.current_image is None:
            return

        x1, y1 = self.rect_start
        x2, y2 = self.rect_end

        # Convert OpenCV image (numpy array) to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB))

        # Draw the rectangle on the image
        draw = ImageDraw.Draw(pil_image)

        color, ok = self.get_color()

        if color == 'red':
            draw.rectangle([self.rect_start, self.rect_end], outline='blue', width=2, fill='blue')
        else:
            draw.rectangle([self.rect_start, self.rect_end], outline=color, width=2, fill=color)

        # Convert PIL image back to OpenCV image
        self.current_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        self.temp_image = self.current_image.copy()  # 직사각형이 추가된 이미지를 임시 이미지로 설정
        self.update_label()

        # Save the updated image with the rectangle
        if self.current_image_path:
            cv2.imwrite(self.current_image_path, self.current_image)

    def add_text_to_image(self, text, color):
        print(color)
        if self.current_image is None:
            return

        x1, y1 = self.rect_start
        x2, y2 = self.rect_end
        text_position = (min(x1, x2), min(y1, y2) + (abs(y2 - y1) // 2))

        rect_height = abs(y2+20 - y1)
        print(rect_height)

        font_size = max(10, rect_height // 2)  # 최소 폰트 크기를 10으로 설정

        # Convert OpenCV image (numpy array) to PIL Image
        pil_image = Image.fromarray(cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB))

        # Load the font
        font = ImageFont.truetype(self.font_path, font_size)

        # Draw the text on the image
        draw = ImageDraw.Draw(pil_image)

        if color == 'red':
            draw.text(text_position, text, font=font, fill='blue')
        else:
            draw.text(text_position, text, font=font, fill=color)

        # Convert PIL image back to OpenCV image
        self.current_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        self.temp_image = self.current_image.copy()  # 텍스트가 추가된 이미지를 임시 이미지로 설정
        self.update_label()

        # Save the updated image with text
        if self.current_image_path:
            cv2.imwrite(self.current_image_path, self.current_image)

    def end_drawings(self, event):
        if not self.drawing:
            return
        self.rect_end = (event.pos().x(), event.pos().y())
        self.drawing = False
        self.image_label.setCursor(Qt.ArrowCursor)
        self.prompt_text_input()

    def prompt_text_input(self):
        if self.rect_start and self.rect_end:
            text, ok = QInputDialog.getText(self, '텍스트 입력', '사각형 내부에 넣을 텍스트를 입력하세요:')
            if ok and text:
                color, ok = self.get_color()
                if ok:
                    self.add_text_to_image(text, color)

    def get_color(self):
        colors = ['white', 'black', 'green', 'red']
        color, ok = QInputDialog.getItem(self, "색깔 선택", "텍스트 색깔을 선택하세요:", colors, 0, False)
        return color, ok

    def apply_stylesheet(self):
        font_path = 'unz.ttf'
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("폰트를 로드하는 데 실패했습니다.")
            return
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print("폰트 패밀리 이름을 가져오는 데 실패했습니다.")
            return
        font_family = font_families[0]
        qss = f"""
        QWidget {{
            background-color: #E0FFFF;
            color: #333333;
            font-family: '{font_family}', Arial, sans-serif;
        }}
        QPushButton {{
            background-color: #1ebdbb;
            border: 2px solid #87CEEB;
            color: #FFFFFF;
            padding: 5px;
            font-size: 35px;
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: #0000CD;
        }}
        QPushButton:pressed {{
            background-color: #FF8C00;
        }}
        QTextEdit {{
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #FFD700;
            padding: 12px;
            font-size: 18px;
            border-radius: 10px;
        }}
        """
        self.setStyleSheet(qss)

class MainEdit(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        font_path = 'unz.ttf'
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("폰트를 로드하는 데 실패했습니다.")
            return
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print("폰트 패밀리 이름을 가져오는 데 실패했습니다.")
            return
        font_family = font_families[0]
        qss = f"""
        QWidget {{
            background-color: #E0FFFF;
            color: #333333;
            font-family: '{font_family}', Arial, sans-serif;
        }}
        QPushButton {{
            background-color: #1ebdbb;
            border: 2px solid #87CEEB;
            color: #FFFFFF;
            padding: 5px;
            font-size: 35px;
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: #0000CD;
        }}
        QPushButton:pressed {{
            background-color: #FF8C00;
        }}
        QTextEdit {{
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #FFD700;
            padding: 12px;
            font-size: 18px;
            border-radius: 10px;
        }}
        """
        self.setStyleSheet(qss)

    def initUI(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        font = QFont()
        font.setPointSize(16)

        self.id_label = QLabel('아이디:')
        self.id_label.setFont(font)
        self.id_input = QLineEdit(self)
        self.id_input.setFont(font)
        form_layout.addRow(self.id_label, self.id_input)

        self.code_label = QLabel('참여코드:')
        self.code_label.setFont(font)
        self.code_input = QLineEdit(self)
        self.code_input.setFont(font)
        form_layout.addRow(self.code_label, self.code_input)

        self.api_label = QLabel('수정된API 키:')
        self.api_label.setFont(font)
        self.api_input = QLineEdit(self)
        self.api_input.setFont(font)
        form_layout.addRow(self.api_label, self.api_input)

        self.submit_button2 = QPushButton('제출', self)
        self.submit_button2.setFont(font)
        self.submit_button2.clicked.connect(self.submited2)
        form_layout.addRow(self.submit_button2)

        main_layout.addLayout(form_layout)

        self.setWindowTitle('미술프로그램')
        self.resize(400, 200)
        self.show()

    def submited2(self):
        DATABASE_URL = "postgresql://postgres.cfqlbtuujqfsgimdzaig:choiminseuck@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        example_table = Table('example_table', metadata, autoload_with=engine)

        user_id = self.id_input.text()
        user_code = self.code_input.text()
        user_api_key = self.api_input.text()

        with engine.connect() as connection:
            with Session(engine) as session:
                stmt_id = select(example_table).where(
                    example_table.c.name == user_id,
                    example_table.c.password == user_code
                )
                result_id = session.execute(stmt_id).fetchone()

                if result_id:
                    stmt_update = update(example_table).where(
                        example_table.c.name == user_id,
                        example_table.c.password == user_code
                    ).values(API_KEY=user_api_key)

                    session.execute(stmt_update)
                    session.commit()
                    print(f"API_KEY for user_id {user_id} updated successfully.")
                else:
                    print("No matching user_id and user_code found.")

class Mainstart(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.apply_stylesheet()

    def apply_stylesheet(self):
        font_path = 'unz.ttf'
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("폰트를 로드하는 데 실패했습니다.")
            return
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print("폰트 패밀리 이름을 가져오는 데 실패했습니다.")
            return
        font_family = font_families[0]
        qss = f"""
        QWidget {{
            background-color: #E0FFFF;
            color: #333333;
            font-family: '{font_family}', Arial, sans-serif;
        }}
        QPushButton {{
            background-color: #1ebdbb;
            border: 2px solid #87CEEB;
            color: #FFFFFF;
            padding: 5px;
            font-size: 35px;
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: #0000CD;
        }}
        QPushButton:pressed {{
            background-color: #FF8C00;
        }}
        QTextEdit {{
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #FFD700;
            padding: 12px;
            font-size: 18px;
            border-radius: 10px;
        }}
        """
        self.setStyleSheet(qss)

    def initUI(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        font = QFont()
        font.setPointSize(16)

        self.id_label = QLabel('아이디:')
        self.id_label.setFont(font)
        self.id_input = QLineEdit(self)
        self.id_input.setFont(font)
        form_layout.addRow(self.id_label, self.id_input)

        self.code_label = QLabel('참여코드:')
        self.code_label.setFont(font)
        self.code_input = QLineEdit(self)
        self.code_input.setFont(font)
        form_layout.addRow(self.code_label, self.code_input)

        self.api_label = QLabel('API 키:')
        self.api_label.setFont(font)
        self.api_input = QLineEdit(self)
        self.api_input.setFont(font)
        form_layout.addRow(self.api_label, self.api_input)

        self.submit_button = QPushButton('제출', self)
        self.submit_button.setFont(font)
        self.submit_button.clicked.connect(self.submit)
        form_layout.addRow(self.submit_button)

        main_layout.addLayout(form_layout)

        self.setWindowTitle('미술프로그램')
        self.resize(400, 200)
        self.show()

    def submit(self):
        user_id = self.id_input.text()
        user_code = self.code_input.text()
        user_api_key = self.api_input.text()

        DATABASE_URL = "postgresql://postgres.cfqlbtuujqfsgimdzaig:choiminseuck@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        example_table = Table('example_table', metadata, autoload_with=engine)

        with engine.connect() as connection:
            stmt_id = select(example_table).where(example_table.c.name == user_id)
            result_id = connection.execute(stmt_id)
            existing_id = result_id.fetchall()

            stmt_code = select(example_table).where(example_table.c.password == user_code)
            result_code = connection.execute(stmt_code)
            existing_code = result_code.fetchall()

        if not existing_id and not existing_code:
            data_to_insert = [
                {'name': user_id, 'password': user_code, 'API_KEY': user_api_key},
            ]

            with engine.begin() as connection:
                for data in data_to_insert:
                    stmt = insert(example_table).values(data)
                    connection.execute(stmt)
            QMessageBox.information(self, '결과', '데이터가 성공적으로 삽입되었습니다.')
        else:
            QMessageBox.warning(self, '경고', '아이디 또는 참여코드가 이미 존재합니다.')

        with engine.connect() as connection:
            stmt = select(example_table)
            result = connection.execute(stmt)
            rows = result.fetchall()

        for row in rows:
            print(row)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.flip_states = []
        self.apply_stylesheet()
        self.mouse_position = None
        self.text_info = None
        self.background = None
        self.images = []
        self.all_objects = []
        self.rotations = []
        self.drawing = False
        self.dragging_object_index = -1
        self.drag_offset = (0, 0)
        self.is_running = False
        self.rect_start = None
        self.rect_end = None
        self.clone = None

    def initUI(self):
        main_layout = QHBoxLayout(self)

        left_layout = QVBoxLayout()
        button0 = QPushButton("색지우기", self)
        button1 = QPushButton('물체넣기', self)
        button2 = QPushButton('배경넣기', self)

        button0.setFixedSize(200, 70)
        button1.setFixedSize(200, 70)
        button2.setFixedSize(200, 70)

        right_layout = QVBoxLayout()
        button5 = QPushButton('글귀넣기', self)
        button3 = QPushButton('영상프로그램 실행', self)
        button4 = QPushButton('영상종료', self)
        button6 = QPushButton('영상입체만들기', self)
        button8 = QPushButton('이미지 다듬기', self)

        button5.setFixedSize(200, 70)
        button3.setFixedSize(200, 70)
        button4.setFixedSize(200, 70)
        button6.setFixedSize(200, 70)

        right_layout.addWidget(button0)
        right_layout.addWidget(button8)
        right_layout.addWidget(button1)
        right_layout.addWidget(button2)
        right_layout.addWidget(button5)
        right_layout.addWidget(button3)
        right_layout.addWidget(button6)
        right_layout.addWidget(button4)

        self.image_label = QLabel(self)
        pixmap = QPixmap('gongik.png')
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.image_label, 3)
        main_layout.addLayout(right_layout, 1)

        button0.clicked.connect(self.make)
        button1.clicked.connect(self.object)
        button2.clicked.connect(self.open_new_window2)

        button5.clicked.connect(self.show_image_with_rectangle_selection)
        button3.clicked.connect(self.open_new_window3)
        button4.clicked.connect(self.open_new_window4)
        button6.clicked.connect(self.open_new_window6)
        button8.clicked.connect(self.mamake)

        self.setWindowTitle('미술프로그램')
        self.resize(1200, 800)

    def apply_stylesheet(self):
        font_path = 'unz.ttf'
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("폰트를 로드하는 데 실패했습니다.")
            return
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        if not font_families:
            print("폰트 패밀리 이름을 가져오는 데 실패했습니다.")
            return
        font_family = font_families[0]
        qss = f"""
        QWidget {{
            background-color: #E0FFFF;
            color: #333333;
            font-family: '{font_family}', Arial, sans-serif;
        }}
        QPushButton {{
            background-color: #1ebdbb;
            border: 2px solid #87CEEB;
            color: #FFFFFF;
            padding: 5px;
            font-size: 35px;
            border-radius: 10px;
        }}
        QPushButton:hover {{
            background-color: #0000CD;
        }}
        QPushButton:pressed {{
            background-color: #FF8C00;
        }}
        QTextEdit {{
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #FFD700;
            padding: 12px;
            font-size: 18px;
            border-radius: 10px;
        }}
        """
        self.setStyleSheet(qss)

    def onMouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            cv2.circle(self.img_edit, (x, y), 30, (255, 255, 255), -1)
            cv2.imshow("수정", self.img_edit)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                cv2.circle(self.img_edit, (x, y), 30, (255, 255, 255), -1)
                cv2.imshow("수정", self.img_edit)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False

    def mamake(self):
        try:
            options = QFileDialog.Options()
            self.img_pathed, _ = QFileDialog.getOpenFileName(self, "파일 선택", "",
                                                           "모든 파일 (*);;텍스트 파일 (*.txt);;이미지 파일 (*.png *.jpg);;PDF 파일 (*.pdf)",
                                                           options=options)

            with open(self.img_pathed, 'rb') as f:
                file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                self.img_edit = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

                cv2.imshow("수정", self.img_edit)

                cv2.setMouseCallback("수정", self.onMouse)

                while True:
                    if cv2.waitKey(0) & 0xFF == 27:
                        cv2.imwrite(str(self.img_pathed) + "result.png", self.img_edit)
                        break
            cv2.destroyAllWindows()

        except:
            pass

    def open_new_window6(self):
        try:
            self.final_running = True
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            fname = QFileDialog.getOpenFileName(self, "Open File", "./")
            if fname[0]:
                print(fname[0])
                file_path = urllib.parse.quote(fname[0])
                file_path = urllib.parse.unquote(file_path)
                video1 = cv2.VideoCapture(file_path)
                video2 = cv2.VideoCapture(file_path)
                video3 = cv2.VideoCapture(file_path)
                video4 = cv2.VideoCapture(file_path)

                if not video1.isOpened() or not video2.isOpened() or not video3.isOpened() or not video4.isOpened():
                    print("Error: One or more video files could not be opened.")
                    return

                self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.out = cv2.VideoWriter('result_final.avi', self.fourcc, 20.0, (3000, 2400))

                if not self.out.isOpened():
                    print("Error: Could not open output file.")
                    return

                while self.final_running:
                    ret1, frame1 = video1.read()
                    ret2, frame2 = video2.read()
                    ret3, frame3 = video3.read()
                    ret4, frame4 = video4.read()

                    if not ret1 or not ret2 or not ret3 or not ret4:
                        break

                    frame1 = cv2.resize(frame1, (800, 800))
                    frame1 = frame1[500:, 400:600, :]
                    frame1 = cv2.resize(frame1, (800, 800))

                    frame4 = cv2.resize(frame4, (800, 800))
                    middle = frame4[120:500, 450:600, :]
                    frame4 = cv2.resize(middle, (800, 800))

                    frame2 = cv2.resize(frame2, (800, 800))
                    frame2 = frame2[0:500, :450, :]
                    frame2 = cv2.resize(frame2, (800, 800))

                    frame3 = cv2.resize(frame3, (800, 800))
                    right = frame3[10:510, 620:, :]
                    frame3 = cv2.resize(right, (800, 800))

                    rows, cols, _ = frame1.shape

                    pts1 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts2 = np.float32([[300, 250], [10, rows - 50], [cols - 300, 250], [cols - 10, rows - 50]])
                    pts3 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts4 = np.float32([[546, 9], [500, 250], [780, 11], [788, 750]])

                    pts5 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts6 = np.float32([[6, 12], [14, 742], [256, 4], [302, 248]])

                    pts7 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts8 = np.float32([[251, 4], [306, 250], [550, 7], [505, 247]])

                    mtrx1 = cv2.getPerspectiveTransform(pts1, pts2)
                    dst1 = cv2.warpPerspective(frame1, mtrx1, (cols, rows))

                    mtrx2 = cv2.getPerspectiveTransform(pts3, pts4)
                    dst2 = cv2.warpPerspective(frame3, mtrx2, (cols, rows))

                    dst2 = cv2.resize(dst2, (cols, rows))

                    combined_frame = cv2.add(dst1, dst2)

                    mtrx3 = cv2.getPerspectiveTransform(pts5, pts6)
                    dst3 = cv2.warpPerspective(frame2, mtrx3, (cols, rows))

                    combined_frame = cv2.add(combined_frame, dst3)

                    mtrx4 = cv2.getPerspectiveTransform(pts7, pts8)
                    dst4 = cv2.warpPerspective(frame4, mtrx4, (cols, rows))

                    combined_frame = cv2.add(combined_frame, dst4)

                    combined_frame = cv2.resize(combined_frame, (3000, 2400))

                    cv2.imshow("합성된 영상", combined_frame)

                    self.out.write(combined_frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                video1.release()
                video2.release()
                video3.release()
                video4.release()
                self.out.release()
                cv2.destroyAllWindows()

        except Exception as e:
            print(f"Error: {e}")

    def make(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            files, _ = QFileDialog.getOpenFileNames(self, "파일 선택", "", "모든 파일 (*);;텍스트 파일 (*.txt)", options=options)

            image_list = files
            self.images_background = []

            for img_path in image_list:
                try:
                    with open(img_path, 'rb') as f:
                        file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                        img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
                        self.images_background.append(img)
                except Exception as e:
                    print(f"Exception loading image {img_path}: {e}")

            for i in range(len(self.images_background)):
                gray = cv2.cvtColor(self.images_background[i], cv2.COLOR_BGR2GRAY)

                blur = cv2.GaussianBlur(gray, (5, 5), 0)

                edges = cv2.Canny(blur, 50, 150)

                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                new_img = np.zeros_like(self.images_background[i])

                cv2.drawContours(new_img, contours, -1, (255, 255, 255), thickness=-1)

                new_img = cv2.bitwise_not(new_img)

                cv2.imshow("result", new_img)

                filename = f"result_image_{i}.png"
                cv2.imwrite(filename, new_img)

        except Exception as e:
            print(f"Error in make: {e}")

    def myPutText(self, src, text, pos, font_size, font_color):
        try:
            img_pil = Image.fromarray(src)
            draw = ImageDraw.Draw(img_pil)
            font = ImageFont.truetype('unz.ttf', 60)
            draw.text(pos, text, font=font, fill=font_color)
            return np.array(img_pil)

        except Exception as e:
            print(f"Error in myPutText: {e}")
            return src

    def show_image_with_rectangle_selection(self):
        try:
            if self.background is None:
                print("No background image loaded.")
                return

            self.clone = self.background.copy()
            cv2.imshow("image", self.clone)
            cv2.setMouseCallback("image", self.extract_coordinates)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            if self.rect_start and self.rect_end:
                text, ok = QInputDialog.getText(self, '텍스트 입력', '사각형 내부에 넣을 텍스트를 입력하세요:')
                if ok and text:
                    self.text_info = {'text': text, 'rect_start': self.rect_start, 'rect_end': self.rect_end}
                    self.add_text_to_background()

        except Exception as e:
            print(f"Error in show_image_with_rectangle_selection: {e}")

    def add_text_to_frame(self, frame, text_info):
        try:
            img_pil = Image.fromarray(frame)
            draw = ImageDraw.Draw(img_pil)
            font = ImageFont.truetype('unz.ttf', text_info['font_size'])
            draw.text(text_info['position'], text_info['text'], font=font, fill=text_info['font_color'])
            return np.array(img_pil)

        except Exception as e:
            print(f"Error in add_text_to_frame: {e}")
            return frame

    def add_text_to_background(self):
        try:
            if self.background is None:
                print("No background image loaded.")
                return

            img_pil = Image.fromarray(cv2.cvtColor(self.background, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img_pil)
            font = ImageFont.truetype('unz.ttf', 60)

            text = self.text_info['text']
            rect_start = self.text_info['rect_start']
            rect_end = self.text_info['rect_end']
            x = rect_start[0]
            y = rect_start[1]
            width = rect_end[0] - rect_start[0]
            height = rect_end[1] - rect_start[1]
            font = ImageFont.truetype('unz.ttf', height)

            draw.text((x-100+ width // 2, y-50+ height // 2), text, font=font, fill=(255, 255, 255, 255))

            img_with_text = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            self.background = img_with_text
            self.update_image_label(img_with_text)

        except Exception as e:
            print(f"Error in add_text_to_background: {e}")

    def extract_coordinates(self, event, x, y, flags, param):
        try:
            if event == cv2.EVENT_LBUTTONDOWN:
                self.drawing = True
                self.rect_start = (x, y)
                self.rect_end = None
                self.clone = self.background.copy()

            elif event == cv2.EVENT_MOUSEMOVE:
                if self.drawing:
                    self.rect_end = (x, y)
                    image = self.clone.copy()
                    cv2.rectangle(image, self.rect_start, self.rect_end, (0, 255, 0), 2)
                    cv2.imshow("image", image)

            elif event == cv2.EVENT_LBUTTONUP:
                self.drawing = False
                self.rect_end = (x, y)
                cv2.rectangle(self.clone, self.rect_start, self.rect_end, (0, 255, 0), 2)
                cv2.imshow("image", self.clone)

        except Exception as e:
            print(f"Error in extract_coordinates: {e}")

    def object(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            files, _ = QFileDialog.getOpenFileNames(self, "파일 선택", "", "모든 파일 (*);;텍스트 파일 (*.txt)", options=options)

            image_list = files

            for img_path in image_list:
                with open(img_path, 'rb') as f:
                    file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                    img = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)
                    position = (np.random.randint(0, self.background.shape[1] - 100),
                                np.random.randint(0, self.background.shape[0] - 100))
                    self.all_objects.append((img, position))
                    self.rotations.append(0)

            self.flip_states = [False] * len(self.all_objects)
            self.rotations = [0] * len(self.rotations)

            self.display_objects_on_background()


        except:
            pass

    def display_objects_on_background(self):
        try:
            if self.background is None:
                print("No background image loaded.")
                return

            background = self.background.copy()

            for i, (img, pos) in enumerate(self.all_objects):
                resized_image = cv2.resize(img, (100, 100))

                if resized_image.shape[2] == 4:
                    mask = resized_image[:, :, 3]
                else:
                    lower_white = np.array([200, 200, 200])
                    upper_white = np.array([255, 255, 255])
                    mask = cv2.inRange(resized_image, lower_white, upper_white)
                    mask = cv2.bitwise_not(mask)

                if resized_image.shape[2] != 4:
                    resized_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2BGRA)

                resized_image[:, :, 3] = mask

                x, y = pos

                alpha_s = resized_image[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s

                for c in range(0, 3):
                    background[y:y + resized_image.shape[0], x:x + resized_image.shape[1], c] = (
                            alpha_s * resized_image[:, :, c] + alpha_l * background[y:y + resized_image.shape[0],
                                                                 x:x + resized_image.shape[1], c])

            self.update_image_label(background)
        except:
            pass
    def update_image_label(self, image):
        try:
            height, width, channel = image.shape
            bytesPerLine = 3 * width
            qImg = QImage(image.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(qImg)
            self.image_label.setPixmap(pixmap)
        except:
            pass
    def open_new_window2(self):
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            self.img_path, _ = QFileDialog.getOpenFileName(self, "파일 선택", "", "모든 파일 (*);;텍스트 파일 (*.txt);;이미지 파일 (*.png *.jpg);;PDF 파일 (*.pdf)", options=options)

            with open(self.img_path, 'rb') as f:
                file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                self.background = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

            self.update_image_label(self.background)

        except Exception as e:
            print(f"Error in open_new_window2: {e}")

    def mouse_event(self, event, x, y, flags, param):
        self.down = False
        if event == cv2.EVENT_MOUSEMOVE:
            self.mouse_position = (x, y)
        elif event == cv2.EVENT_LBUTTONDOWN:
            window_width, window_height = 640, 480
            image_height, image_width = self.background.shape[:2]
            self.down = True
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging_object_index != -1:
            dx, dy = self.drag_offset
            new_x = x - dx
            new_y = y - dy
            self.all_objects[self.dragging_object_index] = (self.all_objects[self.dragging_object_index][0], (new_x, new_y))
            self.display_objects_on_background()
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging_object_index = -1

    def open_new_window3(self):
        if self.background is None or not self.all_objects:
            print("배경 이미지나 물체 이미지가 로드되지 않았습니다.")
            return

        frame_width, frame_height = 640, 480
        background = cv2.resize(self.background, (frame_width, frame_height))
        self.flip_states = [False] * len(self.all_objects)

        self.x_list = [pos[0] for _, pos in self.all_objects]
        self.y_list = [pos[1] for _, pos in self.all_objects]

        self.dx_list = [np.random.randint(1, 10) for _ in range(len(self.all_objects))]
        self.dy_list = [np.random.randint(1, 10) for _ in range(len(self.all_objects))]

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter('output.avi', fourcc, 30.0, (frame_width, frame_height))
        self.is_running = True

        frame_count = 0

        cv2.namedWindow("Floating Objects", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Floating Objects", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback("Floating Objects", self.mouse_event)

        while self.is_running:
            self.frame = background.copy()

            for i, (img, pos) in enumerate(self.all_objects):
                try:
                    resized_image = cv2.resize(img, (100, 100))

                    if self.rotations[i] != 0:
                        M = cv2.getRotationMatrix2D((50, 50), self.rotations[i], 1)
                        resized_image = cv2.warpAffine(resized_image, M, (100, 100))

                    if resized_image.dtype != np.uint8:
                        resized_image = cv2.convertScaleAbs(resized_image)

                    if len(resized_image.shape) == 2:
                        resized_image = cv2.cvtColor(resized_image, cv2.COLOR_GRAY2BGR)

                    if len(resized_image.shape) == 3 and resized_image.shape[2] == 4:
                        mask = resized_image[:, :, 3]
                    else:
                        lower_white = np.array([200, 200, 200])
                        upper_white = np.array([255, 255, 255])
                        mask = cv2.inRange(resized_image, lower_white, upper_white)
                        mask = cv2.bitwise_not(mask)

                        resized_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2BGRA)

                    resized_image[:, :, 3] = mask

                    self.x_list[i] += self.dx_list[i]
                    self.y_list[i] += self.dy_list[i]

                    if self.x_list[i] < 0:
                        self.x_list[i] = 0
                        self.dx_list[i] *= -1
                    elif self.x_list[i] + resized_image.shape[1] > self.frame.shape[1]:
                        self.x_list[i] = self.frame.shape[1] - resized_image.shape[1]
                        self.dx_list[i] *= -1
                    if self.y_list[i] < 0:
                        self.y_list[i] = 0
                        self.dy_list[i] *= -1
                    elif self.y_list[i] + resized_image.shape[0] > self.frame.shape[0]:
                        self.y_list[i] = self.frame.shape[0] - resized_image.shape[0]
                        self.dy_list[i] *= -1

                    if self.mouse_position:
                        mx, my = self.mouse_position
                        if self.x_list[i] <= mx <= self.x_list[i] + 100 and self.y_list[i] <= my <= self.y_list[
                            i] + 100:
                            self.dx_list[i] = np.random.randint(-10, 10)
                            self.dy_list[i] = np.random.randint(-10, 10)

                        if self.down == True:
                            if self.x_list[i] <= mx <= self.x_list[i] + 100 and self.y_list[i] <= my <= self.y_list[
                                i] + 100:
                                self.rotations[i] = (self.rotations[i] + 90) % 360
                                self.display_objects_on_background()
                                break

                    alpha_s = resized_image[:, :, 3] / 255.0
                    alpha_l = 1.0 - alpha_s

                    for c in range(0, 3):
                        self.frame[self.y_list[i]:self.y_list[i] + resized_image.shape[0],
                        self.x_list[i]:self.x_list[i] + resized_image.shape[1], c] = (
                                alpha_s * resized_image[:, :, c] + alpha_l * self.frame[self.y_list[i]:self.y_list[i] +
                                                                                                       resized_image.shape[
                                                                                                           0],
                                                                             self.x_list[i]:self.x_list[i] +
                                                                                            resized_image.shape[1], c])

                except cv2.error as e:
                    print(f"Error processing image at position {pos}: {e}")

            if self.text_info:
                self.frame = self.add_text_to_frame(self.frame, self.text_info)

            cv2.imshow('Floating Objects', self.frame)

            self.out.write(self.frame)

            if cv2.waitKey(30) & 0xFF == ord('q'):
                self.is_running = False

            frame_count += 1

        self.out.release()
        cv2.destroyAllWindows()

    import shutil

    def open_new_window6(self):
        try:
            self.final_running = True
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            fname = QFileDialog.getOpenFileName(self, "Open File", "./")
            if fname[0]:
                print(fname[0])
                file_path = urllib.parse.quote(fname[0])
                file_path = urllib.parse.unquote(file_path)
                video1 = cv2.VideoCapture(file_path)
                video2 = cv2.VideoCapture(file_path)
                video3 = cv2.VideoCapture(file_path)
                video4 = cv2.VideoCapture(file_path)

                if not video1.isOpened() or not video2.isOpened() or not video3.isOpened() or not video4.isOpened():
                    print("Error: One or more video files could not be opened.")
                    return

                self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
                self.out = cv2.VideoWriter('result_final.avi', self.fourcc, 20.0, (1600, 1600))

                if not self.out.isOpened():
                    print("Error: Could not open output file.")
                    return

                while self.final_running:
                    ret1, frame1 = video1.read()
                    ret2, frame2 = video2.read()
                    ret3, frame3 = video3.read()
                    ret4, frame4 = video4.read()

                    if not ret1 or not ret2 or not ret3 or not ret4:
                        break

                    frame1 = cv2.resize(frame1, (800, 800))
                    frame1 = frame1[500:, 400:600, :]
                    frame1 = cv2.resize(frame1, (800, 800))

                    frame4 = cv2.resize(frame4, (800, 800))
                    middle = frame4[120:500, 450:600, :]
                    frame4 = cv2.resize(middle, (800, 800))

                    frame2 = cv2.resize(frame2, (800, 800))
                    frame2 = frame2[0:500, :450, :]
                    frame2 = cv2.resize(frame2, (800, 800))

                    frame3 = cv2.resize(frame3, (800, 800))
                    right = frame3[10:510, 620:, :]
                    frame3 = cv2.resize(right, (800, 800))

                    rows, cols, _ = frame1.shape

                    pts1 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts2 = np.float32([[300, 250], [10, rows - 50], [cols - 300, 250], [cols - 10, rows - 50]])
                    pts3 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts4 = np.float32([[546, 9], [500, 250], [780, 11], [788, 750]])

                    pts5 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts6 = np.float32([[6, 12], [14, 742], [256, 4], [302, 248]])

                    pts7 = np.float32([[0, 0], [0, rows], [cols, 0], [cols, rows]])
                    pts8 = np.float32([[251, 4], [306, 250], [550, 7], [505, 247]])

                    mtrx1 = cv2.getPerspectiveTransform(pts1, pts2)
                    dst1 = cv2.warpPerspective(frame1, mtrx1, (cols, rows))

                    mtrx2 = cv2.getPerspectiveTransform(pts3, pts4)
                    dst2 = cv2.warpPerspective(frame3, mtrx2, (cols, rows))

                    dst2 = cv2.resize(dst2, (cols, rows))

                    combined_frame = cv2.add(dst1, dst2)

                    mtrx3 = cv2.getPerspectiveTransform(pts5, pts6)
                    dst3 = cv2.warpPerspective(frame2, mtrx3, (cols, rows))

                    combined_frame = cv2.add(combined_frame, dst3)

                    mtrx4 = cv2.getPerspectiveTransform(pts7, pts8)
                    dst4 = cv2.warpPerspective(frame4, mtrx4, (cols, rows))

                    combined_frame = cv2.add(combined_frame, dst4)

                    combined_frame = cv2.resize(combined_frame, (1600, 1600))

                    cv2.imshow("합성된 영상", combined_frame)

                    self.out.write(combined_frame)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                video1.release()
                video2.release()
                video3.release()
                video4.release()
                self.out.release()
                cv2.destroyAllWindows()

        except Exception as e:
            print(f"Error: {e}")

    def open_new_window4(self):

        if hasattr(self, 'is_running'):
            if self.is_running ==True:
                self.is_running = False
                save_path, _ = QFileDialog.getSaveFileName(self, "저장할 경로 선택", "", "AVI Files (*.avi);;All Files (*)")
                if save_path:
                    self.out.release()
                    shutil.move('output.avi', save_path)
                    self.is_running = False

                    return
                else:
                    self.out.release()
                    os.remove('output.avi')
                    self.is_running = False
                cv2.destroyAllWindows()


        if hasattr(self,'final_running'):
            if self.final_running ==True:
                self.final_running=False
                save_path, _ = QFileDialog.getSaveFileName(self, "저장할 경로 선택", "", "AVI Files (*.avi);;All Files (*)")
                if save_path:
                    self.out.release()
                    shutil.move('result_final.avi', save_path)
                    self.final_running = False

                    return
                else:
                    self.out.release()
                    os.remove('result_final.avi')
                    self.final_running = False
                cv2.destroyAllWindows()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    startWin = StartWindow()
    sys.exit(app.exec_())
