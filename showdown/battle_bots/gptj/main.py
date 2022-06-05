from showdown.battle import Battle

from ..helpers import format_decision
from ..helpers import pick_yamper_move

import banana_dev as banana
import os


class BattleBot(Battle):
    def __init__(self, *args, **kwargs):
        super(BattleBot, self).__init__(*args, **kwargs)

    def find_best_move(self):
        battles = self.prepare_battles(join_moves_together=True)
        yamper_move, shots = pick_yamper_move(battles)
        Battle.shots.append(shots)
        return format_decision(self, yamper_move)

    @staticmethod
    def call_model(request):
        model_parameters = {"text": request, "length": 80, "temperature": 0.8, "topK": 50, "topP": 0.8}
        return banana.run(os.environ['BANANA_API_KEY'], "gptj", model_parameters)["modelOutputs"][0]["output"].lower().strip()
