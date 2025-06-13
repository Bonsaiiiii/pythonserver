import subprocess
import argparse
import time
import os

parser = argparse.ArgumentParser(description="Convert RTCM to RINEX using convbin.exe")
parser.add_argument('--input', required=True, help='Name of the input RTCM file (without extension)')
parser.add_argument('--output', required=True, help='Name of the output RINEX file (without extension)')
parser.add_argument('--nav', required=True, help='Name of the navigation file (without extension)')
parser.add_argument('--gnav', required=True, help='Name of the GNAV file (without extension)')
parser.add_argument('--qnav', required=True, help='Name of the QNAV file (without extension)')
args = parser.parse_args()

rtklib_path = '/home/zero/RTKLIB/app/consapp/convbin/gcc/convbin'

input_file = '/home/zero/Documents/' + args.input + '.rtcm'

output_file = '/home/zero/Documents/' + args.output + '.25o'

nav_file = '/home/zero/Documents/' + args.nav + '.nav'
gnav_file = '/home/zero/Documents/' + args.gnav + '.25g'
qnav_file = '/home/zero/Documents/' + args.qnav + '.25q'

command = [
    rtklib_path,
    '-v', '2.11',
    '-r', 'rtcm3',
    '-od',
    '-os',
    '-oi',
    '-ot',
    '-ol',
    '-o', output_file,
    '-n', nav_file,
    '-g', gnav_file,
    '-q', qnav_file,
    input_file
]

print("Running command:", ' '.join(command))

process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("Conversion started in the background...")

time.sleep(5)
if process.poll() is None:
    print("Conversion still in progress...")

stdout, stderr = process.communicate()
if process.returncode == 0:
    print("Conversion completed successfully!")
    print(stdout.decode())
else:
    print("Conversion failed.")
    print(stderr.decode())
    
# import subprocess
# import time
#
# # "C:\\Users\\Hugen\\Documents\\RTKLIB_bin-rtklib_2.4.3\\bin\\convbin.exe" ^ -v 3.04 ^ -r rtcm3 ^ -tr "2025/05/23 16:29:10" ^ -od ^ -os ^ -oi ^ -ot ^ -ol ^ -o "C:\\Users\\Hugen\\Documents\\output.20o" ^ -n "C:\\Users\\Hugen\\Documents\\navfile.nav" ^ -g "C:\\Users\\Hugen\\Documents\\gnavfile.25g" ^ -q "C:\\Users\\Hugen\\Documents\\qnavfile.25q" ^ "C:\\Users\\Hugen\\Documents\\output.rtcm"
#
# rtklib_path = 'C:\\Users\\Hugen\\Documents\\RTKLIB_bin-rtklib_2.4.3\\bin\\convbin.exe'  # Adjust path based on where RTKLIB is installed
#
# input_file = 'C:\\Users\\Hugen\\Documents\\FLAMENGOOOO.rtcm'
#
# output_file = 'C:\\Users\\Hugen\\Documents\\output.20o'
#
# nav_file = 'C:\\Users\\Hugen\\Documents\\navfile.nav'
# gnav_file = 'C:\\Users\\Hugen\\Documents\\gnavfile.25g'
# qnav_file = 'C:\\Users\\Hugen\\Documents\\qnavfile.25q'
#
# command = [
#     rtklib_path,  # Path to the executable
#     '-v', '3.04',  # Version flag
#     '-r', 'rtcm3',  # RTCM input
#     '-tr', '2022/3/24 0:0:0',
#     '-os',  # Start processing
#     '-od',
#     '-o', output_file,  # Output file (RIMEX)
#     '-n', nav_file,  # Navigation file
#     '-g', gnav_file,  # GNAV file
#     '-q', qnav_file,  # QNAV file
#     input_file  # Input RTCM file
# ]
#
# process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
#
# print("Conversion started in the background...")
#
# time.sleep(5)
#
# if process.poll() is None:
#     print("Conversion still in progress...")
#
# stdout, stderr = process.communicate()  # To wait for the process to complete and gather output
#
# if process.returncode == 0:
#     print("Conversion completed successfully!")
#     print(stdout.decode())  # Display the standard output from RTKLIB
# else:
#     print("Conversion failed.")
#     print(stderr.decode())  # Display the error output from RTKLIB


