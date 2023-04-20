import argparse
import codecs
import datetime
import os
import random
import re
import subprocess
import sys
import time
import pandas as pd

import yaml

from optuna.trial import Trial
import optuna

from config_parser import *
from config_parser import _OptPick


# cnfg = OptunaConfig.parse_from_config_file(fp)

# print(parsed)
# exit()


def _regex_line_for_first_group(regex: re.Pattern, line: str):
    match = regex.search(line)
    if match is not None:
        value = match.group(1)
        return value
    return None


class TeaPot:
    def __init__(self, fp: str):
        dir_content = os.listdir("./")
        default_path = "./tea_pot_config.yaml"

        self.checkpoint_dir = "./tea_pot_checkpoints"
        self.checkpoint_file_name = f"tea_pot_study_{datetime.datetime.now()}.csv"

        if not os.path.isdir(self.checkpoint_dir):
            os.mkdir(self.checkpoint_dir)


        if os.path.exists(default_path):
            self.config: OptunaConfig = OptunaConfig.parse_from_config_file(default_path)
        else:
            self.config: OptunaConfig = OptunaConfig.parse_from_command_line()

        self.result_score_regex = re.compile(self.config.engine_params.result_regex)

        if self.config.engine_params.prune_config is not None:
            self.prune = True
            self.has_score_regex = self.config.engine_params.prune_config.score_regex is not None
            if self.has_score_regex:
                self.score_regex = re.compile(self.config.engine_params.prune_config.score_regex)

            self.has_iter_regex = self.config.engine_params.prune_config.iter_regex is not None
            if self.has_iter_regex:
                self.iter_regex = re.compile(self.config.engine_params.prune_config.iter_regex)
        else:
            self.prune = False

    def gen_run_str(self, trial: Trial):
        arg_list = []
        base = self.config.engine_params.base_command
        for opt in self.config.search_space_config:
            base = f"{base} {opt.build_cmd_arg(trial)}"
            # arg_list.append(opt.build_cmd_arg(trial))

        return base
        # return ['/bin/sh', '-c',self.config.engine_params.base_command, *arg_list]



    def objective_function(self,trial: Trial):
        comand_parts = self.gen_run_str(trial)
        process = subprocess.Popen(comand_parts, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        start_time = time.time()

        final_score = None
        for raw_line in process.stdout:
            # print(raw_line)

            line = codecs.decode(raw_line, 'unicode_escape')
            code = process.poll()
            if self.config.engine_params.print_level == 2:
                print(line, end="")

            # check if result is found
            val = _regex_line_for_first_group(self.result_score_regex, line)
            # print(f"regex pat {self.result_score_regex} ret: {val}")
            final_score = float(val) if val is not None else final_score
            # print(f"final_s: {final_score}")

            # check if run is over
            # print(codecs.decode(line, 'unicode_escape'), end="")
            # print("term code ", code)

            if code is not None:
                if code == 0:
                    break
                    pass
                else:
                    print("non zero exit code")
                    print(line)
                    exit()
                    break
                    pass
                # run has terminated
                pass



            if self.prune:
                tmp_score = _regex_line_for_first_group(self.score_regex, line)
                if tmp_score is not None:
                    if self.config.engine_params.print_level == 1:
                        print(line, end="")
                    tmp_score = float(tmp_score)
                    final_score = tmp_score
                    if self.config.engine_params.prune_config.use_time:
                        time_delta = int(time.time() -start_time)
                        trial.report(tmp_score, time_delta)
                    else:
                        iter = _regex_line_for_first_group(self.iter_regex, line)
                        if iter is not None:
                            iter = int(iter)
                            trial.report(tmp_score, iter)

                if trial.should_prune():
                    process.kill()
                    break

        return final_score
        # return random.random()


    def trial_callback(self,study: optuna.study.Study, frozen_trial: optuna.trial.FrozenTrial):
        df: pd.DataFrame = study.trials_dataframe()
        df.to_csv(f"{self.checkpoint_dir}/{self.checkpoint_file_name}")



    def run_study(self):
        study = optuna.create_study(direction=self.config.engine_params.direction,
                                    study_name=self.config.name)
        study.optimize(func=self.objective_function,
                       n_trials=self.config.engine_params.n_trials,
                       timeout=self.config.engine_params.timeout,
                       callbacks=[self.trial_callback])

    # print(process.stdout.decode("utf-8"))



def main():
    # with open(r'./config_example.yaml', "r") as file:
    #     parsed = yaml.load(file, Loader=yaml.FullLoader)
    #     # sort_file = yaml.dump(abc, sort_keys=True)

    # fp = './config_example.yaml'

    tp = TeaPot(None)
    tp.run_study()



if __name__ == '__main__':
    main()



#./.py_env/bin/python3 ./test_tr.py   --alpha 0.8167021281665366   --bn 0.012461435663013387   --fp False