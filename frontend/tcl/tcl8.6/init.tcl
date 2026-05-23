package require -exact Tcl 8.6.15

set __bonus_guess_tcl_library [file normalize [file dirname [info script]]]
set tcl_library $__bonus_guess_tcl_library
set auto_path [list $__bonus_guess_tcl_library [file dirname $__bonus_guess_tcl_library]]
source [file join $__bonus_guess_tcl_library auto.tcl]

proc unknown {args} {
    return -code error "invalid command name \"[lindex $args 0]\""
}
