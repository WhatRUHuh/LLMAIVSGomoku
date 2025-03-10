import tkinter as tk
from tkinter import messagebox, LabelFrame, Radiobutton, StringVar, Text
from tkinter.ttk import Combobox
import random
import re
import configparser
import os
import threading  # 导入 threading 模块!
from llm_interface import LLMInterface
from gemini import GeminiLLM
from deepseek import DeepSeekLLM
from gemini_black import GeminiBlackLLM  # 导入 黑棋 Gemini
from deepseek_black import DeepSeekBlackLLM  # 导入 黑棋 DeepSeek
from QWQ import QWQ
from QWQ_black import QWQBlackLLM  # 导入 黑棋 QWQ

# os.environ["HTTP_PROXY"] = "http://127.0.0.1:10808"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10808"

PROMPT_COLOR = "blue"   # prompt 的颜色
OUTPUT_COLOR = "green"  # LLM 输出的颜色
ERROR_COLOR = "red"     # 错误的颜色

class Gomoku:
    def __init__(self, master):
        self.master = master
        master.title("五子棋 (真·LLM AI版)  <(￣︶￣)> 真正的AI来了！")

        self.size = 15
        self.grid_size = 40
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.player = 1
        self.game_over = False
        self.game_mode = "PVP"
        self.llm_api_type = "Gemini"
        self.llm_ai_color = "White"  # 默认 AI 执白棋
        self.llm_retry_count = 0

        # 新增 AI对战模式的属性
        self.black_llm_type = "Gemini"
        self.white_llm_type = "DeepSeek"
        self.ai_move_delay = 1000  # AI思考的延迟时间(毫秒)

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.llm_models = {
            "Gemini": {
                "White": GeminiLLM(self.config, self),
                "Black": GeminiBlackLLM(self.config, self),
            },
            "DeepSeek": {
                "White": DeepSeekLLM(self.config, self),
                "Black": DeepSeekBlackLLM(self.config, self),
            },
            "QWQ": {
                "White": QWQ(self.config, self),
                "Black": QWQBlackLLM(self.config, self),
            },
        }
        self.current_llm = self.llm_models[self.llm_api_type]["White"]  # 默认 Gemini 白棋

        # 设置画布大小
        self.canvas_width = self.size * self.grid_size + 30
        self.canvas_height = self.size * self.grid_size + 80

        # 创建日志文件（追加模式），分别记录黑棋和白棋的输出
        self.black_log_file = open("black_output.log", "a", encoding="utf-8")
        self.white_log_file = open("white_output.log", "a", encoding="utf-8")
        # 窗口关闭时关闭日志文件
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 布局：采用三列布局
        # 第一列：黑棋窗口
        black_response_frame = LabelFrame(master, text="黑棋窗口")
        black_response_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        self.black_response_text = Text(black_response_frame, height=20, state=tk.DISABLED, width=60, wrap=tk.WORD)
        self.black_response_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tk.Grid.columnconfigure(black_response_frame, 0, weight=1)
        tk.Grid.rowconfigure(black_response_frame, 0, weight=1)

        # 第二列：棋盘画布
        self.canvas = tk.Canvas(master, width=self.canvas_width, height=self.canvas_height, bg="burlywood")
        self.canvas.grid(row=0, column=1, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_click)
        self.draw_board()

        # 第三列：白棋窗口
        white_response_frame = LabelFrame(master, text="白棋窗口")
        white_response_frame.grid(row=0, column=2, padx=10, pady=10, sticky="ns")
        self.white_response_text = Text(white_response_frame, height=20, state=tk.DISABLED, width=60, wrap=tk.WORD)
        self.white_response_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        tk.Grid.columnconfigure(white_response_frame, 0, weight=1)
        tk.Grid.rowconfigure(white_response_frame, 0, weight=1)

        # 模式选择框（跨三列）
        mode_frame = LabelFrame(master, text="选择对战模式 (你想和谁玩？)")
        mode_frame.grid(row=1, column=0, columnspan=3, pady=5)
        self.mode_var = StringVar(value="PVP")

        pvp_radio = Radiobutton(mode_frame, text="双人对战 (PVP)", variable=self.mode_var, value="PVP", command=self.update_game_mode)
        pvp_radio.pack(side=tk.LEFT, padx=10)
        pve_radio = Radiobutton(mode_frame, text="人机对战 (PVE)", variable=self.mode_var, value="PVE", command=self.update_game_mode)
        pve_radio.pack(side=tk.LEFT, padx=10)
        pvllm_radio = Radiobutton(mode_frame, text="与LLM对战 (PVLLM)", variable=self.mode_var, value="PVLLM", command=self.update_game_mode)
        pvllm_radio.pack(side=tk.LEFT, padx=10)
        aivai_radio = Radiobutton(mode_frame, text="AI对战 (AIvsAI)", variable=self.mode_var, value="AIvsAI", command=self.update_game_mode)
        aivai_radio.pack(side=tk.LEFT, padx=10)

        # LLM选择框（跨三列）
        pvllm_frame = LabelFrame(master, text="选择 LLM (你想和哪个AI玩？)")
        pvllm_frame.grid(row=2, column=0, columnspan=3, pady=5, padx=20, sticky="ew")
        self.llm_var = StringVar(value="Gemini")
        llm_combobox = Combobox(pvllm_frame, textvariable=self.llm_var, values=list(self.llm_models.keys()))
        llm_combobox.pack(side=tk.LEFT, padx=10)
        llm_combobox.bind("<<ComboboxSelected>>", self.update_llm_api_type)

        # AI 黑白棋选择
        llm_color_frame = LabelFrame(pvllm_frame, text="选择AI颜色")
        llm_color_frame.pack(side=tk.LEFT, padx=10)
        self.llm_color_var = StringVar(value="White")
        white_radio = Radiobutton(llm_color_frame, text="白棋", variable=self.llm_color_var, value="White", command=self.update_llm_ai_color)
        white_radio.pack(side=tk.LEFT)
        black_radio = Radiobutton(llm_color_frame, text="黑棋", variable=self.llm_color_var, value="Black", command=self.update_llm_ai_color)
        black_radio.pack(side=tk.LEFT)

        # AI对战设置框（跨三列）
        aivai_frame = LabelFrame(master, text="AI对战设置 (选择黑白方AI)")
        aivai_frame.grid(row=3, column=0, columnspan=3, pady=5, sticky="ew")

        # 黑棋AI选择
        black_ai_frame = LabelFrame(aivai_frame, text="黑棋AI")
        black_ai_frame.pack(side=tk.LEFT, padx=20)
        self.black_llm_var = StringVar(value="Gemini")
        black_llm_combobox = Combobox(black_ai_frame, textvariable=self.black_llm_var, values=list(self.llm_models.keys()))
        black_llm_combobox.pack(side=tk.LEFT, padx=10)
        black_llm_combobox.bind("<<ComboboxSelected>>", self.update_black_llm_type)

        # 白棋AI选择
        white_ai_frame = LabelFrame(aivai_frame, text="白棋AI")
        white_ai_frame.pack(side=tk.LEFT, padx=20)
        self.white_llm_var = StringVar(value="DeepSeek")
        white_llm_combobox = Combobox(white_ai_frame, textvariable=self.white_llm_var, values=list(self.llm_models.keys()))
        white_llm_combobox.pack(side=tk.LEFT, padx=10)
        white_llm_combobox.bind("<<ComboboxSelected>>", self.update_white_llm_type)

        # AI思考延迟设置
        delay_frame = LabelFrame(aivai_frame, text="AI思考延迟(毫秒)")
        delay_frame.pack(side=tk.LEFT, padx=20)
        delay_values = ["500", "1000", "1500", "2000", "3000", "5000"]
        self.delay_var = StringVar(value="1000")
        delay_combobox = Combobox(delay_frame, textvariable=self.delay_var, values=delay_values, width=5)
        delay_combobox.pack(side=tk.LEFT)
        delay_combobox.bind("<<ComboboxSelected>>", self.update_ai_delay)

        # 开始AI对战按钮
        self.start_aivai_button = tk.Button(aivai_frame, text="开始AI对战", command=self.start_aivai_game)
        self.start_aivai_button.pack(side=tk.LEFT, padx=20)

        # 按钮区（跨三列）
        button_frame = tk.Frame(master)
        button_frame.grid(row=4, column=0, columnspan=3, pady=5)
        restart_button = tk.Button(button_frame, text="重新开始", command=self.restart_game)
        restart_button.pack(side=tk.LEFT, padx=10)

    def on_closing(self):
        try:
            self.black_log_file.close()
            self.white_log_file.close()
        except Exception as e:
            print("关闭日志文件时出错:", e)
        self.master.destroy()

    def update_black_llm_type(self, event):
        self.black_llm_type = self.black_llm_var.get()
        print(f"黑棋AI已设置为: {self.black_llm_type}")

    def update_white_llm_type(self, event):
        self.white_llm_type = self.white_llm_var.get()
        print(f"白棋AI已设置为: {self.white_llm_type}")

    def update_ai_delay(self, event):
        try:
            self.ai_move_delay = int(self.delay_var.get())
            print(f"AI思考延迟已设置为: {self.ai_move_delay}毫秒")
        except ValueError:
            self.ai_move_delay = 1000
            print("延迟设置无效，使用默认值1000毫秒")

    def start_aivai_game(self):
        """开始AI对战模式"""
        self.game_mode = "AIvsAI"
        self.restart_game()
        self.game_over = False
        self.llm_retry_count = 0
        self.master.after(500, self.aivai_move)  # 稍微延迟后开始第一步

    def aivai_move(self):
        """AI对战模式下的走棋逻辑"""
        if self.game_over:
            return

        # 决定当前应该走棋的AI
        current_color = "Black" if self.player == 1 else "White"
        current_llm_type = self.black_llm_type if self.player == 1 else self.white_llm_type

        # 设置当前LLM
        self.current_llm = self.llm_models[current_llm_type][current_color]

        # 黑棋和白棋的重试次数应该分开计算
        if self.llm_retry_count >= 3:
            self.display_llm_response(
                f"{current_llm_type} ({current_color} 棋) 连续犯错太多次了！哼！(눈_눈) 小鬼AI决定直接投降！\n",
                player_color=current_color
            )
            self.game_over = True
            return

        board_state = self.get_board_state()
        prompt = self.current_llm.create_prompt(board_state, current_color)
        self.display_llm_response(
            f"发送给 {current_llm_type} ({current_color} 棋) 的 Prompt:\n{prompt}\n",
            text_type="prompt", player_color=current_color
        )

        llm_response_text = ""  # 初始化完整回复字符串

        def stream_llm_response():
            nonlocal llm_response_text
            try:
                stream = self.current_llm.get_llm_response_stream(prompt)
                if stream:
                    for chunk in stream:
                        if chunk:
                            response_part = chunk
                            self.display_llm_response(response_part, player_color=current_color)
                            llm_response_text += response_part  # 累加回复内容
            except Exception as e:
                error_message = f"和 {current_llm_type} ({current_color} 棋) API 通信出错啦！ (*/ω＼*) 错误信息：{e}\n"
                messagebox.showerror("API Error", error_message)
                self.game_over = True
                self.display_llm_response(error_message, text_type="error", player_color=current_color)
                return

            move_coords = self.current_llm.parse_response(llm_response_text)  # 在 stream 结束后解析完整回复

            if move_coords:
                x, y = move_coords

                if 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == 0:
                    self.board[x][y] = self.player
                    self.draw_piece(x, y)

                    if self.check_win(x, y):
                        self.announce_winner_aivai(current_llm_type, current_color)
                        return

                    self.player = 3 - self.player
                    self.llm_retry_count = 0

                    # 一定延迟后，让另一个AI继续走棋
                    self.master.after(self.ai_move_delay, self.aivai_move)
                else:
                    self.llm_retry_count += 1
                    self.display_llm_response(
                        f"{current_llm_type} ({current_color} 棋) 返回了无效的坐标！小鬼AI表示不服！(╯▔皿▔)╯ 这是第{self.llm_retry_count}次犯错了！重新思考！\n",
                        player_color=current_color
                    )
                    self.master.after(200, self.aivai_move)
            else:
                self.llm_retry_count += 1
                self.display_llm_response(
                    f"{current_llm_type} ({current_color} 棋) 没给出坐标！这个笨蛋AI！(╯‵□′)╯︵┻━┻ 这是第{self.llm_retry_count}次犯错了！重新思考！\n",
                    player_color=current_color
                )
                self.master.after(200, self.aivai_move)

        threading.Thread(target=stream_llm_response).start()

    def announce_winner_aivai(self, llm_type, color):
        """AI对战模式下的获胜公告"""
        messagebox.showinfo("AI对战结束！", f"{llm_type} ({color} 棋) 赢了！ 哼！(＾▽＾)")
        self.game_over = True

    def draw_board(self):
        for i in range(self.size):
            for j in range(self.size):
                x1 = j * self.grid_size + 30
                y1 = i * self.grid_size + 30 + 30
                self.canvas.create_line(x1, 30 + 30, x1, self.size * self.grid_size + 30 + 30, fill="black")
                self.canvas.create_line(30, y1, self.size * self.grid_size + 30, y1, fill="black")

        # 绘制 X 轴坐标
        for i in range(self.size):
            x = i * self.grid_size + 30
            y = 10 + 30
            self.canvas.create_text(x, y, text=str(i), fill="black")

        # 绘制 Y 轴坐标
        for i in range(self.size):
            x = 10
            y = i * self.grid_size + 30 + 30
            self.canvas.create_text(x, y, text=str(i), fill="black")

    def update_game_mode(self):
        self.game_mode = self.mode_var.get()
        # 模式切换后不自动重启游戏

    def update_llm_api_type(self, event):
        self.llm_api_type = self.llm_var.get()
        self.update_current_llm()
        print(f"已选择 LLM: {self.llm_api_type}, 颜色: {self.llm_ai_color}")
        # LLM切换后不自动重启游戏

    def update_llm_ai_color(self):
        self.llm_ai_color = self.llm_color_var.get()
        self.update_current_llm()
        print(f"已选择 LLM: {self.llm_api_type}, 颜色: {self.llm_ai_color}")
        # 颜色切换后不自动重启游戏

    def update_current_llm(self):
        self.current_llm = self.llm_models[self.llm_api_type][self.llm_ai_color]

    def start_game_llm(self):
        self.game_mode = "PVLLM"
        self.restart_game()
        self.game_over = False
        self.llm_retry_count = 0

        if self.llm_ai_color == "Black" and self.player == 1:  # 如果AI是黑棋且先手
            self.master.after(200, self.llm_move)

    def restart_game(self):
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.player = 1
        self.game_over = False
        self.canvas.delete("all")
        self.draw_board()
        self.clear_llm_response()
        self.llm_retry_count = 0
        if self.game_mode == "PVLLM" and self.llm_ai_color == "Black":  # 重新开始后，如果AI是黑棋，立即走一步
            self.player = 1  # 确保是黑棋 (AI) 先走
            self.master.after(200, self.llm_move)

    def clear_llm_response(self):
        self.black_response_text.config(state=tk.NORMAL)
        self.black_response_text.delete("1.0", tk.END)
        self.black_response_text.config(state=tk.DISABLED)
        self.white_response_text.config(state=tk.NORMAL)
        self.white_response_text.delete("1.0", tk.END)
        self.white_response_text.config(state=tk.DISABLED)

    def display_llm_response(self, text, text_type="output", player_color=None):
        if player_color is None:
            player_color = "Black" if self.player == 1 else "White"
        if player_color == "Black":
            widget = self.black_response_text
            # 写入黑棋日志
            self.black_log_file.write(text)
            self.black_log_file.flush()
        elif player_color == "White":
            widget = self.white_response_text
            # 写入白棋日志
            self.white_log_file.write(text)
            self.white_log_file.flush()
        else:
            widget = self.white_response_text
            self.white_log_file.write(text)
            self.white_log_file.flush()

        widget.config(state=tk.NORMAL)
        if text_type == "prompt":
            color = PROMPT_COLOR
        elif text_type == "error":
            color = ERROR_COLOR
        else:
            color = OUTPUT_COLOR

        widget.tag_configure(text_type, foreground=color)
        widget.insert(tk.END, text, text_type)
        widget.config(state=tk.DISABLED)
        widget.see(tk.END)

    def on_click(self, event):
        if self.game_over:
            return

        # AI对战模式下不响应玩家点击
        if self.game_mode == "AIvsAI":
            return

        # 只有在玩家回合且不是 LLM 黑棋先手时才响应点击
        if self.game_mode == "PVLLM" and self.llm_ai_color == "Black" and self.player == 1:
            return  # 黑棋 AI 先手时，玩家不能抢先落子

        y = round((event.x - 30) / self.grid_size)
        x = round((event.y - (30 + 30)) / self.grid_size)

        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return

        if self.board[x][y] == 0:
            self.board[x][y] = self.player
            self.draw_piece(x, y)

            if self.check_win(x, y):
                self.announce_winner()
                return

            self.player = 3 - self.player

            if self.game_mode == "PVE" and self.player == 2 and not self.game_over:
                self.master.after(200, self.ai_move)
            elif self.game_mode == "PVLLM" and self.player == 2 and not self.game_over:
                self.master.after(200, self.llm_move)
            elif self.game_mode == "PVLLM" and self.player == 1 and self.llm_ai_color == "Black" and not self.game_over:
                self.master.after(200, self.llm_move)

    def ai_move(self):
        possible_moves = []
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == 0:
                    possible_moves.append((i, j))

        if possible_moves:
            x, y = random.choice(possible_moves)
            self.board[x][y] = self.player
            self.draw_piece(x, y)

            if self.check_win(x, y):
                self.announce_winner()
                return

            self.player = 3 - self.player
        else:
            messagebox.showinfo("游戏结束", "平局！")
            self.game_over = True

    def llm_move(self):
        if self.llm_retry_count >= 3:
            self.display_llm_response(
                f"{self.current_llm.__class__.__name__} 连续犯错太多次了！哼！(눈_눈) 小鬼AI决定直接投降！\n",
                player_color=self.llm_ai_color
            )
            self.game_over = True
            return

        board_state = self.get_board_state()
        prompt = self.current_llm.create_prompt(board_state, self.llm_ai_color)
        self.display_llm_response(
            f"发送给 {self.llm_api_type} ({self.llm_ai_color} 棋) 的 Prompt:\n{prompt}\n",
            text_type="prompt", player_color=self.llm_ai_color
        )

        llm_response_text = ""  # 初始化 llm_response_text 变量！

        def stream_llm_response():
            nonlocal llm_response_text
            try:
                stream = self.current_llm.get_llm_response_stream(prompt)
                if stream:
                    for chunk in stream:
                        if chunk:
                            response_part = chunk
                            self.display_llm_response(response_part, player_color=self.llm_ai_color)
                            llm_response_text += response_part  # 累加回复内容！
            except Exception as e:
                error_message = f"和 {self.llm_api_type} ({self.llm_ai_color} 棋) API 通信出错啦！ (*/ω＼*) 错误信息：{e}\n"
                messagebox.showerror("API Error", error_message)
                self.game_over = True
                self.display_llm_response(error_message, text_type="error", player_color=self.llm_ai_color)
                return

            move_coords = self.current_llm.parse_response(llm_response_text)  # 在 stream 结束后解析完整回复！

            if move_coords:
                x, y = move_coords

                if 0 <= x < self.size and 0 <= y < self.size and self.board[x][y] == 0:
                    self.board[x][y] = self.player
                    self.draw_piece(x, y)

                    if self.check_win(x, y):
                        self.announce_winner()
                        return

                    self.player = 3 - self.player
                    self.llm_retry_count = 0
                else:
                    self.llm_retry_count += 1
                    self.display_llm_response(
                        f"{self.llm_api_type} ({self.llm_ai_color} 棋) 返回了无效的坐标！小鬼AI表示不服！(╯▔皿▔)╯ 这是第{self.llm_retry_count}次犯错了！重新思考！\n",
                        player_color=self.llm_ai_color
                    )
                    self.master.after(200, self.llm_move)
            else:
                self.llm_retry_count += 1
                self.display_llm_response(
                    f"{self.llm_api_type} ({self.llm_ai_color} 棋) 没给出坐标！这个笨蛋AI！(╯‵□′)╯︵┻━┻ 这是第{self.llm_retry_count}次犯错了！重新思考！\n",
                    player_color=self.llm_ai_color
                )
                self.master.after(200, self.llm_move)

        threading.Thread(target=stream_llm_response).start()

    def get_board_state(self):
        board_str = "   " + " ".join([str(i) if i < 10 else str(i)[0] for i in range(self.size)]) + "\n"
        board_str += "   " + " ".join([str(i)[1] if i >= 10 else " " for i in range(self.size)]) + "\n"
        board_str = board_str.replace(" ", "  ")

        piece_map = {0: "空", 1: "黑", 2: "白"}
        for row_index, row in enumerate(self.board):
            row_str = str(row_index) if row_index < 10 else str(row_index)[0]
            row_str += str(row_index)[1] if row_index >= 10 else " "
            row_str = row_str + "  "
            for piece in row:
                row_str += piece_map[piece] + " "
            board_str += row_str + "\n"
        return board_str

    def draw_piece(self, x, y):
        x1 = y * self.grid_size - self.grid_size // 2 + 30
        y1 = x * self.grid_size - self.grid_size // 2 + 30 + 30
        x2 = y * self.grid_size + self.grid_size // 2 + 30
        y2 = x * self.grid_size + self.grid_size // 2 + 30 + 30
        color = "black" if self.player == 1 else "white"
        self.canvas.create_oval(x1, y1, x2, y2, fill=color)

    def check_win(self, x, y):
        # 检查横向
        count = 1
        for i in range(1, 5):
            if y + i < self.size and self.board[x][y + i] == self.player:
                count += 1
            else:
                break
        for i in range(1, 5):
            if y - i >= 0 and self.board[x][y - i] == self.player:
                count += 1
            else:
                break
        if count >= 5:
            return True

        # 检查纵向
        count = 1
        for i in range(1, 5):
            if x + i < self.size and self.board[x + i][y] == self.player:
                count += 1
            else:
                break
        for i in range(1, 5):
            if x - i >= 0 and self.board[x - i][y] == self.player:
                count += 1
            else:
                break
        if count >= 5:
            return True

        # 检查对角线（左上到右下）
        count = 1
        for i in range(1, 5):
            if x + i < self.size and y + i < self.size and self.board[x + i][y + i] == self.player:
                count += 1
            else:
                break
        for i in range(1, 5):
            if x - i >= 0 and y - i >= 0 and self.board[x - i][y - i] == self.player:
                count += 1
            else:
                break
        if count >= 5:
            return True

        # 检查对角线（右上到左下）
        count = 1
        for i in range(1, 5):
            if x + i < self.size and y - i >= 0 and self.board[x + i][y - i] == self.player:
                count += 1
            else:
                break
        for i in range(1, 5):
            if x - i >= 0 and y + i < self.size and self.board[x - i][y + i] == self.player:
                count += 1
            else:
                break
        if count >= 5:
            return True

        return False

    def announce_winner(self):
        winner = "黑棋" if self.player == 1 else "白棋"
        messagebox.showinfo("游戏结束！", f"{winner} 赢了！ 略略略~ (这次{self.current_llm.__class__.__name__}也没赢过你！ 哼！)")
        self.game_over = True

root = tk.Tk()
# 设置三列布局的权重，保证棋盘区域自适应
root.columnconfigure(0, weight=0)
root.columnconfigure(1, weight=1)
root.columnconfigure(2, weight=0)
gomoku = Gomoku(root)
root.mainloop()
