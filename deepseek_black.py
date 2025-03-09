# deepseek_black.py
import os
from openai import OpenAI
from llm_interface import LLMInterface
import re

class DeepSeekBlackLLM(LLMInterface): # 类名改成 DeepSeekBlackLLM
    def __init__(self, config, gomoku_game):
        self.config = config
        self.gomoku_game = gomoku_game
        self.api_key = self.config.get('DeepSeek', 'api_key')  # 从 config.ini 读取 API Key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def create_prompt(self, board_state, ai_color): #  保留 ai_color 参数
        prompt = f"【五子棋指令】你现在是黑棋AI (玩家1)，目标是赢下这场五子棋对决！<(￣︶￣)> \n" #  改成 黑棋AI (玩家1)
        prompt += "棋盘大小是 15x15，坐标从 0 到 14，要记清楚哦！(눈\_눈)\n"
        prompt += "【重要规则】五子棋的目标是在横向、纵向或斜向的任意方向上，率先连成五个棋子！ (ง •̀\_•́)ง 记住是**任意方向**！ (╬￣皿￣)\n"
        prompt += "【重要说明】当前棋盘状态使用汉字表示：'空'代表空格，'黑'代表黑棋，'白'代表白棋，不要搞错了！(╯▔皿▔)╯\n"
        prompt += "坐标系统：横向是**列**（坐标的**第二个数字**），纵向是**行**（坐标的**第一个数字**）。 比如[2,0]表示第3行第1列，搞不清楚就等着输吧！(¬‿¬)\n"
        prompt += "棋盘顶部和左侧有坐标轴，看不懂自己对照！(翻白眼)\n"
        prompt += "当前棋盘状态：\n" + board_state + "\n"

        #  记录黑白棋子的位置 (使用旧代码逻辑! 直接从 self.gomoku_game.board 读取!)
        black_pieces = []
        white_pieces = []
        for x in range(self.gomoku_game.size):
            for y in range(self.gomoku_game.size):
                if self.gomoku_game.board[x][y] == 1:
                    black_pieces.append((x, y))
                elif self.gomoku_game.board[x][y] == 2:
                    white_pieces.append((x, y))

        prompt += "\n【黑棋位置】：(这些都是你下的棋子！要记住！) " + str(black_pieces) + "\n" #  改成 黑棋位置
        prompt += "\n【白棋位置】：(白棋就是你的对手哦！要小心！) " + str(white_pieces) + "\n" #  改成 白棋位置

        prompt += "【核心规则】只能在'空'的位置下棋！不遵守规则就判你输！(╬￣皿￣)\n"
        prompt += "\n给我认真思考一步最佳落子位置！不要瞎蒙！(눈\_눈) 否则有你好看！(╬￣皿￣)\n"
        prompt += "思考时，用()标出考虑的坐标。 示例：(3,5) 哼，本AI考虑这里怎么样... \n"
        prompt += "【最终指令】用[]标出最终确定的坐标！只能有一个！示例：[4,7] 就决定是你了！\n"
        prompt += "除了()和[]，可以写一些理由和吐槽，但坐标格式必须正确！不然...哼哼！(ಡωಡ)\n"
        print(prompt)
        return prompt

    def get_llm_response_stream(self, prompt): # 修改为 get_llm_response_stream, 返回生成器!
        reasoning_content = ""  # 定义完整思考过程
        answer_content = ""     # 定义完整回复
        is_answering = False   # 判断是否结束思考过程并开始回复
        completion = self.client.chat.completions.create(
            model="deepseek-r1",  # 此处以 deepseek-r1 为例，可按需更换模型名称
            messages=[
                {"role": "user", "content": prompt}
            ],
            stream=True,
        )
        for chunk in completion:
            # 打印思考过程
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content != None:
                yield chunk.choices[0].delta.reasoning_content #  逐段 yield reasoning_content
            # 打印回复过程
            else:
                yield chunk.choices[0].delta.content # 逐段 yield content


    def parse_response(self, response_text):
        coord_pattern = r"\[(\d+),\s*(\d+)\]"
        match = re.search(coord_pattern, response_text)
        if match:
            try:
                x = int(match.group(1))
                y = int(match.group(2))
                return (x, y)
            except ValueError:
                return None
        return None
