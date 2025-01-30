# Pico PIO Theremin

This repository contains the code used in these in *Towards Data Science* articles:

- [**Nine Pico PIO Wats with MicroPython**](https://towardsdatascience.com/nine-pico-pio-wats-with-micropython-part-1-82b80fb84473), [Part 1](https://towardsdatascience.com/nine-pico-pio-wats-with-micropython-part-1-82b80fb84473) & [Part 2](https://towardsdatascience.com/nine-pico-pio-wats-with-micropython-part-2-984a642f25a4)

- [**Nine Pico PIO Wats with Rust**](https://medium.com/towards-data-science/nine-pico-pio-wats-with-rust-part-1-9d062067dc25), [Part 1](https://medium.com/towards-data-science/nine-pico-pio-wats-with-rust-part-1-9d062067dc25) & Part 2 (*forthcoming*)

It uses the PIO features of the Raspberry Pi Pico to generate sound and handle input from an ultrasonic rangefinder. The examples include a backup beeper, a melody player, and a theremin-like instrument.

## Python

To run the various MicroPython examples, edit the `main.py`. See the [article](https://towardsdatascience.com/nine-pico-pio-wats-with-micropython-part-1-82b80fb84473) for some details on getting the code onto the Pico.

## Rust

To run the various Rust examples, use the following commands:

- `cargo run --example backup_demo`
- `cargo run --example sound_demo`
- `cargo run --example distance_demo`
- `cargo run --example distance_debug`
- `cargo run --example theremin`
- `cargo run --example theremin_no_pio --release`

See the [article](https://medium.com/towards-data-science/nine-pico-pio-wats-with-rust-part-1-9d062067dc25) for some details on getting the code onto the Pico.

## License

This project is licensed under either of:

- Apache License, Version 2.0 ([LICENSE-APACHE](LICENSE-APACHE) or <http://www.apache.org/licenses/LICENSE-2.0>)
- MIT license ([LICENSE-MIT](LICENSE-MIT) or <http://opensource.org/licenses/MIT>)

at your option.
