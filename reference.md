# PIO Pin Instruction Reference

## MicroPython

| Example | Description | Pin Base Used | # of Pins |
|------------|-------------|---------------|-----------|
| `in_(pins, 3)` | Reads 3 bits to ISR | `in_base` | given |
| `out(pins, 4)` | Write 4 bits from OSR | `out_base` | given |
| `set(pins, 0b10101)` | Set pin(s) w/ const bit-pattern | `set_base` | `set_init` |
| `jmp(pin, "label")` | Jump if pin is "1" | `jmp_pin` | 1 |
| `wait(1, pin, 2)` | Wait until pin #2 is 1 (or 0) | `in_base` | index |
| `mov(pins, x)` | Moves data to pins | `out_base` | `out_init` |
| `mov(x, pins)` | Moves data from pins | `in_base` | `in_init` |
| `nop().side(1)` | Side-set pins | `sideset_base` | `sideset_init` |

-- All instructions use consecutive pins starting at their respective base pins

## Rust

| Example | Description | Pin Range | Subrange |
|------------|-------------|---------------|-----------|
| `in pins, 3` | Reads 3 bits to ISR | `set_in_pins` | First *n* |
| `out pins, 4` | Write 4 bits from OSR | `set_out_pins` | First *n* |
| `set pins, 0b10101` | Set pin(s) with constant bit-pattern | `set_set_pins` | All |
| `jmp pin label` | Jump if the given pin is "1" | `set_jmp_pin` | Just one pin |
| `wait 1 pin 2` | Wait until pin #2 is 1 (or 0) | `set_in_pins` | index *n* |
| `mov pins, x` | Moves data to pins | `set_out_pins` | All |
| `mov x, pins` | Moves data from pins | `set_in_pins` | All |
| `nop side 1` | Operates on side-set pins | `use_program` | All |

Note: In Rust, PIO instructions are written as strings inside the `pio_asm!` macro or in .pio files.
