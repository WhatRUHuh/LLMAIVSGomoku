import os
from openai import OpenAI
from llm_interface import LLMInterface
import re

class DeepSeekLLM(LLMInterface):
    def __init__(self, config, gomoku_game):
        self.config = config
        self.gomoku_game = gomoku_game
        self.api_key = self.config.get('modelscope', 'api_key')  # 从 config.ini 读取 API Key
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api-inference.modelscope.cn/v1/"
        )

    def create_prompt(self, board_state, ai_color):
        prompt = f"【五子棋指令】你现在是白棋AI (玩家2)，目标是赢下这场对决！<(￣︶￣)>\n"
        prompt += "棋盘大小为15x15，坐标范围0到14，请牢记！(눈_눈)\n"
        prompt += "【规则】横、纵、斜均可连成五子获胜！(ง •̀_•́)ง\n"
        prompt += "【说明】棋盘状态中：'空'表示空位，'黑'表示黑棋，'白'表示白棋，请勿混淆！(╯▔皿▔)╯\n"
        prompt += "坐标说明：格式为[行,列]，例如[2,0]表示第3行第1列；棋盘顶部及左侧有坐标轴。\n"
        prompt += "当前棋盘状态：\n" + board_state + "\n"

        # 记录双方棋子的位置
        black_pieces = []
        white_pieces = []
        for x in range(self.gomoku_game.size):
            for y in range(self.gomoku_game.size):
                if self.gomoku_game.board[x][y] == 1:
                    black_pieces.append((x, y))
                elif self.gomoku_game.board[x][y] == 2:
                    white_pieces.append((x, y))
        prompt += "\n【黑棋位置】： " + str(black_pieces) + "\n"
        prompt += "\n【白棋位置】： " + str(white_pieces) + "\n"

        prompt += "【核心】只能在空位落子，否则判输！(╬￣皿￣)\n"
        prompt += "\n请快速思考一步最佳落子位置，迅速决定，最多思考30秒！(눈_눈)\n"
        prompt += "思考时请用()标示考虑的坐标（例如：(3,5)），最终请用[]标示最终选择（例如：[4,7]）。\n"
        prompt += "理由可附加，但坐标格式必须正确！(ಡωಡ)\n"
        print(prompt)
        return prompt

    def get_llm_response_stream(self, prompt):
        done_reasoning = False
        completion = self.client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",  # ModelScope Model-Id
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        for chunk in completion:
            reasoning_chunk = chunk.choices[0].delta.reasoning_content
            answer_chunk = chunk.choices[0].delta.content
            if reasoning_chunk:
                yield reasoning_chunk
            elif answer_chunk:
                if not done_reasoning:
                    yield "\n\n === Final Answer ===\n"
                    done_reasoning = True
                yield answer_chunk

    def parse_response(self, response_text):
        marker = "=== Final Answer ==="
        if marker in response_text:
            final_text = response_text.split(marker)[-1]
        else:
            final_text = response_text
         # 同时匹配 [数字, 数字] 和 [(数字, 数字)] 格式
        coord_pattern = r"\[\(?(\d{1,2}),\s*(\d{1,2})\)?\]"
        # coord_pattern = r"\[(\d{1,2}),\s*(\d{1,2})\]"
        matches = re.findall(coord_pattern, final_text)
        if matches:
            try:
                x_str, y_str = matches[-1]
                return (int(x_str), int(y_str))
            except ValueError:
                return None
        return None
