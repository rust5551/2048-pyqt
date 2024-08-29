import random
import sys
import sqlite3
import os
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QDialog, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, QRectF


class Tile: # Клетка
    def __init__(self, value):
        self.value = value


class NameInputDialog(QDialog): # Диалоговое окно для ввода никнейма
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('')
        self.setGeometry(200, 200, 200, 200)

        self.label = QLabel("Введите ваш никнейм", self)
        self.label.move(20, 10)
        self.name_input = QLineEdit("", self)
        self.name_input.move(20, 30)
        self.name_input.setMaxLength(10)
        self.button = QPushButton("ОК", self)
        self.button.resize(60, 30)
        self.button.move(60, 60)
        self.button.clicked.connect(self.enter)

    def enter(self):
        if self.name_input.text():
            self.name = self.name_input.text()
            self.close()


class Game(QWidget): # Сама игра
    def __init__(self):
        super().__init__()
        dlg = NameInputDialog()
        dlg.exec()
        self.name = dlg.name

        if os.path.isfile("top_players"):
            self.con = sqlite3.connect("top_players") # Подключение к БД
            self.cur = self.con.cursor()
        else:
            self.con = sqlite3.connect("top_players")
            self.con.execute("""CREATE TABLE players (
                                Name  TEXT (10) UNIQUE ON CONFLICT REPLACE,
                                Score INTEGER);""")
            self.cur = self.con.cursor()

        self.initUI()
        self.top_players = []
        self.game_running = False
        self.leaderboard_show = False
        self.highscore = 0
        self.score = 0
        self.brushes = {
            'bg': QBrush(QColor(0xfaf8ef)),
            'button': QBrush(QColor(0x8f7a66)),
            'gameover': QBrush(QColor(225, 213, 202, 170)),
            0: QBrush(QColor(0xcdc1b4)),
            1: QBrush(QColor(0xbbada0)),
            2: QBrush(QColor(0xeee4da)),
            4: QBrush(QColor(0xede0c8)),
            8: QBrush(QColor(0xf2b179)),
            16: QBrush(QColor(0xf59563)),
            32: QBrush(QColor(0xf67c5f)),
            64: QBrush(QColor(0xf65e3b)),
            128: QBrush(QColor(0xedcf72)),
            256: QBrush(QColor(0xedcc61)),
            512: QBrush(QColor(0xedc850)),
            1024: QBrush(QColor(0xedc53f)),
            2048: QBrush(QColor(0xedc22e)),
        }
        self.bg_x = 175
        self.score_x = 175
        self.highscore_x = 285
        self.leaderboard_open_x = 395
        self.reset_x = 525
        self.reset2_x = 300
        self.leaderboard_x = 530
        self.score_rect = QRectF(self.score_x, 20, 100, 60)
        self.highscore_rect = QRectF(self.highscore_x, 20, 100, 60)
        self.leaderboard_open = QRectF(self.leaderboard_open_x, 20, 120, 60)
        self.reset_rect = QRectF(self.reset_x, 20, 100, 60)
        self.reset2_rect = QRectF(self.reset2_x, 400, 200, 60)
        self.tiles_bg = QRectF(self.bg_x, 125, 450, 450)
        self.leaderboard_rect = QRectF(self.leaderboard_x, 55, 210, 500)
        self.players = QRectF(540, 30, 190, 60)
        self.light_pen = QPen(QColor(0xf9f6f2))
        self.dark_pen = QPen(QColor(0x776e65))
        self.read_from_db()

    def initUI(self):
        self.setGeometry(400, 75, 800, 600)
        self.setFixedSize(800, 600)
        self.setWindowTitle('2048')

    def read_from_db(self): # Чтение данных из БД и их запись в переменную top_players
        self.result = self.cur.execute("""SELECT * FROM players
                                    ORDER BY Score DESC
                                    LIMIT 7;""").fetchall()
        for player in self.result:
            self.top_players.append(player)
        self.top_players = sorted(self.top_players, key=lambda x: x[1], reverse=True)

    def write_to_db(self): # Запись данных в БД
        names = [player[0] for player in self.result]
        scores = [player[1] for player in self.result]
        if self.name not in names:
            self.cur.execute(f"""INSERT INTO players (name, score)
             VALUES ("{self.name}", {self.highscore})""")
            self.con.commit()
        elif self.name in names and self.highscore > scores[names.index(self.name)]:
            self.cur.execute(f"""REPLACE INTO players (name, score)
             VALUES ("{self.name}", {self.highscore})""")
            self.con.commit()

    def keyPressEvent(self, k): # Обработчик нажатий на клавиатуру
        if self.game_running:
            if k.key() in (87, 1062, 16777235):  # w
                self.move_up()
            elif k.key() in (65, 1060, 16777234):  # a
                self.move_left()
            elif k.key() in (83, 1067, 16777237):  # s
                self.move_down()
            elif k.key() in (68, 1042, 16777236):  # d
                self.move_right()
            self.update()
            if self.score > self.highscore:
                self.highscore = self.score
                self.record()
            self.game_over()

    def closeEvent(self, event): # Запись данных при закрытии окна
        self.write_to_db()

    def start_game(self): # Начало игры
        self.score = 0
        self.record()
        self.tiles = [[Tile(0) for _ in range(4)] for _ in range(4)]
        self.spawn()
        self.spawn()
        self.game_running = True
        self.update()
        self.write_to_db()

    def record(self): # Добавление имени и лучшего счёта в список top_players
        recorded = False
        for i in self.top_players:
            if self.name == i[0]:
                if self.highscore > i[1]:
                    self.top_players[self.top_players.index(i)] = (self.name, self.highscore)
                recorded = True
                break
        if not recorded:
            self.top_players.append((self.name, self.highscore))

    def mousePressEvent(self, e): # Сохранение позиции курсора при нажатии на кнопку мыши
        self.lastPoint = e.pos()

    def mouseReleaseEvent(self, e): # Проверка, была ли нажата кнопка на экране
        # Новая игра
        if self.reset_rect.contains(self.lastPoint.x(), self.lastPoint.y()) and self.reset_rect.contains(e.pos().x(), e.pos().y()): 
            self.start_game()
        # Таблица лидеров
        elif self.leaderboard_open.contains(self.lastPoint.x(), self.lastPoint.y()) and self.leaderboard_open.contains(e.pos().x(), e.pos().y()):
            if self.leaderboard_show:
                self.leaderboard_show = False
                self.bg_x = 175
                self.score_x = 175
                self.highscore_x = 285
                self.leaderboard_open_x = 395
                self.reset_x = 525
                self.reset2_x = 300
            else:
                self.leaderboard_show = True
                self.bg_x = 25
                self.score_x = 25
                self.highscore_x = 135
                self.leaderboard_open_x = 245
                self.reset_x = 375
                self.reset2_x = 150
            self.score_rect = QRectF(self.score_x, 20, 100, 60)
            self.highscore_rect = QRectF(self.highscore_x, 20, 100, 60)
            self.leaderboard_open = QRectF(self.leaderboard_open_x, 20, 120, 60)
            self.reset_rect = QRectF(self.reset_x, 20, 100, 60)
            self.reset2_rect = QRectF(self.reset2_x, 400, 200, 60)
            self.tiles_bg = QRectF(self.bg_x, 125, 450, 450)
            self.update()
        # Новая игра
        elif self.reset2_rect.contains(self.lastPoint.x(), self.lastPoint.y()) and self.reset2_rect.contains(e.pos().x(), e.pos().y()):
            self.start_game()

    def paintEvent(self, event): # Отрисовка интерфейса
        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.brushes['bg'])
        painter.drawRect(self.rect())
        painter.setBrush(self.brushes[1])
        painter.drawRoundedRect(self.score_rect, 10, 10)
        painter.drawRoundedRect(self.highscore_rect, 10, 10)
        painter.drawRoundedRect(self.tiles_bg, 10, 10)
        painter.setBrush(self.brushes['button'])
        painter.drawRoundedRect(self.leaderboard_open, 10, 10)
        painter.drawRoundedRect(self.reset_rect, 10, 10)
        painter.setFont(QtGui.QFont('Arial', 13, 100))
        painter.setPen(self.light_pen)
        painter.drawText(self.score_rect, f'СЧЁТ\n{self.score}', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
        painter.drawText(self.highscore_rect, f'ЛУЧШИЙ\n{self.highscore}', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
        painter.drawText(self.reset_rect, 'НОВАЯ ИГРА', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
        painter.drawText(self.leaderboard_open, 'ТАБЛИЦА ЛИДЕРОВ', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
        painter.setFont(QtGui.QFont('Arial', 30, 100))
        for row in range(4): # Отрисовка поля
            for col in range(4):
                painter.setPen(Qt.NoPen)
                tile_value = self.tiles[row][col].value
                painter.setBrush(self.brushes[tile_value])
                tile = QRectF(self.bg_x + (col + 1) * 10 + 100 * col, 125 + (row + 1) * 10 + 100 * row, 100, 100)
                painter.drawRoundedRect(tile, 5, 5)
                if tile_value != 0:
                    painter.setPen(self.dark_pen if tile_value < 8 else self.light_pen)
                    painter.drawText(tile, str(tile_value), QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
        if self.leaderboard_show: # Отрисовка таблицы лидеров
            self.top_players = sorted(self.top_players, key=lambda x: x[1], reverse=True)
            painter.setBrush(self.brushes[1])
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.leaderboard_rect, 10, 10)
            painter.setBrush(self.brushes[0])
            for i in range(7):
                try:
                    painter.setPen(Qt.NoPen)
                    player = QRectF(self.leaderboard_x + 10, 65 + i * 70, 190, 60)
                    painter.drawRoundedRect(player, 10, 10)
                    painter.setFont(QtGui.QFont('Arial', 14, 100))
                    painter.setPen(self.dark_pen)
                    painter.drawText(player, f'{self.top_players[i][0]}:\n{self.top_players[i][1]}', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
                except:
                    pass

        if self.game_running is False: # Отрисовка экрана конца игры
            painter.setFont(QtGui.QFont('Arial', 30, 100))
            painter.setBrush(self.brushes['gameover'])
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.tiles_bg, 10, 10)
            painter.setBrush(self.brushes['button'])
            painter.drawRoundedRect(self.reset2_rect, 10, 10)
            painter.setPen(self.dark_pen)
            painter.drawText(self.tiles_bg, 'КОНЕЦ ИГРЫ', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))
            painter.setPen(self.light_pen)
            painter.setFont(QtGui.QFont('Arial', 15, 100))
            painter.drawText(self.reset2_rect, 'НОВАЯ ИГРА', QtGui.QTextOption(Qt.AlignmentFlag.AlignCenter))

    def spawn(self): # Создание клеток
        while True:
            row = random.randint(0, 3)
            col = random.randint(0, 3)
            if self.tiles[row][col].value == 0:
                self.tiles[row][col].value = random.choice([2, 2, 2, 2, 4])
                break

    def game_over(self): # Проверка на конец игры
        empty_tiles = []
        not_over = False
        win = False
        for row in self.tiles:
            for col in row:
                if col.value == 2048:
                    win = True
                if col.value == 0:
                    empty_tiles.append(1)
        if empty_tiles is False:
            for i in range(4):
                for j in range(4):
                    if i < 3 and self.tiles[i][j].value == self.tiles[i + 1][j].value:
                        not_over = True
                        break
                    if j < 3 and self.tiles[i][j].value == self.tiles[i][j + 1].value:
                        not_over = True
                        break
            if (not not_over) or win:
                self.game_running = False
                self.write_to_db()

    def move_up(self): # Движение вверх
        moved = False
        for _ in range(3):
            for i in range(3, 0, -1):
                for j in range(len(self.tiles[i])):
                    if self.tiles[i - 1][j].value != 0 and self.tiles[i][j].value == self.tiles[i - 1][j].value:
                        self.tiles[i - 1][j].value *= 2
                        self.score += self.tiles[i - 1][j].value
                        self.tiles[i][j].value = 0
                        moved = True
                    elif self.tiles[i - 1][j].value == 0 and self.tiles[i][j].value != 0:
                        self.tiles[i - 1][j].value = self.tiles[i][j].value
                        self.tiles[i][j].value = 0
                        moved = True
        if moved:
            self.spawn()

    def move_left(self): # Движение влево
        moved = False
        for _ in range(3):
            for i in range(4):
                for j in range(3, 0, -1):
                    if self.tiles[i][j - 1].value != 0 and self.tiles[i][j].value == self.tiles[i][j - 1].value:
                        self.tiles[i][j - 1].value *= 2
                        self.score += self.tiles[i][j - 1].value
                        self.tiles[i][j].value = 0
                        moved = True
                    elif self.tiles[i][j - 1].value == 0 and self.tiles[i][j].value != 0:
                        self.tiles[i][j - 1].value = self.tiles[i][j].value
                        self.tiles[i][j].value = 0
                        moved = True
        if moved:
            self.spawn()

    def move_down(self): # Движение вниз
        moved = False
        for _ in range(3):
            for i in range(3):
                for j in range(len(self.tiles[i])):
                    if self.tiles[i + 1][j].value != 0 and self.tiles[i][j].value == self.tiles[i + 1][j].value:
                        self.tiles[i + 1][j].value *= 2
                        self.score += self.tiles[i + 1][j].value
                        self.tiles[i][j].value = 0
                        moved = True
                    elif self.tiles[i + 1][j].value == 0 and self.tiles[i][j].value != 0:
                        self.tiles[i + 1][j].value = self.tiles[i][j].value
                        self.tiles[i][j].value = 0
                        moved = True
        if moved:
            self.spawn()

    def move_right(self): # Движение вправо
        moved = False
        for _ in range(3):
            for i in range(4):
                for j in range(3):
                    if self.tiles[i][j + 1].value != 0 and self.tiles[i][j].value == self.tiles[i][j + 1].value:
                        self.tiles[i][j + 1].value *= 2
                        self.score += self.tiles[i][j + 1].value
                        self.tiles[i][j].value = 0
                        moved = True
                    elif self.tiles[i][j + 1].value == 0 and self.tiles[i][j].value != 0:
                        self.tiles[i][j + 1].value = self.tiles[i][j].value
                        self.tiles[i][j].value = 0
                        moved = True
        if moved:
            self.spawn()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Game()
    ex.show()
    ex.start_game()
    sys.exit(app.exec())
