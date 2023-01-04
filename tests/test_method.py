import pytest
from capstone import CS_ARCH_RISCV
from capstone import CS_MODE_RISCV64
from capstone import Cs
from unicorn import Uc
from unicorn.riscv_const import UC_RISCV_REG_RA
from unicorn.unicorn_const import UC_ARCH_RISCV
from unicorn.unicorn_const import UC_MODE_RISCV64

from gigue.constants import CALLER_SAVED_REG
from gigue.instructions import IInstruction
from gigue.method import Method

# =================================
#            Constants
# =================================

ADDRESS = 0x1000
RET_ADDRESS = 0xB000

cap_disasm = Cs(CS_ARCH_RISCV, CS_MODE_RISCV64)
uc_emul = Uc(UC_ARCH_RISCV, UC_MODE_RISCV64)
uc_emul.mem_map(ADDRESS, 2 * 1024 * 1024)
# Fill memory with nops up to BEEC by default
for addr in range(ADDRESS, RET_ADDRESS + 4, 4):
    uc_emul.mem_write(addr, IInstruction.nop().generate_bytes())
uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
# Zero out registers
for reg in CALLER_SAVED_REG:
    uc_emul.reg_write(reg, 0)

# =================================
#             Method
# =================================


def test_initialization():
    method = Method(size=32, address=0x7FFFFF, call_number=15, registers=[])
    assert method.size == 32
    assert method.address == 0x7FFFFF
    assert method.call_number == 15


def test_error_initialization():
    with pytest.raises(ValueError):
        Method(size=28, address=0x7FFFFF, call_number=15, registers=[])


def test_fill_with_nops():
    method = Method(size=32, address=0x7FFFFF, call_number=15, registers=[])
    method.fill_with_nops()
    bytes = method.generate_bytes()
    for i in cap_disasm.disasm(bytes, ADDRESS):
        assert i.mnemonic == "nop"


@pytest.mark.parametrize("execution_number", range(5))
def test_instructions_adding(execution_number):
    method = Method(size=32, address=0x1000, call_number=15, registers=CALLER_SAVED_REG)
    method.add_instructions()
    assert len(method.instructions) == method.size


# TODO
def test_patch_calls():
    method = Method(size=7, address=0x1000, call_number=3, registers=CALLER_SAVED_REG)
    callee1 = Method(size=2, address=0x1100, call_number=0, registers=CALLER_SAVED_REG)
    callee2 = Method(size=2, address=0x1200, call_number=0, registers=CALLER_SAVED_REG)
    callee3 = Method(size=2, address=0x1300, call_number=0, registers=CALLER_SAVED_REG)
    method.add_instructions()
    callee1.add_instructions()
    callee2.add_instructions()
    callee3.add_instructions()
    method.patch_calls([callee1, callee2, callee3])


# TODO
def test_patch_calls_check_recursive_loop_call():
    method = Method(size=7, address=0x1000, call_number=3, registers=CALLER_SAVED_REG)
    callee1 = Method(size=2, address=0x1100, call_number=0, registers=CALLER_SAVED_REG)
    callee2 = Method(size=2, address=0x1200, call_number=0, registers=CALLER_SAVED_REG)
    method.add_instructions()
    callee1.add_instructions()
    callee2.add_instructions()
    with pytest.raises(ValueError):
        method.patch_calls([callee1, callee2, method])


# TODO
def test_patch_calls_check_mutual_loop_call():
    method = Method(size=3, address=0x1000, call_number=1, registers=CALLER_SAVED_REG)
    callee = Method(size=3, address=0x1100, call_number=1, registers=CALLER_SAVED_REG)
    method.add_instructions()
    callee.add_instructions()
    method.patch_calls([callee])
    callee.patch_calls([method])
    assert method.callees == [callee]
    assert callee.callees == []


@pytest.mark.parametrize("execution_number", range(30))
@pytest.mark.parametrize(
    "weights",
    [
        [100, 0, 0, 0, 0],  # Only R Instructions
        [0, 100, 0, 0, 0],  # Only I Instructions
        [0, 0, 100, 0, 0],  # Only U Instructions
        [0, 0, 0, 100, 0],  # Only J Instructions
        [0, 0, 0, 0, 100],  # Only B Instructions
        [35, 40, 10, 5, 10],
    ],
)
def test_instructions_disassembly_execution_smoke(execution_number, weights):
    method = Method(size=10, address=0x1000, call_number=3, registers=CALLER_SAVED_REG)
    method.add_instructions(weights)
    bytes = method.generate_bytes()
    # for i in cap_disasm.disasm(bytes, ADDRESS):
    #     print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    next(cap_disasm.disasm(bytes, ADDRESS))
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    uc_emul.mem_write(ADDRESS, bytes)
    uc_emul.emu_start(ADDRESS, RET_ADDRESS)
    uc_emul.emu_stop()


@pytest.mark.parametrize("execution_number", range(30))
def test_patch_calls_disassembly_execution(execution_number):
    method = Method(size=7, address=ADDRESS, call_number=3, registers=CALLER_SAVED_REG)
    callee1 = Method(size=2, address=0x1100, call_number=0, registers=CALLER_SAVED_REG)
    callee2 = Method(size=2, address=0x1200, call_number=0, registers=CALLER_SAVED_REG)
    callee3 = Method(size=2, address=0x1300, call_number=0, registers=CALLER_SAVED_REG)
    method.add_instructions()
    callee1.add_instructions()
    callee2.add_instructions()
    callee3.add_instructions()
    method.patch_calls([callee1, callee2, callee3])
    bytes_method = method.generate_bytes()
    # for i in cap_disasm.disasm(bytes_method, ADDRESS):
    #     print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    bytes_callee1 = callee1.generate_bytes()
    bytes_callee2 = callee2.generate_bytes()
    bytes_callee3 = callee3.generate_bytes()
    uc_emul = Uc(UC_ARCH_RISCV, UC_MODE_RISCV64)
    uc_emul.mem_map(ADDRESS, 2 * 1024 * 1024)
    # Fill memory with nops up to B000 by default
    for addr in range(ADDRESS, RET_ADDRESS + 4, 4):
        uc_emul.mem_write(addr, IInstruction.nop().generate_bytes())
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    # Zero out registers
    for reg in CALLER_SAVED_REG:
        uc_emul.reg_write(reg, 0)
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    uc_emul.mem_write(ADDRESS, bytes_method)
    uc_emul.mem_write(0x1100, bytes_callee1)
    uc_emul.mem_write(0x1200, bytes_callee2)
    uc_emul.mem_write(0x1300, bytes_callee3)
    # print(ADDRESS + len(bytes_method))
    uc_emul.emu_start(ADDRESS, ADDRESS + len(bytes_method) - 4)
    uc_emul.emu_stop()


if __name__ == "__main__":
    method = Method(size=32, address=0x1000, call_number=3, registers=CALLER_SAVED_REG)
    callee1 = Method(size=2, address=0x1100, call_number=0, registers=CALLER_SAVED_REG)
    callee2 = Method(size=2, address=0x1200, call_number=0, registers=CALLER_SAVED_REG)
    callee3 = Method(size=2, address=0x1300, call_number=0, registers=CALLER_SAVED_REG)
    method.add_instructions(weights=[35, 40, 10, 5, 10])
    method.patch_calls([callee1, callee2, callee3])
    bytes = method.generate_bytes()
    for i in cap_disasm.disasm(bytes, ADDRESS):
        print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    uc_emul = Uc(UC_ARCH_RISCV, UC_MODE_RISCV64)
    uc_emul.mem_map(ADDRESS, 2 * 1024 * 1024)
    # Fill memory with nops up to B000 by default
    for addr in range(ADDRESS, RET_ADDRESS + 4, 4):
        uc_emul.mem_write(addr, IInstruction.nop().generate_bytes())
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    # Zero out registers
    for reg in CALLER_SAVED_REG:
        uc_emul.reg_write(reg, 0)
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    for addr in range(ADDRESS, RET_ADDRESS + 4, 4):
        uc_emul.mem_write(addr, IInstruction.nop().generate_bytes())
    uc_emul.reg_write(UC_RISCV_REG_RA, RET_ADDRESS)
    uc_emul.mem_write(ADDRESS, bytes)
    # for i in cap_disasm.disasm(uc_emul.mem_read(ADDRESS, ADDRESS + 32), ADDRESS): # RET_ADDRESS - ADDRESS + 8
    #     print("0x%x:\t%s\t%s" % (i.address, i.mnemonic, i.op_str))
    uc_emul.emu_start(ADDRESS, RET_ADDRESS)
    uc_emul.emu_stop()
