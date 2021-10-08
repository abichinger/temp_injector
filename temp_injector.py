##!/usr/bin/env python

from typing import Any, Callable, List, Dict, Tuple
import argparse
import re

class Parameter():

    def __init__(self, char:str, type:type):
        self.char = char
        self.type = type

class GCodeInstruction():

    def __init__(self, cmd, required_params:Dict[str, Parameter], optional_params:Dict[str, Parameter], func:Callable, ignore_unknown=True):
        self.cmd = cmd
        self.required_params = required_params
        self.optional_params = optional_params
        self.func = func
        self.ignore_unknown = ignore_unknown

    @property
    def params(self):
        params = self.required_params.copy()
        params.update(self.optional_params)
        return params

    @params.setter
    def params(self, value):
        raise RuntimeError('params is read only')

    def parse(self, gcode):
        [cmd, *args] = gcode.split(" ")

        d = {}
        required = set()
        for arg in args:

            if arg[0] not in self.params:
                if self.ignore_unknown:
                    continue
                else:
                    raise RuntimeError(f'{cmd} has no parameter {arg[0]}')

            if arg[0] in self.required_params:
                required.add(p.char)
            
            p = self.params[arg[0]]
            d[p.char] = p.type(arg[1:])

        missing = set(self.required_params.keys()) - required 
        if len(missing) != 0:
            raise RuntimeError(f'required arguments missing for {cmd}: {missing}')

        return d

class VirtualPrinter():

    def __init__(self, x=None, y=None, z=None, e=None, bed_temp=None, hotend_temp=None, ignore_unknown=True):

        self.x = x
        self.y = y
        self.z = z
        self.e = e

        self.bed_temp = bed_temp
        self.hotend_temp = hotend_temp

        self.ignore_unknown = ignore_unknown

        self.instruction_set = {} #type: Dict[str, GCodeInstruction]

    def register_gcode(self, cmd:str, required_params:List[Tuple[str,type]], optional_params:List[Tuple[str,type]], func, ignore_unknown=True):
        required = {p[0]: Parameter(p[0], p[1]) for p in required_params}
        optional = {p[0]: Parameter(p[0], p[1]) for p in optional_params}
        self.instruction_set[cmd] = GCodeInstruction(cmd, required, optional, func, ignore_unknown)

    def process_line(self, gcode:str):
        if gcode.startswith(';'):
            return

        gcode = gcode.split(';')[0].strip()

        [cmd, *_] = gcode.split(" ")
        if cmd not in self.instruction_set:
            if self.ignore_unknown:
                return
            else:
                raise RuntimeError(f'unknown instruction {cmd}')
        
        instr = self.instruction_set[cmd]
        args = instr.parse(gcode)

        instr.func(self, args)

    def print_status(self):
        print(f'X:{self.x}, Y:{self.y}, Z:{self.z}, Bed:{self.bed_temp}°, Hotend:{self.hotend_temp}°')

def g28(printer:VirtualPrinter, args:dict):
    printer.x = 0
    printer.y = 0
    printer.z = 0

def g0(printer:VirtualPrinter, args:dict):
    printer.x = args.get('X', printer.x)
    printer.y = args.get('Y', printer.y)
    printer.z = args.get('Z', printer.z)
    printer.e = args.get('E', printer.e)

def m104(printer:VirtualPrinter, args:dict):
    printer.hotend_temp = args.get('S', printer.hotend_temp)

def m140(printer:VirtualPrinter, args:dict):
    printer.bed_temp = args.get('S', printer.bed_temp)

def create_printer():

    p = VirtualPrinter()

    p.register_gcode('G28', [], [], g28)
    p.register_gcode('G0', [], [('X', float), ('Y', float), ('Z', float), ('E', float)], g0)
    p.register_gcode('G1', [], [('X', float), ('Y', float), ('Z', float), ('E', float)], g0)
    p.register_gcode('M104', [], [('S', float)], m104)
    p.register_gcode('M109', [], [('S', float)], m104)
    p.register_gcode('M140', [], [('S', float)], m140)
    p.register_gcode('M190', [], [('S', float)], m140)

    return p


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='inject temperature steps')
    parser.add_argument('input_file', type=str, help='input file (.gcode)')
    parser.add_argument('output_file', type=str, help='output file (.gcode)')
    parser.add_argument('initial_temp', type=int, help='initial temperature')
    parser.add_argument('temp_step', type=int, help='temperature steps')
    parser.add_argument('section_height', type=float, nargs='?', help='height of one block in mm  (default: 10mm)', default=10)
    parser.add_argument('base_height', type=float, nargs='?', help='height of the base in mm (default: 1.5mm)', default=1.5)

    args = parser.parse_args()

    p = create_printer()
    extruding = False

    with open(args.input_file, 'r') as in_file:
        with open(args.output_file, 'w') as out_file:

            for line in in_file:
                line = line.strip()
                
                if not extruding and (line.startswith('M104') or line.startswith('M109')):
                    m = re.search('S\\d+', line)
                    if m is not None:
                        initial_temp = int(m[0][1:])

                        if initial_temp != args.initial_temp:
                            line = re.sub('S\\d+', f'S{args.initial_temp}', line)
                            print(f'Changed initial temp from {initial_temp}° to {args.initial_temp}°')

                p.process_line(line)
                out_file.write(line + '\n')

                if p.hotend_temp is None or p.hotend_temp < 100 or p.e is None or p.e <= 0:
                    continue
                elif not extruding:
                    extruding = True
                    p.print_status()

                block_index = int((p.z - args.base_height) / args.section_height)
                temp_index = int(abs(p.hotend_temp - args.initial_temp) / abs(args.temp_step))

                if block_index > temp_index:
                    next_temp = args.initial_temp + args.temp_step*block_index
                    temp_gcode = f'M104 S{next_temp}'
                    
                    p.process_line(temp_gcode)
                    out_file.write(temp_gcode + '\n')

                    p.print_status()

            out_file.write('M104 S0\n')

                




    

