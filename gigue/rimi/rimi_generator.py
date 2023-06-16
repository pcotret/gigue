from typing import List

from gigue.constants import (
    BIN_DIR,
    CALLER_SAVED_REG,
    CMP_REG,
    DATA_REG,
    DATA_SIZE,
    HIT_CASE_REG,
    INSTRUCTION_WEIGHTS,
)
from gigue.generator import TrampolineGenerator
from gigue.rimi.rimi_builder import (
    RIMIFullInstructionBuilder,
    RIMIShadowStackInstructionBuilder,
)
from gigue.rimi.rimi_constants import RIMI_SSP_REG, SHADOW_STACK_SIZE


class RIMIShadowStackTrampolineGenerator(TrampolineGenerator):
    def __init__(
        self,
        interpreter_start_address: int,
        jit_start_address: int,
        jit_size: int,
        jit_nb_methods: int,
        method_variation_mean: float,
        method_variation_stdev: float,
        call_depth_mean: int,
        call_occupation_mean: float,
        call_occupation_stdev: float,
        pics_ratio: float,
        pics_mean_case_nb: int,
        data_size: int = DATA_SIZE,
        data_generation_strategy: str = "random",
        shadow_stack_size: int = SHADOW_STACK_SIZE,
        pics_cmp_reg: int = CMP_REG,
        pics_hit_case_reg: int = HIT_CASE_REG,
        registers: List[int] = CALLER_SAVED_REG,
        data_reg: int = DATA_REG,
        rimi_ssp_reg: int = RIMI_SSP_REG,
        weights: List[int] = INSTRUCTION_WEIGHTS,
        output_bin_file: str = BIN_DIR + "out.bin",
        output_data_bin_file: str = BIN_DIR + "data.bin",
        output_ss_bin_file: str = BIN_DIR + "ss.bin",
    ):
        super().__init__(
            interpreter_start_address=interpreter_start_address,
            jit_start_address=jit_start_address,
            jit_size=jit_size,
            jit_nb_methods=jit_nb_methods,
            method_variation_mean=method_variation_mean,
            method_variation_stdev=method_variation_stdev,
            call_depth_mean=call_depth_mean,
            call_occupation_mean=call_occupation_mean,
            call_occupation_stdev=call_occupation_stdev,
            pics_ratio=pics_ratio,
            pics_mean_case_nb=pics_mean_case_nb,
            data_size=data_size,
            data_generation_strategy=data_generation_strategy,
            pics_cmp_reg=pics_cmp_reg,
            pics_hit_case_reg=pics_hit_case_reg,
            registers=registers,
            data_reg=data_reg,
            weights=weights,
            output_bin_file=output_bin_file,
            output_data_bin_file=output_data_bin_file,
            output_ss_bin_file=output_ss_bin_file
        )
        self.builder: RIMIShadowStackInstructionBuilder = (
            RIMIShadowStackInstructionBuilder()
        )
        self.rimi_ssp_reg: int = rimi_ssp_reg
        self.registers: List[int] = [
            reg for reg in self.registers if reg != self.rimi_ssp_reg
        ]

        self.shadow_stack_size = shadow_stack_size

    def generate_shadowstack_binary(self) -> bytes:
        self.ss_bin = self.miner.generate_data(
            "zeroes", self.shadow_stack_size
        )
        return self.ss_bin


class RIMIFullTrampolineGenerator(RIMIShadowStackTrampolineGenerator):
    def __init__(
        self,
        interpreter_start_address: int,
        jit_start_address: int,
        jit_size: int,
        jit_nb_methods: int,
        method_variation_mean: float,
        method_variation_stdev: float,
        call_depth_mean: int,
        call_occupation_mean: float,
        call_occupation_stdev: float,
        pics_ratio: float,
        pics_mean_case_nb: int,
        data_size: int = DATA_SIZE,
        data_generation_strategy: str = "random",
        shadow_stack_size: int = SHADOW_STACK_SIZE,
        pics_cmp_reg: int = CMP_REG,
        pics_hit_case_reg: int = HIT_CASE_REG,
        registers: List[int] = CALLER_SAVED_REG,
        data_reg: int = DATA_REG,
        rimi_ssp_reg: int = RIMI_SSP_REG,
        weights: List[int] = INSTRUCTION_WEIGHTS,
        output_bin_file: str = BIN_DIR + "out.bin",
        output_data_bin_file: str = BIN_DIR + "data.bin",
        output_ss_bin_file: str = BIN_DIR + "ss.bin",
    ):
        super().__init__(
            interpreter_start_address=interpreter_start_address,
            jit_start_address=jit_start_address,
            jit_size=jit_size,
            jit_nb_methods=jit_nb_methods,
            method_variation_mean=method_variation_mean,
            method_variation_stdev=method_variation_stdev,
            call_depth_mean=call_depth_mean,
            call_occupation_mean=call_occupation_mean,
            call_occupation_stdev=call_occupation_stdev,
            pics_ratio=pics_ratio,
            pics_mean_case_nb=pics_mean_case_nb,
            data_size=data_size,
            data_generation_strategy=data_generation_strategy,
            shadow_stack_size=shadow_stack_size,
            pics_cmp_reg=pics_cmp_reg,
            pics_hit_case_reg=pics_hit_case_reg,
            registers=registers,
            data_reg=data_reg,
            rimi_ssp_reg=rimi_ssp_reg,
            weights=weights,
            output_bin_file=output_bin_file,
            output_data_bin_file=output_data_bin_file,
            output_ss_bin_file=output_ss_bin_file
        )
        self.builder: RIMIFullInstructionBuilder = RIMIFullInstructionBuilder()
