import logging
import re

import config
import constants
import importlib

from showdown.engine.objects import StateMutator
from showdown.engine.select_best_move import pick_safest
from showdown.engine.select_best_move import get_payoff_matrix


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
        logger.debug("Searching through the state: {}".format(mutator.state))
        bot_choice, shots = ask_yamper(b)
    return bot_choice, shots


def ask_yamper(battle):
    logger.info(f"========================================= TURN {battle.turn} =========================================")

    user_options, _ = battle.get_all_options()
    switch_options = [s.replace("switch ", "") for s in [a for a in user_options if "switch " in a]]
    attack_options = [a for a in user_options if "switch " not in a]
    safest_option = pick_safest_move_from_battles([battle])

    prompt_list = lambda start, options: (start + ", ".join(options) + ". ")[::-1].replace(',', ' or'[::-1], 1)[::-1] if options else ""
    status_prompt = "You are in a Pokémon battle where you have " + str(len(battle.user.reserve)) + " Pokémons. "
    attack_prompt = prompt_list("Your available attacks are ", attack_options)
    switch_prompt = prompt_list("You can switch to ", switch_options)
    bias_prompt = "The best option is " + safest_option + ". What will you do?"

    try:
        nlp_health = lambda rate : "high" if rate >= 0.8 else "mid" if rate >= 0.4 else "low"
        opponent_health = nlp_health(battle.opponent.active.hp/battle.opponent.active.max_hp)
        active_health = nlp_health(battle.user.active.hp/battle.user.active.max_hp)
        status_prompt += "The opponent is a " + battle.opponent.active.base_name + " with " + opponent_health + " health, meanwhile your Pokémon is a " + battle.user.active.base_name + " with " + active_health + " health. "
    except ZeroDivisionError:
        pass

    bot_choice, shots = get_valid_response(status_prompt + attack_prompt + switch_prompt + bias_prompt, attack_options, switch_options, safest_option.replace("switch ", ""))
    bot_choice = "switch " + bot_choice if any(bot_choice  in s for s in switch_options) else bot_choice
    return bot_choice, shots


def get_valid_response(prompt, attack_options, switch_options, safest_option):
    battle_module = importlib.import_module('showdown.battle_bots.{}.main'.format(config.battle_bot_module))
    logger.info("PROMPT: " + prompt)
    response = None
    bot_choice = None
    shots = 0
    while (bot_choice is None):
        response = battle_module.BattleBot.call_model(prompt)
        logger.debug("RESPONSE: " + response)
        parser = lambda options : [a for a in options if a in response.lower()]
        attack_choice = parser(attack_options)
        switch_choice = parser(switch_options)
        if safest_option in response:
            bot_choice = safest_option
        elif attack_choice:
            bot_choice = attack_choice[0]
        elif switch_choice:
            bot_choice = switch_choice[0]
        # Sometimes the response is the question repeated. We avoid it with this.
        if prompt[:len(prompt)//2].lower() in response.lower():
            bot_choice = None
        shots += 1
    logger.info("RESPONSE: " + response)
    logger.info("CHOICE: " + bot_choice)
    return bot_choice, shots