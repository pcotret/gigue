import random

from gigue.constants import (
    CALL_TMP_REG,
    CALLEE_SAVED_REG,
    CMP_REG,
    HIT_CASE_REG,
    INSTRUCTION_WEIGHTS,
    RA,
    SP,
)
from gigue.exceptions import WrongOffsetException
from gigue.helpers import align
from gigue.instructions import (
    BInstruction,
    IInstruction,
    JInstruction,
    RInstruction,
    SInstruction,
    UInstruction,
)


class InstructionBuilder:
    R_INSTRUCTIONS = [
        "add",
        "addw",
        "andr",
        "mul",
        "mulh",
        "mulhsu",
        "mulhu",
        "mulw",
        "orr",
        "sll",
        "sllw",
        "slt",
        "sltu",
        "sra",
        "sraw",
        "srl",
        "srlw",
        "sub",
        "subw",
        "xor",
    ]
    I_INSTRUCTIONS = ["addi", "addiw", "andi", "ori", "slti", "sltiu", "xori"]
    I_INSTRUCTIONS_LOAD = ["lb", "lbu", "ld", "lh", "lhu"]
    U_INSTRUCTIONS = ["auipc", "lui"]
    S_INSTRUCTIONS = ["sb", "sd", "sh", "sw"]
    B_INSTRUCTIONS = ["beq", "bge", "bgeu", "blt", "bltu", "bne"]

    ALIGNMENT = {
        "b": 1,
        "h": 2,
        "w": 4,
        "d": 8,
    }

    # Helpers
    # \______

    @staticmethod
    def consolidate_bytes(instructions):
        return b"".join([instr.generate_bytes() for instr in instructions])

    @staticmethod
    def split_offset(offset):
        if abs(offset) < 8:
            raise WrongOffsetException(
                f"Call offset should be greater than 8 (currently {offset})."
            )
        offset_low = offset & 0xFFF
        # The right part handles the low offset sign
        # extension (that should be mitigated)
        offset_high = (offset & 0xFFFFF000) + ((offset & 0x800) << 1)
        # print("offset: {}/{} -> olow: {} + ohigh: {}".format(
        #     hex(offset),
        #     hex(offset & 0xFFFFFFFF),
        #     hex(offset_low),
        #     hex(offset_high)
        # ))
        return offset_low, offset_high

    @classmethod
    def define_memory_access_alignment(cls, name):
        for key in InstructionBuilder.ALIGNMENT.keys():
            if key in name:
                return InstructionBuilder.ALIGNMENT[key]

    # Specific instruction building
    # \___________________________

    @staticmethod
    def build_nop():
        return IInstruction.nop()

    @staticmethod
    def build_ret():
        return IInstruction.ret()

    # Random instruction building
    # \__________________________

    @staticmethod
    def build_random_r_instruction(registers, *args, **kwargs):
        name = random.choice(InstructionBuilder.R_INSTRUCTIONS)
        constr = getattr(RInstruction, name)
        rd, rs1, rs2 = tuple(random.choices(registers, k=3))
        return constr(rd=rd, rs1=rs1, rs2=rs2)

    @staticmethod
    def build_random_i_instruction(registers, *args, **kwargs):
        name = random.choice(InstructionBuilder.I_INSTRUCTIONS)
        constr = getattr(IInstruction, name)
        rd, rs1 = tuple(random.choices(registers, k=2))
        imm = random.randint(0, 0xFFF)
        return constr(rd=rd, rs1=rs1, imm=imm)

    @staticmethod
    def build_random_u_instruction(registers, *args, **kwargs):
        name = random.choice(InstructionBuilder.U_INSTRUCTIONS)
        constr = getattr(UInstruction, name)
        rd = random.choice(registers)
        imm = random.randint(0, 0xFFFFFFFF)
        return constr(rd=rd, imm=imm)

    @staticmethod
    def build_random_s_instruction(registers, data_reg, data_size, *args, **kwargs):
        name = random.choice(InstructionBuilder.S_INSTRUCTIONS)
        constr = getattr(SInstruction, name)
        # Note: sd, rs2, off(rs1) stores the contents of rs2
        # at the address in rs1 + offset
        rs1 = data_reg
        rs2 = random.choice(registers)
        alignment = InstructionBuilder.define_memory_access_alignment(name)
        imm = align(random.randint(0, min(data_size, 0x7FF)), alignment)
        return constr(rs1=rs1, rs2=rs2, imm=imm)

    @staticmethod
    def build_random_l_instruction(registers, data_reg, data_size, *args, **kwargs):
        name = random.choice(InstructionBuilder.I_INSTRUCTIONS_LOAD)
        constr = getattr(IInstruction, name)
        # Note: ld, rd, off(rs1) loads the value at the address
        # stored in rs1 + off in rd
        rd = random.choice(registers)
        rs1 = data_reg
        alignment = InstructionBuilder.define_memory_access_alignment(name)
        imm = align(random.randint(0, min(data_size, 0x7FF)), alignment)
        return constr(rd=rd, rs1=rs1, imm=imm)

    # TODO: There should be a better way?
    @classmethod
    def size_offset(cls, max_offset):
        possible_offsets = set([4, max_offset])
        for i in range(1, max_offset // 12 + 1):
            possible_offsets.add(i * 12 + max_offset % 12)
        if max_offset % 12 == 8:
            possible_offsets.add(8)
        return list(possible_offsets)

    @staticmethod
    def build_random_j_instruction(registers, max_offset, *args, **kwargs):
        # Jump to stay in the method and keep aligment
        rd = random.choice(registers)
        offset = random.choice(InstructionBuilder.size_offset(max_offset))
        return JInstruction.jal(rd, offset)

    @staticmethod
    def build_random_b_instruction(registers, max_offset, *args, **kwargs):
        name = random.choice(InstructionBuilder.B_INSTRUCTIONS)
        constr = getattr(BInstruction, name)
        rs1, rs2 = random.choices(registers, k=2)
        # offset = max(random.randrange(0, max(12, max_offset), 12), 12)
        offset = random.choice(InstructionBuilder.size_offset(max_offset))
        return constr(rs1=rs1, rs2=rs2, imm=offset)

    @staticmethod
    def build_random_instruction(
        registers, max_offset, data_reg, data_size, weights=INSTRUCTION_WEIGHTS
    ):
        method_name = random.choices(
            [
                "build_random_r_instruction",
                "build_random_i_instruction",
                "build_random_u_instruction",
                "build_random_j_instruction",
                "build_random_b_instruction",
                "build_random_s_instruction",
                "build_random_l_instruction",
            ],
            weights,
        )[0]
        method = getattr(InstructionBuilder, method_name)
        instruction = method(
            registers=registers,
            max_offset=max_offset,
            data_reg=data_reg,
            data_size=data_size,
        )
        return instruction

    # Element calls
    # \____________

    # Visitor to build either a PIC or method
    @staticmethod
    def build_element_call(elt, offset):
        return elt.accept_build_call(offset)

    @staticmethod
    def build_method_base_call(offset):
        # Base method, no trampolines
        offset_low, offset_high = InstructionBuilder.split_offset(offset)
        return [UInstruction.auipc(1, offset_high), IInstruction.jalr(1, 1, offset_low)]

    @staticmethod
    def build_method_call(offset):
        # This method uses the trampoline to call/return from JIT elements
        offset_low, offset_high = InstructionBuilder.split_offset(offset)
        return [UInstruction.auipc(1, offset_high), IInstruction.jalr(1, 1, offset_low)]

    @staticmethod
    def build_pic_call(offset, hit_case, hit_case_reg=HIT_CASE_REG):
        offset_low, offset_high = InstructionBuilder.split_offset(offset)
        # 1. Needed case hit
        # 2/3. Jump to the PC-related PIC location
        return [
            IInstruction.addi(rd=hit_case_reg, rs1=0, imm=hit_case),
            UInstruction.auipc(rd=1, imm=offset_high),
            IInstruction.jalr(rd=1, rs1=1, imm=offset_low),
        ]

    # Specific structures
    # \__________________

    @staticmethod
    def build_switch_case(
        case_number, method_offset, hit_case_reg=HIT_CASE_REG, cmp_reg=CMP_REG
    ):
        # Switch for one case:
        #   1 - Loading the value to compare in the compare register
        #   2 - Compare to the current case (should be in the hit case register)
        #   3 - Jump to the corresponding method if equal
        #   4 - Go to the next case if not
        # Note: beq is not used to cover a wider range (2Mb rather than 8kb)
        return [
            IInstruction.addi(rd=cmp_reg, rs1=0, imm=case_number),
            BInstruction.bne(rs1=cmp_reg, rs2=hit_case_reg, imm=8),
            JInstruction.jal(rd=0, imm=method_offset),
        ]

    @staticmethod
    def build_prologue(used_s_regs, local_var_nb, contains_call):
        # An example prologue would be:
        # addi sp sp -16 (+local vars)
        # sd s0 0(sp)
        # sd s1 4(sp)
        # sd s2 8(sp)
        # sd ra 12(sp)
        instructions = []
        stack_space = (used_s_regs + local_var_nb + (1 if contains_call else 0)) * 8
        # Decrement sp by number of s registers + local variable space
        instructions.append(IInstruction.addi(rd=SP, rs1=SP, imm=-stack_space))
        # Store any saved registers used
        for i in range(used_s_regs):
            instructions.append(
                SInstruction.sd(rs1=SP, rs2=CALLEE_SAVED_REG[i], imm=i * 8)
            )
        # Store ra is a function call is made
        if contains_call:
            instructions.append(SInstruction.sd(rs1=SP, rs2=RA, imm=used_s_regs * 8))
        return instructions

    @staticmethod
    def build_epilogue(used_s_regs, local_var_nb, contains_call, *args, **kwargs):
        # An example epilogue would be:
        # ld s0 0(sp)
        # ld s1 4(sp)
        # ld s2 8(sp)
        # ld ra 12(sp)
        # addi sp sp 16 (+local vars)
        # jr ra
        instructions = []
        stack_space = (used_s_regs + local_var_nb + (1 if contains_call else 0)) * 8
        # Reload saved registers used
        for i in range(used_s_regs):
            instructions.append(
                IInstruction.ld(rd=CALLEE_SAVED_REG[i], rs1=SP, imm=i * 8)
            )
        # Reload ra (if necessary)
        if contains_call:
            instructions.append(IInstruction.ld(rd=RA, rs1=SP, imm=used_s_regs * 8))
        # Increment sp to previous value
        instructions.append(IInstruction.addi(rd=SP, rs1=SP, imm=stack_space))
        # Jump back to return address
        instructions.append(IInstruction.ret())
        return instructions

    # Trampoline-related
    # \_________________

    @staticmethod
    def build_pc_relative_reg_save(offset, register):
        # Save a pc-relative value in a given register.
        offset_low, offset_high = InstructionBuilder.split_offset(offset)
        return [
            UInstruction.auipc(register, offset_high),
            IInstruction.addi(register, register, offset_low),
        ]

    @staticmethod
    def build_call_jit_elt_trampoline():
        # The call JIT trampoline is used to call a JIT method/PIC (wow).
        # It does not do much without isolation solution set up (see RIMI builder!).
        # Note that:
        #  - The RA should be set by the caller.
        #  - The callee address is set in a dedicated register.
        return [IInstruction.jr(rs1=CALL_TMP_REG)]

    @staticmethod
    def build_ret_from_jit_elt_trampoline():
        # The ret JIT trampoline is used to return from a JIT method/PIC (wow).
        # It does not do much without isolation solution set up (see RIMI builder!).
        # Note that:
        #  - The RA should be set by the caller.
        return [IInstruction.ret()]
