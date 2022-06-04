from showdown.battle import Battle

from ..helpers import format_decision
from ..helpers import pick_yamper_move

import os
import openai

class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        yamper_move, attemps = pick_yamper_move(battles)
        Battle.attemps.append(attemps)
        return format_decision(self, yamper_move)

    @staticmethod
    def call_model(request):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        return openai.Completion.create(engine="text-davinci-002", prompt=request, temperature=0, max_tokens=100, top_p=1, frequency_penalty=0, presence_penalty=0, stop=["\n"])