import unittest
from temp_injector import create_printer

class TestPrinter(unittest.TestCase):

    def test_g28(self):
        p = create_printer()
        p.process_line('G28')

        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.z, 0)

    def test_g0(self):
        p = create_printer()
        p.process_line('G28')
        p.process_line('G92 E0')
        p.process_line('G0 X10.5 Y5 Z1')

        self.assertEqual(p.x, 10.5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 1)
        self.assertEqual(p.e, 0)

        p.process_line('G0 X20 E5')

        self.assertEqual(p.x, 20)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 1)
        self.assertEqual(p.e, 5)

    def test_set_temperature(self):
        p = create_printer()
        
        p.process_line('M104 S100')
        self.assertEqual(p.hotend_temp, 100)
        p.process_line('M109 S200.5')
        self.assertEqual(p.hotend_temp, 200.5)

        p.process_line('M140 S55.5')
        self.assertEqual(p.bed_temp, 55.5)
        p.process_line('M190 S60')
        self.assertEqual(p.bed_temp, 60)

    def test_positioning_mode(self):
        p = create_printer()
        
        #absolute positioning
        p.process_line('G28')
        p.process_line('G92 E0')
        p.process_line('G90')

        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.z, 0)
        self.assertEqual(p.e, 0)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 5)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 5)

        #relative positioning 
        p.process_line('G28')
        p.process_line('G92 E0')
        p.process_line('G91')

        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.z, 0)
        self.assertEqual(p.e, 0)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 5)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 10)
        self.assertEqual(p.z, 10)
        self.assertEqual(p.e, 10)

        #absolute positioning with relative extruder positioning
        p.process_line('G28')
        p.process_line('G92 E0')
        p.process_line('G90')
        p.process_line('M83')

        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.z, 0)
        self.assertEqual(p.e, 0)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 5)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 10)

        #relative positioning with absolute extruder positioning
        p.process_line('G28')
        p.process_line('G92 E0')
        p.process_line('G91')
        p.process_line('M82')

        self.assertEqual(p.x, 0)
        self.assertEqual(p.y, 0)
        self.assertEqual(p.z, 0)
        self.assertEqual(p.e, 0)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 5)
        self.assertEqual(p.y, 5)
        self.assertEqual(p.z, 5)
        self.assertEqual(p.e, 5)

        p.process_line('G0 X5 Y5 Z5 E5')

        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 10)
        self.assertEqual(p.z, 10)
        self.assertEqual(p.e, 5)