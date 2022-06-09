from gigue.constants import find_instr_for_opcode


class Disassembler:

    def extract_info(self, instruction, size, shift):
        mask = (1 << size) - 1
        return (instruction & (mask << shift)) >> shift

    def extract_opcode7(self, instruction):
        return self.extract_info(instruction, 7, 0)

    def extract_opcode3(self, instruction):
        return self.extract_info(instruction, 3, 12)

    def extract_imm_i(self, instruction):
        return self.extract_info(instruction, 12, 20)

    def extract_rd(self, instruction):
        return self.extract_info(instruction, 5, 7)

    def extract_rs1(self, instruction):
        return self.extract_info(instruction, 5, 15)

    def extract_rs2(self, instruction):
        return self.extract_info(instruction, 5, 20)

    def disassemble(self, instruction):
        instr_type = self.get_instruction_type(instruction)
        if instr_type == "R":
            return self.disassemble_r_instruction(instruction)
        elif instr_type == "I":
            return self.disassemble_i_instruction(instruction)
        elif instr_type == "J":
            return self.disassemble_r_instruction(instruction)
        elif instr_type == "U":
            return self.disassemble_r_instruction(instruction)
        elif instr_type == "S":
            return self.disassemble_r_instruction(instruction)
        else:
            raise NotImplementedError("Instruction type not recognized.")

    def get_instruction_type(self, instruction):
        return find_instr_for_opcode(instruction & 0x3F)

    def disassemble_r_instruction(self, instruction):
        disa_instr = "Disassembled R instruction:\n"
        disa_instr += "opcode7: {}\n".format(str(bin(self.extract_opcode7(instruction))))
        disa_instr += "opcode3: {}\n".format(str(bin(self.extract_opcode3(instruction))))
        disa_instr += "rd: {}\n".format(str(self.extract_rd(instruction)))
        disa_instr += "rs1: {}\n".format(str(self.extract_rs1(instruction)))
        disa_instr += "rs2: {}".format(str(self.extract_rs2(instruction)))
        return disa_instr

    def disassemble_i_instruction(self, instruction):
        disa_instr = "Disassembled I instruction:\n"
        disa_instr += "opcode7: {}\n".format(str(bin(self.extract_opcode7(instruction))))
        disa_instr += "opcode3: {}\n".format(str(bin(self.extract_opcode3(instruction))))
        disa_instr += "rd: {}\n".format(str(self.extract_rd(instruction)))
        disa_instr += "rs1: {}\n".format(str(self.extract_rs1(instruction)))
        disa_instr += "imm: {}".format(str(self.extract_imm_i(instruction)))
        return disa_instr


if __name__ == "__main__":
    # addi 5, 6, 255
    instr = 0xff30293
    disa = Disassembler()
    print(disa.get_instruction_type(instr))
    print(disa.disassemble(instr))
