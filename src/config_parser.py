import argparse
import re
import sys
from abc import abstractmethod
from typing import Optional

import yaml
from optuna.trial import Trial

#############################
#       validators
#############################

def _is_valid_regex(str_pattern: str):
    try:
        pattern = re.compile(str_pattern)
        is_valid = pattern.groups == 1
    except re.error:
        is_valid = False
    return is_valid

def _is_valid():
    pass

def _has_required_keys(parse_dict: dict, key_list: [str]):
    keys = parse_dict.keys()
    for required_key in key_list:
        if required_key not in keys:
            print(f"The required key {required_key} is not in the parsed obj {list(parse_dict.keys())}")
            raise TeaPotConfigError()
            pass
            #todo: error

def _key_is_valid(key, valid_keys):
    if key not in valid_keys:
        print(f"The key {key} is not in the list of valid keys: {valid_keys}")
        raise TeaPotConfigError()

        pass
#############################
#       config objects
#############################


class TeaPotConfigError(Exception):
    pass


class _PruneConfig:
    def __init__(self):
        self.score_regex: Optional[str] = r'score: (\S*)'
        self.iter_regex: Optional[str] = r'iter: (\S*)'
        self.use_time: bool = False

        self._valid_keys = ["score_regex", "iter_regex", "use_time"]

    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = _PruneConfig()
        conf._parse_from_config_dict(parse_dict)
        return conf

    def _parse_from_config_dict(self, parse_dict: dict):
        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)
            if key == "score_regex":
                if _is_valid_regex(value):
                    self.score_regex = value
                else:
                    raise TeaPotConfigError()
            elif key == "iter_regex":
                if _is_valid_regex(value):
                    self.iter_regex = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "use_time":
                if type(value) == bool:
                    if "iter_regex" in parse_dict.keys():
                        # todo warn user
                        pass
                    self.use_time = value
                else:
                    raise TeaPotConfigError()
                    pass

class _EngineConfig:
    def __init__(self):
        self.base_command: Optional[str] = None
        self.print_level: int = 0

        self.n_trials: Optional[int] = None
        self.timeout: int = 100

        self.direction: str = "minimize"
        self._direction_valid_values = ["maximize", "minimize"]

        self.result_regex: str = r"score: (\S*)"

        self.prune_config: Optional[_PruneConfig] = None#_PruneConfig()

        self._valid_keys = ["base_command", "n_trials","timeout", "direction", "result_regex", "pruning", "print_level"]
        self._required_keys = ["base_command", "direction", "result_regex", ]
        pass

    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = _EngineConfig()
        conf._parse_from_config_dict(parse_dict)
        return conf

    def _parse_from_config_dict(self, parse_dict: dict):
        # check for required values
        _has_required_keys(parse_dict,self._required_keys)

        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)

            if key == "base_command":
                if type(value) == str:
                    self.base_command = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "print_level":
                if type(value) == int:
                    self.print_level = value
                else:
                    raise TeaPotConfigError()
            elif key == "n_trials":
                if type(value) == int:
                    self.n_trials = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "timeout":
                if type(value) == int:
                    self.timeout = value
                else:
                    raise TeaPotConfigError()
                    pass

            elif key == "direction":
                if type(value) == str and value in self._direction_valid_values:
                    self.direction = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "result_regex":
                if _is_valid_regex(value):
                    self.result_regex = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "pruning":
                if type(value) == dict:
                    self.prune_config = _PruneConfig.parse_from_config_dict(value)
                else:
                    raise TeaPotConfigError()
                    pass

class _OptPick:
    def __init__(self):

        self._valid_keys: [str]
        self._required_keys: [str]

    @abstractmethod
    def build_cmd_arg(self, trial: Trial) -> str:
        pass


    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = OptunaConfig()
        conf._parse_from_config_dict(parse_dict)
        return conf


class _PickInt(_OptPick):
    def __init__(self):
        super().__init__()
        self.name: Optional[str] = None
        self.call_param: str = ""
        self.from_val: int = 0
        self.to_val: int = 0
        self.step: Optional[int] = None
        self.use_log: bool = False

        self._valid_keys = ["name", "call_param", "from", "to", "step", "log"]
        self._required_keys = [ "call_param","from", "to"]

    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = _PickInt()
        conf._parse_from_config_dict(parse_dict)
        return conf

    def build_cmd_arg(self,
                      trial: Trial) -> str:
        val = trial.suggest_int(name=self.name,
                                low=self.from_val,
                                high=self.to_val,
                                step=self.step,
                                log=self.use_log
                                )

        cmd_arg = f" {self.call_param}{val} "
        return cmd_arg

    def _parse_from_config_dict(self, parse_dict: dict):
        # check for required values
        _has_required_keys(parse_dict,self._required_keys)

        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)
            if key == "name":
                if type(value) == str:
                    self.name = value
                else:
                    raise TeaPotConfigError()
            elif key == "call_param":
                if type(value) == str:
                    self.call_param = value
                else:
                    raise TeaPotConfigError()
            elif key == "from":
                if type(value) == int:
                    self.from_val = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "to":
                if type(value) == int:
                    self.to_val = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "step":
                if type(value) == int:
                    self.step = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "log":
                if type(value) == bool:
                    self.use_log = value
                else:
                    raise TeaPotConfigError()
                    pass

class _PickFloat(_OptPick):
    def __init__(self):
        super().__init__()
        self.name: Optional[str] = None
        self.call_param: str = ""
        self.from_val: float = 0
        self.to_val: float = 0
        self.step: Optional[float] = None
        self.use_log: bool = False


        self._valid_keys = ["name", "call_param", "from", "to", "step", "log"]
        self._required_keys = [ "call_param","from", "to"]

    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = _PickFloat()
        conf._parse_from_config_dict(parse_dict)
        return conf

    def build_cmd_arg(self,
                      trial: Trial) -> str:
        val = trial.suggest_float(name=self.name,
                                low=self.from_val,
                                high=self.to_val,
                                step=self.step,
                                log=self.use_log
                                )

        cmd_arg = f" {self.call_param}{val} "
        return cmd_arg

    def _parse_from_config_dict(self, parse_dict: dict):
        # check for required values
        _has_required_keys(parse_dict,self._required_keys)

        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)
            if key == "name":
                if type(value) == str:
                    self.name = value
                else:
                    raise TeaPotConfigError()
            elif key == "call_param":
                if type(value) == str:
                    self.call_param = value
                else:
                    raise TeaPotConfigError()
            elif key == "from":
                if type(value) == float or type(value) == int:
                    self.from_val = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "to":
                if type(value) == float or type(value) == int:
                    self.to_val = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "step":
                if type(value) == float or type(value) == int:
                    self.step = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "log":
                if type(value) == bool:
                    self.use_log = value
                else:
                    raise TeaPotConfigError()
                    pass


class _PickCategorical(_OptPick):
    def __init__(self):
        super().__init__()
        self.name: Optional[str] = None
        self.call_param: str = ""
        self.pick_options: [str] = []

        self._valid_keys = ["name", "call_param", "picks"]
        self._required_keys = ["call_param", "picks"]

    @staticmethod
    def parse_from_config_dict(parse_dict):
        conf = _PickCategorical()
        conf._parse_from_config_dict(parse_dict)
        return conf


    def build_cmd_arg(self,
                      trial: Trial) -> str:
        val = trial.suggest_categorical(name=self.name,
                                        choices=self.pick_options
                                        )

        cmd_arg = f" {self.call_param}{val} "
        return cmd_arg


    def _parse_from_config_dict(self,
                               parse_dict: dict):
        # check for required values
        _has_required_keys(parse_dict,self._required_keys)

        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)
            if key == "name":
                if type(value) == str:
                    self.name = value
                else:
                    raise TeaPotConfigError()
            elif key == "call_param":
                if type(value) == str:
                    self.call_param = value
                else:
                    raise TeaPotConfigError()
            elif key == "picks":
                if type(value) == list:
                    self.pick_options.clear()
                    for pick in value:
                        if type(pick) == str:
                            self.pick_options.append(pick)
                        else:
                            raise TeaPotConfigError()
                            pass
                else:
                    raise TeaPotConfigError()
                    pass


class OptunaConfig:
    def __init__(self):
        self.name: Optional[str] = None
        self.engine_params: _EngineConfig = _EngineConfig()
        self.search_space_config: [_OptPick]= []
        self._search_space_config_valid_values = ["pick_int", "pick_float", "pick_categorical"]

        self._valid_keys = ["study_name", "engine_params", "search_space"]
        self._required_keys = ["engine_params", "search_space"]


    @staticmethod
    def parse_from_config_file(file_path: str):

        try:
            with open(file_path, "r") as file:
                parsed = yaml.load(file, Loader=yaml.FullLoader)
                # sort_file = yaml.dump(abc, sort_keys=True)
                # print(parsed)
        except Exception as e:
            print(e)

        conf = OptunaConfig()
        conf._parse_from_config_dict(parsed)
        return conf

    @staticmethod
    def parse_from_command_line(conf=None):
        if conf is None:
            conf = OptunaConfig()
        conf._parse_from_command_line_args()
        return conf

    def _parse_from_command_line_args(self):
        # fetch the args
        args = sys.argv
        parser_args = args

        if "--cmd" in args:
            cm_idx = args.index("--cmd")
            parser_args = args[1:cm_idx]
            used_cmd = args[cm_idx+1:]

            cur_idx = 1
            drop = []

            # parse the command part

            while True:
                part = used_cmd[cur_idx]
                try:
                    if "i[" in part:
                        int_pick = _PickInt()
                        int_pick.call_param = f" {used_cmd[cur_idx - 1]} "
                        int_pick.name = used_cmd[cur_idx-1].lstrip("--")
                        lower, higher = part.lstrip("i[").rstrip("]").split(",")
                        int_pick.from_val = lower
                        int_pick.to_val = higher
                        self.search_space_config.append(int_pick)
                        drop.append(cur_idx - 1)
                        drop.append(cur_idx)
                    elif "f[" in part:
                        float_pick = _PickFloat()
                        float_pick.call_param = f" {used_cmd[cur_idx - 1]} "
                        float_pick.name = used_cmd[cur_idx-1].lstrip("--")
                        lower, higher = part.lstrip("f[").rstrip("]").split(",")
                        float_pick.from_val = lower
                        float_pick.to_val = higher
                        self.search_space_config.append(float_pick)
                        drop.append(cur_idx - 1)
                        drop.append(cur_idx)
                    elif "c[" in part:
                        cat_pick = _PickCategorical()
                        cat_pick.call_param = f" {used_cmd[cur_idx - 1]} "
                        cat_pick.name = used_cmd[cur_idx-1].lstrip("--")
                        parts = part.lstrip("c[").rstrip("]").split(",")
                        cat_pick.pick_options = parts
                        self.search_space_config.append(cat_pick)
                        drop.append(cur_idx - 1)
                        drop.append(cur_idx)

                except Exception as e:
                    print(e)
                    raise TeaPotConfigError()

                cur_idx += 1
                if cur_idx >= len(used_cmd):
                    break
            for d in reversed(drop):
                used_cmd.pop(d)

            command_str = ""
            for s in used_cmd:
                command_str += " " + s

            self.engine_params.base_command = command_str

        # parse the argument part

        parser = argparse.ArgumentParser()

        parser.add_argument("--dir", type=str, default="./")
        parser.add_argument("--direction", type=str, default="minimize",choices=["maximize", "minimize"])


        pa = parser.parse_args(parser_args)

        self.engine_params.direction = pa.direction

        # print(f"\n{pa.target_re}\n")
        # print(f"\n{pa.test}\n")

    def _parse_from_config_dict(self,
                           parse_dict: dict):
        # check for required values
        _has_required_keys(parse_dict, self._required_keys)

        for key, value in parse_dict.items():
            _key_is_valid(key, self._valid_keys)
            if key == "study_name":
                if type(value) == str:
                    self.name = value
                else:
                    raise TeaPotConfigError()
                    pass
            elif key == "engine_params":
                if type(value) == dict:
                    self.engine_params = _EngineConfig.parse_from_config_dict(value)
                else:
                    raise TeaPotConfigError()
                    pass

            elif key == "search_space":
                if type(value) == list:
                    self.search_space_config.clear()
                    for pick in value:
                        if type(pick) == dict:
                            key_list = pick.keys()
                            if len(key_list) != 1:
                                raise TeaPotConfigError()
                            for k,v in pick.items():
                                # this is stupid because python is stupid.
                                if k not in self._search_space_config_valid_values or type(v) != dict:
                                    raise TeaPotConfigError()
                                elif k == "pick_int":
                                    self.search_space_config.append(_PickInt.parse_from_config_dict(v))
                                elif k == "pick_float":
                                    self.search_space_config.append(_PickFloat.parse_from_config_dict(v))
                                elif k == "pick_categorical":
                                    self.search_space_config.append(_PickCategorical.parse_from_config_dict(v))
                        else:
                            raise TeaPotConfigError()
                            pass
                else:
                    raise TeaPotConfigError()
                    pass


#
#       Param validation
#




