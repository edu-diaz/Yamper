import logging

import config
import constants
import banana_dev as banana
import os

from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import pick_safest
from showdown.engine.select_best_move import get_payoff_matrix

from difflib import SequenceMatcher


logger = logging.getLogger(__name__)


def format_decision(battle, decision):
    # Formats a decision for communication with Pokemon-Showdown
    # If the pokemon can mega-evolve, it will
    # If the move can be used as a Z-Move, it will be

    if decision.startswith(constants.SWITCH_STRING + " "):
        switch_pokemon = decision.split("switch ")[-1]
        for pkmn in battle.user.reserve:
            if pkmn.name == switch_pokemon:
                message = "/switch {}".format(pkmn.index)
                break
        else:
            raise ValueError("Tried to switch to: {}".format(switch_pokemon))
    else:
        message = "/choose move {}".format(decision)
        if battle.user.active.can_mega_evo:
            message = "{} {}".format(message, constants.MEGA)
        elif battle.user.active.can_ultra_burst:
            message = "{} {}".format(message, constants.ULTRA_BURST)

        # only dynamax on last pokemon
        if battle.user.active.can_dynamax and all(p.hp == 0 for p in battle.user.reserve):
            message = "{} {}".format(message, constants.DYNAMAX)

        if battle.user.active.get_move(decision).can_z:
            message = "{} {}".format(message, constants.ZMOVE)

    return [message, str(battle.rqid)]


def prefix_opponent_move(score_lookup, prefix):
    new_score_lookup = dict()
    for k, v in score_lookup.items():
        bot_move, opponent_move = k
        new_opponent_move = "{}_{}".format(opponent_move, prefix)
        new_score_lookup[(bot_move, new_opponent_move)] = v

    return new_score_lookup


def pick_safest_move_from_battles(battles):
    all_scores = dict()
    for i, b in enumerate(battles):
        state = b.create_state()
        mutator = StateMutator(state)
        user_options, opponent_options = b.get_all_options()
        logger.debug("Searching through the state: {}".format(mutator.state))
        scores = get_payoff_matrix(mutator, user_options, opponent_options, depth=config.search_depth, prune=True)

        prefixed_scores = prefix_opponent_move(scores, str(i))
        all_scores = {**all_scores, **prefixed_scores}

    decision, payoff = pick_safest(all_scores, remove_guaranteed=True)
    bot_choice = decision[0]
    logger.debug("Safest: {}, {}".format(bot_choice, payoff))
    return bot_choice


def pick_yamper_move(battles):
    bot_choice = None
    for _, b in enumerate(battles):
        state = b.create_state()
        mutator = StateMutator(state)
        user_options, _ = b.get_all_options()
        logger.debug("Searching through the state: {}".format(mutator.state))
        bot_choice = ask_yamper(user_options, b.opponent.active.base_name, b.turn)

    return bot_choice


def ask_yamper(user_options, opponent_pokemon, turn):
    logger.info(f"=========================== TURN {turn} ===========================")
    switch_options = [s for s in [a for a in user_options if "switch" in a]]
    attack_options = [a for a in user_options if "switch" not in a]
    bot_choice = None
    logger.debug("USER OPTIONS: " + ", ".join(user_options))

    if attack_options:
        request = "The opponent is " + opponent_pokemon + ". Which next move will you do: " + ", ".join(attack_options) + " or switch to another pokemon?"
        bot_choice = get_valid_response(request, attack_options, True)
        if bot_choice == "switch" and switch_options:
            request = "The opponent is " + opponent_pokemon + ". Which Pokemon will you choose: " + (", ".join(switch_options[:-1]) + " or " + switch_options[-1]).replace("switch ", "") + "?"
            bot_choice = get_valid_response(request, switch_options)
        else:
            request = "The opponent is " + opponent_pokemon + ". Which next move do you prefer: " + ", ".join(attack_options) + " or switch to another pokemon? Switching is the worst option."
            bot_choice = get_valid_response(request, attack_options, False)
    else:
        request = "The opponent is " + opponent_pokemon + ". Which Pokemon will you choose: " + (", ".join(switch_options[:-1]) + " or " + switch_options[-1]).replace("switch ", "") + "?"
        bot_choice = get_valid_response(request, switch_options)

    return bot_choice


def get_valid_response(request, options, attack_and_switch=False):
    logger.info("REQUEST: " + request)
    model_parameters = {"text": request, "length": 15, "temperature": 0.4, "topK": 50, "topP": 0.8}
    response = None
    bot_choice = None
    options = options + ["switch"] if attack_and_switch else options
    while (bot_choice is None):
        logger.debug("REQUEST: " + request)
        response = banana.run(os.environ['BANANA_API_KEY'], "gptj", model_parameters)["modelOutputs"][0]["output"].lower().strip()
        logger.debug("REQUEST: " + response)
        choice = [a for a in options if a.replace("switch ", "") in response]
        bot_choice = choice[0] if len(choice) == 1 else bot_choice
    logger.info("RESPONSE: " + response)
    logger.info("CHOICE: " + bot_choice)
    return bot_choice