// cmk
//! This build script requests that `cargo` re-build the crate whenever `memory.x` is changed.
//! `memory.x`is a linker script--a text file telling the final step of the compilation process
//! how modules and program sections (parts of the program) should be located in memory when loaded
//! on hardware.
//! Linker scripts like `memory.x` are not normally a part of the build process and changes to it
//! would ordinarily be ignored by the build process.

use core::error::Error;
use std::{env, fs::File, io::Write, path::PathBuf};

fn main() -> Result<(), Box<dyn Error>> {
    // Put `memory.x` in our output directory and ensure it's on the linker search path.
    let out_dir =
        &PathBuf::from(env::var_os("OUT_DIR").ok_or("OUT_DIR environment variable is not set")?);

    // // Compile the PIO file
    // let program_with_defines = pio_file!("src/toggle.pio");
    // let program = &program_with_defines.program;
    // let binary_path = out_dir.join("toggle_pio.bin");
    // let mut file = File::create(&binary_path).expect("Failed to create binary file");
    // for &instruction in &program.code {
    //     file.write_all(&instruction.to_le_bytes()).expect("Failed to write instruction");
    // }

    File::create(out_dir.join("memory.x"))?.write_all(include_bytes!("memory.x"))?;
    println!("cargo:rustc-link-search={}", out_dir.display());
    // Tell `cargo` to rebuild project if `memory.x` linker script file changes
    println!("cargo:rerun-if-changed=memory.x");
    println!("cargo:rerun-if-changed=src/toggle.pio");
    Ok(())
}
