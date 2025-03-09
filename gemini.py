# gemini.py
import google.generativeai as genai
import re

from llm_interface import LLMInterface

class GeminiLLM(LLMInterface):
    def __init__(self, config, gomoku_game):
        self.config = config
        self.gomoku_game = gomoku_game
        self.gemini_api_key = self.config.get('Gemini', 'api_key')
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash') #  提前加载模型

    def create_prompt(self, board_state, ai_color): #  新增 ai_color 参数，但这里 ai_color 参数其实用不上，因为是白棋版本
        prompt = f"【五子棋指令】你现在是白棋AI (玩家2)，目标是赢下这场五子棋对决！<(￣︶￣)> \n"
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

        prompt += "\n【黑棋位置】：(黑棋就是你的对手哦！要小心！) " + str(black_pieces) + "\n"
        prompt += "\n【白棋位置】：(这些都是你下的棋子！要记住！) " + str(white_pieces) + "\n"

        prompt += "【核心规则】只能在'空'的位置下棋！不遵守规则就判你输！(╬￣皿￣)\n"
        prompt += "\n给我认真思考一步最佳落子位置！不要瞎蒙！(눈\_눈) 否则有你好看！(╬￣皿￣)\n"
        prompt += "思考时，用()标出考虑的坐标。 示例：(3,5) 哼，本AI考虑这里怎么样... \n"
        prompt += "【最终指令】用[]标出最终确定的坐标！只能有一个！示例：[4,7] 就决定是你了！\n"
        prompt += "除了()和[]，可以写一些理由和吐槽，但坐标格式必须正确！不然...哼哼！(ಡωಡ)\n"
        print(prompt)
        return prompt

    def get_llm_response_stream(self, prompt): # 修改为 get_llm_response_stream, 返回生成器!
        response_stream = self.model.generate_content(prompt, stream=True) #  获取流式 response
        for chunk in response_stream: # 迭代 stream, 逐段返回 text
             yield chunk.text

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
